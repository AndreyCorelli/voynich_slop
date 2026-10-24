"""Disjoint-book partial fine-tuning and oracle context retrieval curve."""
import argparse
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
import random
import time
import numpy as np
import torch
from benchmarks import word_mapping_repeated_cloze as base
from benchmarks.word_mapping_repeated_cloze_analysis import GLUE
from benchmarks.word_mapping_neural_model import DEFAULT_MODEL, file_hashes
from voynich_smt.data.corpus import digest, write_json
from voynich_smt.neural_scoring import WholeWordScorer
from voynich_smt.neural_cloze import ClozeCandidateBank, RepeatedCloze
from voynich_smt.structural_oracle import StructuralOracle
from voynich_smt.word_mapping.corpora import WordStream

OUT=Path('experiments/results/word-mapping/cloze-finetune-calibration')
FRACTIONS=(0.,.1,.25,.5,1.)

def scaffold(decoding, anchors, target, fraction):
    others=sorted(set(decoding)-set(anchors)-{target})
    random.Random(731).shuffle(others)
    result={c:w for c,w in anchors.items() if c!=target}
    result.update({c:decoding[c] for c in others[:math.floor(fraction*len(others))]})
    assert target not in result
    return result

def training_examples(segments, entries, cloze, count, seed):
    rng=random.Random(seed); locations=defaultdict(list)
    oracle=StructuralOracle(entries,{})
    anchors={w:w for s in segments for w in s if oracle.kind(w)=='fixed'}
    for si,s in enumerate(segments):
        for i,w in enumerate(s):
            if oracle.kind(w)=='content' and w not in GLUE:locations[w].append((si,i))
    targets=sorted(locations); examples=[]
    for _ in range(count):
        target=rng.choice(targets); si,i=rng.choice(locations[target]); s=segments[si]
        fraction=rng.choice(FRACTIONS[:-1])
        visible=scaffold({w:w for w in s},anchors,target,fraction)
        labels=cloze.visible_ids(target)
        ids,positions=cloze.job(s,target,i,visible,len(labels))
        examples.append({'ids':ids,'positions':list(positions),'labels':labels,'target':target,'segment':si,'fraction':fraction})
    return examples

def loss(model, tokenizer, examples):
    width=max(len(e['ids']) for e in examples)
    inputs=torch.full((len(examples),width),tokenizer.pad_token_id,dtype=torch.long)
    attention=torch.zeros_like(inputs); rows=[]; places=[]; labels=[]; weights=[]
    for row,e in enumerate(examples):
        inputs[row,:len(e['ids'])]=torch.tensor(e['ids']); attention[row,:len(e['ids'])]=1
        rows.extend([row]*len(e['labels'])); places.extend(e['positions']); labels.extend(e['labels'])
        weights.extend([1/len(e['labels'])/len(examples)]*len(e['labels']))
    hidden=model.roberta(input_ids=inputs,attention_mask=attention).last_hidden_state
    logits=model.lm_head(hidden[rows,places])
    values=torch.nn.functional.cross_entropy(logits,torch.tensor(labels),reduction='none')
    return (values*torch.tensor(weights)).sum()

def train(steps):
    OUT.mkdir(parents=True,exist_ok=True)
    if (OUT/'training.json').exists():raise ValueError('Training already exists; use --evaluate')
    public,anchors,targets,entries,forms,freq=base.prepare()
    asset=json.loads((DEFAULT_MODEL/'manifest.json').read_text())
    assert digest(asset['protocol'])==asset['sha256']
    assert file_hashes(DEFAULT_MODEL)==asset['protocol']['files_sha256']
    torch.manual_seed(731); torch.set_num_threads(4)
    scorer=WholeWordScorer.load(DEFAULT_MODEL/'inference',batch_size=16,threads=4)
    cloze=RepeatedCloze(scorer,ClozeCandidateBank(scorer.tokenizer,forms))
    segments=list(WordStream.load(base.anchor.PARENT/'splits/train.json').segments())
    valid_indices=[i for i,s in enumerate(segments) if int(digest(s)[:8],16)%10==0]
    if not valid_indices:raise ValueError('Empty training validation split')
    train_indices=[i for i in range(len(segments)) if i not in valid_indices]
    training=training_examples([segments[i] for i in train_indices],entries,cloze,steps*8,731)
    validation=training_examples([segments[i] for i in valid_indices],entries,cloze,128,732)
    protocol={'seed':731,'steps':steps,'batch_size':8,'learning_rate':2e-5,'warmup_steps':20,
        'train_segments':train_indices,'validation_segments':valid_indices,'train_tokens':sum(len(segments[i]) for i in train_indices),
        'validation_tokens':sum(len(segments[i]) for i in valid_indices),'source_sha256':digest(segments),
        'training_examples_sha256':digest(training),'validation_examples_sha256':digest(validation),
        'base_model_sha256':asset['sha256'],'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'curve_fractions':FRACTIONS,'evaluation_targets':targets,'glue_exclusions':sorted(GLUE),
        'training':'uniform lexical target types; all target occurrences masked; upper two encoder layers and LM head dense/layernorm trainable; tied embeddings and decoder bias frozen; normal training dropout',
        'selection':'lowest held-out training-book mean per-example piece cross entropy including unchanged step zero; no development metric selection'}
    write_json(OUT/'manifest.json',{'protocol':protocol,'sha256':digest(protocol)})
    write_json(OUT/'examples.json',{'training':training,'validation':validation})
    model=scorer.model
    for p in model.parameters():p.requires_grad_(False)
    for layer in model.roberta.encoder.layer[-2:]:
        for p in layer.parameters():p.requires_grad_(True)
    for module in (model.lm_head.dense,model.lm_head.layer_norm):
        for p in module.parameters():p.requires_grad_(True)
    parameters=[p for p in model.parameters() if p.requires_grad]
    optimizer=torch.optim.AdamW(parameters,lr=2e-5)
    history=[]; best=float('inf'); selected=0; start=time.monotonic()
    def assess(step):
        nonlocal best,selected
        model.eval()
        with torch.no_grad():v=float(np.mean([loss(model,scorer.tokenizer,validation[i:i+8]).item() for i in range(0,len(validation),8)]))
        history.append({'step':step,'validation_loss':v,'elapsed_seconds':time.monotonic()-start})
        if v<best:
            best=v; selected=step
            model.save_pretrained(OUT/'model',safe_serialization=True); scorer.tokenizer.save_pretrained(OUT/'model')
        print('validation',step,v,'selected',selected,flush=True)
    assess(0)
    training_losses=[]
    for step in range(1,steps+1):
        model.train(); optimizer.zero_grad(set_to_none=True)
        value=loss(model,scorer.tokenizer,training[(step-1)*8:step*8]); value.backward()
        torch.nn.utils.clip_grad_norm_(parameters,1.)
        lr=2e-5*min(step/20,1)*max(0.,(steps-step)/(max(1,steps-20)))
        for group in optimizer.param_groups:group['lr']=lr
        optimizer.step(); training_losses.append(float(value.detach()))
        if step%10==0:print('train',step,'loss',np.mean(training_losses[-10:]),flush=True)
        if step%50==0 or step==steps:assess(step)
    result={'selected_step':selected,'validation_history':history,'training_losses':training_losses,
        'trainable_parameters':sum(p.numel() for p in parameters),'total_parameters':sum(p.numel() for p in model.parameters()),
        'model_files_sha256':file_hashes(OUT/'model'),'elapsed_seconds':time.monotonic()-start}
    write_json(OUT/'training.json',result)

