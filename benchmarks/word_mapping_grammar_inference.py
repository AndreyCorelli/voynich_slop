"""Weakly supervised grammar inference without unknown-word spellings."""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import random
import numpy as np
import torch
from torch import nn
from safetensors.torch import save_file,load_file
from benchmarks import word_mapping_grammar_oracle as oracle_b
from voynich_smt.data.corpus import digest,write_json
from voynich_smt.structural_oracle import StructuralOracle

OUT=Path('experiments/results/word-mapping/grammar-inference-calibration')
RADIUS=8

class ContextGrammar(nn.Module):
    def __init__(self,width,classes):
        super().__init__();self.embedding=nn.Embedding(width*17,64);self.head=nn.Linear(64,classes)
    def forward(self,inputs):return self.head(torch.relu(self.embedding(inputs).sum(1)/math.sqrt(17)))

def context_ids(segment,target,center,visible,vocabulary):
    lookup={w:i+4 for i,w in enumerate(vocabulary)};width=len(vocabulary)+4;result=[]
    if target in visible or segment[center]!=target:raise ValueError('Target must be hidden')
    for slot,offset in enumerate(range(-RADIUS,RADIUS+1)):
        i=center+offset
        if not 0<=i<len(segment):value=0
        elif segment[i]==target:value=2
        elif segment[i] in visible:value=lookup.get(visible[segment[i]],3)
        else:value=1
        result.append(slot*width+value)
    return result

def examples(segments,oracle,vocabulary,classes):
    lookup={signature:i for i,signature in enumerate(classes)}
    visible={w:w for s in segments for w in s if oracle.kind(w)=='fixed'}
    rows=[]
    for si,s in enumerate(segments):
        for center,target in enumerate(s):
            if oracle.kind(target)!='content' or target in oracle_b.parent.GLUE:continue
            labels=sorted(lookup[v] for v in oracle.profiles[target])
            rows.append({'inputs':context_ids(s,target,center,visible,vocabulary),'labels':labels,'target':target,'segment':si,'center':center})
    return rows

def tensors(rows,classes):
    inputs=torch.tensor([r['inputs'] for r in rows],dtype=torch.long)
    allowed=torch.zeros((len(rows),classes),dtype=torch.bool)
    for i,row in enumerate(rows):allowed[i,row['labels']]=True
    return inputs,allowed

def ambiguity_loss(logits,allowed):
    logp=torch.log_softmax(logits,dim=-1)
    return -torch.logsumexp(logp.masked_fill(~allowed,-torch.inf),dim=-1)

def prepare():
    public,anchors,targets,entries,forms,frequencies=oracle_b.parent.base.prepare()
    oracle=StructuralOracle(entries,{})
    segments=list(oracle_b.parent.WordStream.load(oracle_b.parent.base.anchor.PARENT/'splits/train.json').segments())
    parent=json.loads((oracle_b.parent.OUT/'manifest.json').read_text())['protocol']
    assert digest(segments)==parent['source_sha256']
    vocabulary=sorted({w for i in parent['train_segments'] for w in segments[i] if oracle.kind(w)=='fixed'})
    classes=sorted({s for w in forms if oracle.kind(w)=='content' for s in oracle.profiles[w]},key=repr)
    # Dictionary grammar states are public; no gold word is added to the inventory.
    training=examples([segments[i] for i in parent['train_segments']],oracle,vocabulary,classes)
    validation=examples([segments[i] for i in parent['validation_segments']],oracle,vocabulary,classes)
    return public,anchors,targets,oracle,forms,frequencies,vocabulary,classes,training,validation

