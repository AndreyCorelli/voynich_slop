"""Regenerate inputs/rankings, sample neural replay, and audit public forwards."""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import numpy as np
import torch
from safetensors.torch import load_file
from benchmarks import word_mapping_repeat_identity as b
from benchmarks import word_mapping_repeat_identity_enriched as enriched
from voynich_smt.data.corpus import digest,write_json

def run(ordinary=False):
    out=b.OUT if ordinary else enriched.OUT
    generator=b.examples_for if ordinary else enriched.examples_for
    manifest=json.loads((out/'manifest.json').read_text());protocol=manifest['protocol']
    assert digest(protocol)==manifest['sha256']
    for path,value in protocol['code_sha256'].items():assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==value
    if not ordinary:assert hashlib.sha256(Path(enriched.__file__).read_bytes()).hexdigest()==json.loads((out/'sampling-manifest.json').read_text())['code_sha256']
    segments=list(b.old.WordStream.load(b.old.base.anchor.PARENT/'splits/train.json').segments());assert digest(segments)==protocol['source_sha256']
    assert set(protocol['train_segments']).isdisjoint(protocol['validation_segments'])
    public,anchors,targets,entries,forms,_=b.old.base.prepare()
    truth=json.loads((b.old.base.anchor.PARENT/'truth/fit-2000.json').read_text())
    examples={};changes={};stats={};sample_checks=[];rows=[];full_errors=[]
    for arm in ('repeat','collapsed'):
        examples[arm]=json.loads((out/arm/'examples.json').read_text())
        training=json.loads((out/arm/'training.json').read_text())
        assert b.old.file_hashes(out/arm/'model')==training['model_sha256']
        assert hashlib.sha256((out/arm/'adapter.safetensors').read_bytes()).hexdigest()==training['adapter_sha256']
        scorer,adapter,cloze=b.setup(arm,path=out/arm/'model');adapter.load_state_dict(load_file(str(out/arm/'adapter.safetensors')))
        for split in ('training','validation'):
            split_segments=[segments[i] for i in protocol['train_segments' if split=='training' else 'validation_segments']]
            assert digest(examples[arm][split])==training['examples_sha256'][split]
            regenerated=generator(split_segments,entries,cloze,len(examples[arm][split]),941 if split=='training' else 942)
            assert regenerated==examples[arm][split]
            for e in regenerated:
                assert e['labels']==cloze.visible_ids(e['target'])
                assert all(e['ids'][p]==scorer.tokenizer.mask_token_id for p in e['positions'])
        if arm=='repeat':
            for split in ('training','validation'):
                repeated_target=0;repeated_other=0
                for e in examples[arm][split]:
                    counts=Counter(e['identity']);target=counts[e['identity'][e['positions'][0]]]
                    repeated_target+=target>len(e['labels'])
                    targetslot=e['identity'][e['positions'][0]]
                    repeated_other+=any(n>1 for i,n in counts.items() if i not in (0,targetslot))
                stats[split]={'examples':len(examples[arm][split]),'repeated_target':repeated_target,'other_repeated_type':repeated_other}
        original=load_file(str(b.old.DEFAULT_MODEL/'inference/model.safetensors'));tuned=load_file(str(out/arm/'model/model.safetensors'))
        changed=[name for name in tuned if not torch.equal(tuned[name],original[name])]
        assert all(n.startswith(('roberta.encoder.layer.10.','roberta.encoder.layer.11.','lm_head.dense.','lm_head.layer_norm.')) for n in changed)
        changes[arm]=changed;del original,tuned,scorer,adapter,cloze
    for split in ('training','validation'):
        strip=lambda rows:[{k:v for k,v in row.items() if k!='identity'} for row in rows]
        assert strip(examples['repeat'][split])==strip(examples['collapsed'][split])
    for label,arm,mode,fractions in [('repeat','repeat','repeat',b.FRACTIONS),('collapsed','collapsed','collapsed',b.FRACTIONS),('broken_repeat','repeat','broken',(0.,.5))]:
        scorer,adapter,cloze=b.setup(mode,path=out/arm/'model');adapter.load_state_dict(load_file(str(out/arm/'adapter.safetensors')));adapter.eval()
        for target in targets:
            saved=json.loads((out/'cases'/f'{label}-{target}.json').read_text());regenerated=[]
            with np.load(out/'scores'/f'{label}-{target}.npz') as scores:
                for fraction in fractions:
                    visible=b.old.scaffold(truth['decoding'],anchors,target,fraction);reserved=set(visible.values());excluded=set(cloze.bank.excluded)
                    eligible=[i for i,w in enumerate(forms) if i not in excluded and w not in reserved]
                    values=scores[str(fraction)]
                    regenerated.append(b.old.base.evaluate_case({'cipher':target,'model':label,'fraction':fraction},{'neural':values},forms,eligible,entries,truth))
                    if target==targets[-1]:
                        replay=cloze.rank_scores(public['segments'],target,visible)['pooled'];assert np.allclose(replay,values,atol=1e-6,rtol=0)
                        sample_checks.append({'model':label,'fraction':fraction,'cipher':target})
                        if label=='repeat':
                            occurrences=[(s,i) for s in public['segments'] for i,c in enumerate(s) if c==target]
                            for length,(indices,pieces) in cloze.bank.groups.items():
                                index=int(indices[0]);full=[]
                                for s,i in occurrences:
                                    ids,positions,identity=cloze.job(s,target,i,visible,length)
                                    inputs=torch.tensor([ids]);identities=torch.tensor([identity])
                                    with torch.inference_mode():
                                        embeddings=scorer.model.roberta.embeddings.word_embeddings(inputs)+adapter(identities)
                                        logits=scorer.model(inputs_embeds=embeddings,attention_mask=torch.ones_like(inputs)).logits[0]
                                        probs=torch.log_softmax(logits,dim=-1)
                                        full.append(float(probs[list(positions),torch.tensor(pieces[0])].mean()))
                                error=abs(math.fsum(full)/len(full)-values[index]);assert error<1e-4;full_errors.append(error)
            assert saved==regenerated;rows.extend(regenerated)
        del scorer,adapter,cloze
    assert digest(rows)==json.loads((out/'report.json').read_text())['cases_sha256']
    write_json(out/'independent-validation.json',{'manifest_sha256':manifest['sha256'],'all_examples_regenerated':True,'matched_training_inputs':True,
        'all_case_rankings_regenerated':True,'neural_replay_cases':sample_checks,'public_forward_scores':len(full_errors),'max_public_forward_error':max(full_errors),
        'repetition_statistics':stats,'changed_parameters':changes,'validation_code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})
    print('Validated',len(rows),'case rankings,',len(sample_checks),'neural replays and',len(full_errors),'public-forward scores',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--ordinary',action='store_true');run(p.parse_args().ordinary)
