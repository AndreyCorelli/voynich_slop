"""Independent provenance, masking and public-forward audit for fine-tuned cloze."""
import hashlib
import json
import math
from pathlib import Path
import numpy as np
import torch
from benchmarks import word_mapping_cloze_finetune as b
from voynich_smt.data.corpus import digest,write_json
from voynich_smt.neural_cloze import ClozeCandidateBank,RepeatedCloze
from voynich_smt.neural_scoring import WholeWordScorer
from voynich_smt.word_mapping.corpora import WordStream

def run():
    manifest=json.loads((b.OUT/'manifest.json').read_text()); protocol=manifest['protocol']
    examples=json.loads((b.OUT/'examples.json').read_text())
    segments=list(WordStream.load(b.base.anchor.PARENT/'splits/train.json').segments())
    assert digest(segments)==protocol['source_sha256']
    assert set(protocol['train_segments']).isdisjoint(protocol['validation_segments'])
    assert set(protocol['train_segments'])|set(protocol['validation_segments'])==set(range(len(segments)))
    public,anchors,targets,entries,forms,_=b.base.prepare()
    truth=json.loads((b.base.anchor.PARENT/'truth/fit-2000.json').read_text())
    scorer=WholeWordScorer.load(b.OUT/'model',batch_size=16,threads=4)
    bank=ClozeCandidateBank(scorer.tokenizer,forms);cloze=RepeatedCloze(scorer,bank)
    for split in ('training','validation'):
        assert digest(examples[split])==protocol[f'{split}_examples_sha256']
        split_indices=protocol['train_segments' if split=='training' else 'validation_segments']
        split_segments=[segments[i] for i in split_indices]
        regenerated=b.training_examples(split_segments,entries,cloze,len(examples[split]),731 if split=='training' else 732)
        assert regenerated==examples[split]
        for example in examples[split]:
            s=split_segments[example['segment']]; target=example['target']
            assert target in s
            assert example['labels']==cloze.visible_ids(target)
            assert all(example['ids'][p]==scorer.tokenizer.mask_token_id for p in example['positions'])
    from safetensors.torch import load_file
    original=load_file(str(b.DEFAULT_MODEL/'inference/model.safetensors'))
    tuned=load_file(str(b.OUT/'model/model.safetensors'))
    allowed=('roberta.encoder.layer.10.','roberta.encoder.layer.11.','lm_head.dense.','lm_head.layer_norm.')
    changes=[name for name in tuned if not torch.equal(tuned[name],original[name])]
    assert changes and all(name.startswith(allowed) for name in changes)
    del original,tuned
    checks=[]; target=targets[-1]
    occurrences=[(s,i) for s in public['segments'] for i,c in enumerate(s) if c==target]
    for fraction in b.FRACTIONS:
        visible=b.scaffold(truth['decoding'],anchors,target,fraction)
        assert target not in visible
        with np.load(b.OUT/'scores'/f'tuned-{target}.npz') as saved:reference=saved[str(fraction)]
        for length,(indices,pieces) in bank.groups.items():
            index=int(indices[0]); values=[]
            for s,i in occurrences:
                ids,positions=cloze.job(s,target,i,visible,length)
                inputs=torch.tensor([ids])
                with torch.inference_mode():
                    logits=scorer.model(input_ids=inputs,attention_mask=torch.ones_like(inputs)).logits[0]
                    probs=torch.log_softmax(logits,dim=-1)
                    values.append(float(probs[list(positions),torch.tensor(pieces[0])].mean()))
            error=abs(math.fsum(values)/len(values)-reference[index]);assert error<1e-4
            checks.append({'fraction':fraction,'pieces':length,'absolute_error':error})
    paths=[Path(b.__file__),Path(__file__),Path(b.base.__file__),Path(b.base.anchor.__file__),
        Path('src/voynich_smt/neural_cloze.py'),Path('src/voynich_smt/neural_scoring.py'),Path('src/voynich_smt/structural_oracle.py'),
        b.base.anchor.PARENT/'splits/train.json',b.base.anchor.PARENT/'public/fit-2000.json',b.base.anchor.PARENT/'truth/fit-2000.json',
        b.base.anchor.INVENTORY/'forms-100000.jsonl']
    write_json(b.OUT/'independent-validation.json',{'manifest_sha256':manifest['sha256'],'split_and_example_checks':True,'exact_training_example_replay':True,'changed_parameters':changes,
        'public_forward_checks':checks,'maximum_absolute_error':max(c['absolute_error'] for c in checks),
        'files_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}})
    print('Independent masking/split checks and',len(checks),'public-forward scores passed')
if __name__=='__main__':run()