def run(steps=1000,validate=False):
    torch.set_num_threads(4);torch.manual_seed(1051)
    public,anchors,targets,oracle,forms,frequencies,vocabulary,classes,training,validation=prepare()
    protocol={'seed':1051,'steps':steps,'batch':64,'radius':RADIUS,'vocabulary':vocabulary,'classes':classes,
        'training_sha256':digest(training),'validation_sha256':digest(validation),'public_sha256':digest(public),
        'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'selection':'lowest held-out training-segment ambiguous-label loss; no development tuning',
        'labels':'complete dictionary analysis sets, not disambiguated token syntax; loss allows any valid analysis',
        'input':'function-anchor spellings at offsets; unknown words collapsed; repeated target distinguished; no unknown spelling, word length or target lemma',
        'weights':[1,3],'primary':'exact lexical identity; grammar compatibility is not syntactic accuracy'}
    manifest={'protocol':protocol,'sha256':digest(protocol)}
    model=ContextGrammar(len(vocabulary)+4,len(classes))
    x,y=tensors(training,len(classes));vx,vy=tensors(validation,len(classes))
    counts=Counter(row['target'] for row in training);vcounts=Counter(row['target'] for row in validation)
    sampling=torch.tensor([1/counts[row['target']] for row in training],dtype=torch.double)
    validation_weights=torch.tensor([1/vcounts[row['target']] for row in validation]);validation_weights/=validation_weights.sum()
    priors=np.ones(len(classes),dtype=np.float64)*.1
    for row in training:
        for label in row['labels']:priors[label]+=1/len(row['labels'])
    priors/=priors.sum()
    if validate:
        assert json.loads((OUT/'manifest.json').read_text())==json.loads(json.dumps(manifest))
        selection=json.loads((OUT/'training.json').read_text());model.load_state_dict(load_file(str(OUT/'model.safetensors')))
    else:
        if (OUT/'manifest.json').exists():raise ValueError('Existing experiment')
        write_json(OUT/'manifest.json',manifest);write_json(OUT/'examples.json',{'training':training,'validation':validation})
        optimizer=torch.optim.AdamW(model.parameters(),lr=.002,weight_decay=.01);best=float('inf');history=[];selected=0
        def assess(step):
            nonlocal best,selected
            model.eval()
            with torch.no_grad():
                logits=model(vx);loss=float((ambiguity_loss(logits,vy)*validation_weights).sum())
                accuracy=float((vy[torch.arange(len(vy)),logits.argmax(1)].float()*validation_weights).sum())
            history.append({'step':step,'validation_loss':loss,'valid_analysis_top1':accuracy})
            if loss<best:
                best=loss;selected=step;save_file(model.state_dict(),str(OUT/'model.safetensors'))
            print('grammar training',step,loss,accuracy,flush=True)
        assess(0)
        for step in range(1,steps+1):
            model.train();indices=torch.multinomial(sampling,64,replacement=True)
            optimizer.zero_grad(set_to_none=True);loss=ambiguity_loss(model(x[indices]),y[indices]).mean();loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(),1.);optimizer.step()
            if step%100==0 or step==steps:assess(step)
        selection={'selected_step':selected,'history':history,'train_examples':len(training),'validation_examples':len(validation),
            'classes':len(classes),'function_vocabulary':len(vocabulary),'model_sha256':hashlib.sha256((OUT/'model.safetensors').read_bytes()).hexdigest()}
        write_json(OUT/'training.json',selection);model.load_state_dict(load_file(str(OUT/'model.safetensors')))
    assert hashlib.sha256((OUT/'model.safetensors').read_bytes()).hexdigest()==selection['model_sha256']
    model.eval();lookup={signature:i for i,signature in enumerate(classes)}
    candidate_labels=[sorted(lookup[s] for s in oracle.profiles.get(w,()) if s in lookup) for w in forms]
    reserved=set(anchors.values());eligible=[i for i,w in enumerate(forms) if w not in reserved and oracle.kind(w)=='content']
    truth=json.loads((oracle_b.parent.base.anchor.PARENT/'truth/fit-2000.json').read_text())
    score_hashes={};rows=[]
    for target in targets:
        gold=truth['decoding'][target];profile=oracle.profiles.get(gold,frozenset())
        occurrences=[(s,i) for s in public['segments'] for i,c in enumerate(s) if c==target]
        inputs=torch.tensor([context_ids(s,target,i,anchors,vocabulary) for s,i in occurrences])
        with torch.no_grad():probabilities=torch.softmax(model(inputs),dim=-1).numpy().astype(np.float64)
        mean=probabilities.mean(0);predicted=int(mean.argmax());prior_top=int(priors.argmax())
        learned=np.zeros(len(forms));prior_score=np.zeros(len(forms))
        for index,labels in enumerate(candidate_labels):
            if not labels:learned[index]=prior_score[index]=math.log(1e-12);continue
            learned[index]=np.log(np.maximum(probabilities[:,labels].sum(1),1e-12)).mean()
            prior_score[index]=math.log(max(float(priors[labels].sum()),1e-12))
        path=oracle_b.parent.OUT/'scores'/f'base-{target}.npz';score_hashes[str(path)]=hashlib.sha256(path.read_bytes()).hexdigest()
        with np.load(path) as saved:neural=saved['0.0'].copy()
        frequency=np.asarray([np.log(frequencies[w]+.1) for w in forms])
        compatible={w for w in forms if w==gold or (profile and oracle.profiles.get(w)==profile)}
        rankings={}
        for label,values in [('neural',neural),('frequency',frequency)]:
            rankings[label]=oracle_b.parent.base.ranking(values,forms,eligible,gold,compatible)
            for weight in (1,3):
                for role,grammar in [('inferred',learned),('grammar_prior',prior_score)]:
                    rankings[f'{label}/{role}/{weight}']=oracle_b.parent.base.ranking(values+weight*grammar,forms,eligible,gold,compatible)
            for role,tag in [('inferred',predicted),('grammar_prior',prior_top)]:
                narrowed=[i for i in eligible if tag in candidate_labels[i]]
                rankings[f'{label}/{role}/hard']=oracle_b.parent.base.ranking(values,forms,narrowed,gold,compatible)
        rows.append({'cipher':target,'gold':gold,'gold_kind':oracle.kind(gold),'lexical':oracle.kind(gold)=='content' and gold not in oracle_b.parent.GLUE,
            'valid_inferred_analysis':classes[predicted] in profile,'valid_prior_analysis':classes[prior_top] in profile,
            'inferred_analysis':classes[predicted],'rankings':rankings})
    summary=[]
    for population in ('known_content','lexical_content'):
        selected=[r for r in rows if r['gold_kind']=='content' and (population=='known_content' or r['lexical'])]
        for label in rows[0]['rankings']:
            summary.append({'population':population,'metric':label,'types':len(selected),
                **{key:sum(r['rankings'][label][key] for r in selected) for key in ('exact_top1','exact_top10','compatible_top1','compatible_top10')}})
    selected=[r for r in rows if r['lexical']]
    report={'manifest_sha256':manifest['sha256'],'selection':selection,'summary':summary,'case_sha256':digest(rows),'neural_score_files_sha256':score_hashes,
        'lexical_grammar_analysis_top1':sum(r['valid_inferred_analysis'] for r in selected),'lexical_prior_analysis_top1':sum(r['valid_prior_analysis'] for r in selected),
        'scope':'weak dictionary labels, oracle function anchors, reused development, no true token parse or global grammar search; final test unscored'}
    if validate:
        assert json.loads((OUT/'cases.json').read_text())==json.loads(json.dumps(rows));assert json.loads((OUT/'report.json').read_text())==json.loads(json.dumps(report))
        write_json(OUT/'validation.json',{'all_context_predictions_and_rankings_replayed':True,'report_sha256':digest(report)})
    else:write_json(OUT/'cases.json',rows);write_json(OUT/'report.json',report)
    for row in summary:
        if row['population']=='lexical_content':print(row,flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--steps',type=int,default=1000);p.add_argument('--validate',action='store_true');a=p.parse_args();run(a.steps,a.validate)
