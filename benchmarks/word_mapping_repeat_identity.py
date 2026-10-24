"""Matched repeat-identity training versus collapsed masking, with ablation."""
import argparse
import hashlib
import json
from pathlib import Path
import time
import numpy as np
import torch
from safetensors.torch import save_file,load_file
from benchmarks import word_mapping_cloze_finetune as old
from voynich_smt.data.corpus import digest,write_json
from voynich_smt.neural_scoring import WholeWordScorer
from voynich_smt.neural_cloze import ClozeCandidateBank
from voynich_smt.repeat_identity import IdentityCloze,adapter_for,pack

OUT=Path('experiments/results/word-mapping/repeat-identity-calibration')
FRACTIONS=(0.,.25,.5)

def setup(mode,seed=941,path=None):
    torch.manual_seed(seed);torch.set_num_threads(4)
    scorer=WholeWordScorer.load(path or old.DEFAULT_MODEL/'inference',batch_size=16,threads=4)
    adapter=adapter_for(scorer.model)
    _,_,_,_,forms,_=old.base.prepare()
    return scorer,adapter,IdentityCloze(scorer,ClozeCandidateBank(scorer.tokenizer,forms),adapter,mode=mode,seed=seed)

def objective(model,adapter,tok,examples):
    jobs=[(e['ids'],e['positions'],e['identity']) for e in examples]
    inputs,attention,identity,rows,places=pack(jobs,tok.pad_token_id)
    embeddings=model.roberta.embeddings.word_embeddings(inputs)+adapter(identity)
    hidden=model.roberta(inputs_embeds=embeddings,attention_mask=attention).last_hidden_state
    values=torch.nn.functional.cross_entropy(model.lm_head(hidden[rows,places]),torch.tensor([v for e in examples for v in e['labels']]),reduction='none')
    weights=torch.tensor([1/len(e['labels'])/len(examples) for e in examples for _ in e['labels']])
    return (values*weights).sum()

def examples_for(segments,entries,cloze,count,seed):
    # Reuse exactly the target/context sampling, then attach randomized IDs.
    original=old.training_examples(segments,entries,cloze_for_plain(cloze),count,seed)
    from voynich_smt.structural_oracle import StructuralOracle
    oracle=StructuralOracle(entries,{})
    anchors={w:w for s in segments for w in s if oracle.kind(w)=='fixed'}
    examples=[]
    for index,e in enumerate(original):
        s=segments[e['segment']];target=e['target']
        visible=old.scaffold({w:w for w in s},anchors,target,e['fraction'])
        # Locate the exact center by matching the frozen ordinary input job.
        centers=[i for i,w in enumerate(s) if w==target and cloze_for_plain(cloze).job(s,target,i,visible,len(e['labels']))==(e['ids'],tuple(e['positions']))]
        center=centers[0]
        cloze.seed=seed+index*7919
        ids,positions,identity=cloze.job(s,target,center,visible,len(e['labels']))
        examples.append({**e,'ids':ids,'positions':list(positions),'identity':identity})
    return examples

def cloze_for_plain(cloze):
    from voynich_smt.neural_cloze import RepeatedCloze
    return RepeatedCloze(cloze.scorer,cloze.bank)

def train(steps):
    if (OUT/'manifest.json').exists():raise ValueError('Existing experiment; use --evaluate or --validate')
    parent=json.loads((old.OUT/'manifest.json').read_text())['protocol']
    segments=list(old.WordStream.load(old.base.anchor.PARENT/'splits/train.json').segments())
    assert digest(segments)==parent['source_sha256']
    _,_,targets,entries,_,_=old.base.prepare()
    protocol={'steps':steps,'batch_size':8,'seed':941,'learning_rate':2e-5,'fractions':FRACTIONS,'slots':32,
        'source_sha256':digest(segments),'train_segments':parent['train_segments'],'validation_segments':parent['validation_segments'],
        'targets':targets,'base_model_sha256':json.loads((old.DEFAULT_MODEL/'manifest.json').read_text())['sha256'],
        'selection':'minimum training-book validation loss including step zero; no retrieval selection',
        'code_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(__file__),Path('src/voynich_smt/repeat_identity.py'),Path(old.__file__))},
        'scope':'random per-example anonymous hidden-type IDs; same word mask inputs and target/context samples in both arms; upper two layers and head plus identity adapter; no final test'}
    write_json(OUT/'manifest.json',{'protocol':protocol,'sha256':digest(protocol)})
    for mode in ('repeat','collapsed'):
        scorer,adapter,cloze=setup(mode)
        training=examples_for([segments[i] for i in parent['train_segments']],entries,cloze,steps*8,941)
        validation=examples_for([segments[i] for i in parent['validation_segments']],entries,cloze,128,942)
        write_json(OUT/mode/'examples.json',{'training':training,'validation':validation})
        model=scorer.model
        for p in model.parameters():p.requires_grad_(False)
        for layer in model.roberta.encoder.layer[-2:]:
            for p in layer.parameters():p.requires_grad_(True)
        for module in (model.lm_head.dense,model.lm_head.layer_norm):
            for p in module.parameters():p.requires_grad_(True)
        params=[p for p in model.parameters() if p.requires_grad]+list(adapter.parameters())
        optimizer=torch.optim.AdamW(params,lr=2e-5);history=[];best=float('inf');selected=0;start=time.monotonic();losses=[]
        def assess(step):
            nonlocal best,selected
            model.eval();adapter.eval()
            with torch.no_grad():value=float(np.mean([objective(model,adapter,scorer.tokenizer,validation[i:i+8]).item() for i in range(0,len(validation),8)]))
            history.append({'step':step,'validation_loss':value})
            if value<best:
                best=value;selected=step;model.save_pretrained(OUT/mode/'model',safe_serialization=True);scorer.tokenizer.save_pretrained(OUT/mode/'model')
                save_file({'weight':adapter.weight.detach().contiguous()},str(OUT/mode/'adapter.safetensors'))
            print(mode,'validation',step,value,flush=True)
        assess(0)
        torch.manual_seed(943)
        for step in range(1,steps+1):
            model.train();optimizer.zero_grad(set_to_none=True)
            value=objective(model,adapter,scorer.tokenizer,training[(step-1)*8:step*8]);value.backward()
            torch.nn.utils.clip_grad_norm_(params,1.)
            for group in optimizer.param_groups:group['lr']=2e-5*min(step/20,1)*max(0,(steps-step)/max(1,steps-20))
            optimizer.step();losses.append(float(value.detach()))
            if step%100==0 or step==steps:assess(step)
        write_json(OUT/mode/'training.json',{'selected_step':selected,'history':history,'losses':losses,'seconds':time.monotonic()-start,
            'model_sha256':old.file_hashes(OUT/mode/'model'),'adapter_sha256':hashlib.sha256((OUT/mode/'adapter.safetensors').read_bytes()).hexdigest(),
            'examples_sha256':{'training':digest(training),'validation':digest(validation)}})
        del cloze,scorer,model,adapter,optimizer,params