def evaluate(replay=False):
    public,anchors,targets,entries,forms,frequencies=base.prepare()
    truth=json.loads((base.anchor.PARENT/'truth/fit-2000.json').read_text())
    manifest=json.loads((OUT/'manifest.json').read_text()); training=json.loads((OUT/'training.json').read_text())
    assert digest(manifest['protocol'])==manifest['sha256']
    assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest()==manifest['protocol']['code_sha256']
    assert file_hashes(OUT/'model')==training['model_files_sha256']
    frequency=np.asarray([math.log(frequencies[w]+.1) for w in forms])
    collected=[]
    for label,path in [('base',DEFAULT_MODEL/'inference'),('tuned',OUT/'model')]:
        scorer=WholeWordScorer.load(path,batch_size=16,threads=4)
        bank=ClozeCandidateBank(scorer.tokenizer,forms); cloze=RepeatedCloze(scorer,bank)
        for number,target in enumerate(targets,1):
            output=OUT/'cases'/f'{label}-{target}.json'; score_path=OUT/'scores'/f'{label}-{target}.npz'
            if output.exists() and not replay:
                collected.extend(json.loads(output.read_text())); continue
            rows=[]; saved_scores={}
            for fraction in FRACTIONS:
                visible=scaffold(truth['decoding'],anchors,target,fraction)
                scores=cloze.rank_scores(public['segments'],target,visible)['pooled']
                eligible=[i for i,w in enumerate(forms) if i not in bank.excluded and w not in set(visible.values())]
                case=base.evaluate_case({'cipher':target,'fraction':fraction,'model':label,'visible_types':len(visible)},
                    {'neural':scores,'frequency':frequency},forms,eligible,entries,truth)
                rows.append(case); saved_scores[str(fraction)]=scores
            if replay:
                with np.load(score_path) as old:
                    for key,value in saved_scores.items():assert np.allclose(old[key],value,atol=1e-6,rtol=0)
                assert json.loads(output.read_text())==rows
            else:
                score_path.parent.mkdir(parents=True,exist_ok=True); np.savez_compressed(score_path,**saved_scores)
                write_json(output,rows)
            collected.extend(rows); print('curve',label,number,'/',len(targets),flush=True)
        del cloze,bank,scorer
    summary=[]
    for label in ('base','tuned'):
        for fraction in FRACTIONS:
            for population in ('known_content','lexical_content'):
                rows=[r for r in collected if r['model']==label and r['fraction']==fraction and r['gold_kind']=='content' and (population=='known_content' or r['gold'] not in GLUE)]
                for metric in ('neural','frequency'):
                    vals=[r['rankings'][metric]['content_candidates'] for r in rows]
                    summary.append({'model':label,'fraction':fraction,'population':population,'metric':metric,'types':len(vals),
                        **{k:sum(v[k] for v in vals) for k in ('compatible_top1','compatible_top10','exact_top1','exact_top10')}})
    report={'manifest_sha256':manifest['sha256'],'selected_step':training['selected_step'],'summary':summary,'case_sha256':digest(collected),
        'scope':'same previously explored development targets; correct oracle scaffolds; target excluded before selecting visible types; no final test; morphological compatibility does not establish sentence meaning'}
    if replay:
        assert json.loads((OUT/'report.json').read_text())==report
        write_json(OUT/'validation.json',{'full_neural_replay':True,'tolerance':1e-6,'report_sha256':digest(report)})
    else:write_json(OUT/'report.json',report)
    for row in summary:
        if row['population']=='lexical_content':print(row,flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--steps',type=int,default=200); parser.add_argument('--evaluate',action='store_true'); parser.add_argument('--validate',action='store_true')
    args=parser.parse_args()
    if not args.evaluate and not args.validate:train(args.steps)
    evaluate(args.validate)