def evaluate(replay=False):
    public,anchors,targets,entries,forms,freq=old.base.prepare()
    truth=json.loads((old.base.anchor.PARENT/'truth/fit-2000.json').read_text())
    manifest=json.loads((OUT/'manifest.json').read_text());assert digest(manifest['protocol'])==manifest['sha256']
    for path,h in manifest['protocol']['code_sha256'].items():assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==h
    rows=[]
    for label,arm,mode,fractions in [('repeat','repeat','repeat',FRACTIONS),('collapsed','collapsed','collapsed',FRACTIONS),('broken_repeat','repeat','broken',(0.,.5))]:
        training=json.loads((OUT/arm/'training.json').read_text());assert old.file_hashes(OUT/arm/'model')==training['model_sha256']
        assert hashlib.sha256((OUT/arm/'adapter.safetensors').read_bytes()).hexdigest()==training['adapter_sha256']
        scorer,adapter,cloze=setup(mode,path=OUT/arm/'model');adapter.load_state_dict(load_file(str(OUT/arm/'adapter.safetensors')));adapter.eval()
        for number,target in enumerate(targets,1):
            path=OUT/'cases'/f'{label}-{target}.json'; scorepath=OUT/'scores'/f'{label}-{target}.npz'
            if path.exists() and not replay:rows.extend(json.loads(path.read_text()));continue
            cases=[];scores={}
            for fraction in fractions:
                visible=old.scaffold(truth['decoding'],anchors,target,fraction)
                result=cloze.rank_scores(public['segments'],target,visible)['pooled']
                reserved=set(visible.values());excluded=set(cloze.bank.excluded)
                eligible=[i for i,w in enumerate(forms) if i not in excluded and w not in reserved]
                case=old.base.evaluate_case({'cipher':target,'model':label,'fraction':fraction},{'neural':result},forms,eligible,entries,truth)
                cases.append(case);scores[str(fraction)]=result
            if replay:
                assert json.loads(path.read_text())==cases
                with np.load(scorepath) as saved:
                    for key,value in scores.items():assert np.allclose(saved[key],value,atol=1e-6,rtol=0)
            else:
                write_json(path,cases);scorepath.parent.mkdir(parents=True,exist_ok=True);np.savez_compressed(scorepath,**scores)
            rows.extend(cases);print('retrieval',label,number,'/',len(targets),flush=True)
        del scorer,adapter,cloze
    summary=[]
    for label in ('repeat','collapsed','broken_repeat'):
        for fraction in FRACTIONS:
            for population in ('known_content','lexical_content'):
                selected=[r for r in rows if r['model']==label and r['fraction']==fraction and r['gold_kind']=='content' and (population=='known_content' or r['gold'] not in old.GLUE)]
                if not selected:continue
                values=[r['rankings']['neural']['content_candidates'] for r in selected]
                summary.append({'model':label,'fraction':fraction,'population':population,'types':len(values),**{k:sum(v[k] for v in values) for k in ('compatible_top1','compatible_top10','exact_top1','exact_top10')}})
    report={'manifest_sha256':manifest['sha256'],'summary':summary,'cases_sha256':digest(rows),'scope':'explored development retrieval; oracle context; morphological compatibility; no full decoding or final test'}
    if replay:
        assert json.loads((OUT/'report.json').read_text())==report;write_json(OUT/'validation.json',{'neural_replay':True,'tolerance':1e-6,'report_sha256':digest(report)})
    else:write_json(OUT/'report.json',report)
    print(json.dumps(summary,indent=2),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--steps',type=int,default=400);p.add_argument('--evaluate',action='store_true');p.add_argument('--validate',action='store_true');args=p.parse_args()
    if not args.evaluate and not args.validate:train(args.steps)
    evaluate(args.validate)
