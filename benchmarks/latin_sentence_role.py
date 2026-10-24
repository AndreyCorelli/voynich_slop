"""Train/freeze a broader sentence-wide expected-role model, then attack it."""
import argparse,hashlib,json,random,re,shutil
from pathlib import Path
from functools import lru_cache
from collections import Counter
import numpy as np
import torch
from torch.nn import functional as F
from voynich_smt.sentence_roles import SentenceRoles,Encoder,reading_features,head_bin
from voynich_smt.latin_sentence_cases import read_conllu,SPLITS
from benchmarks.latin_context_role import role,Model as Compatibility,POS
from benchmarks.latin_adversarial_objective import OUT as SOURCE,quality
from benchmarks.latin_relative_search import grammatical_metrics
from voynich_smt.relative_search import PassageScorer
from voynich_smt.word_mapping.morphology import WhitakerAnnotator
from voynich_smt.data.corpus import write_json,digest
OUT=Path('experiments/results/latin-sentence-role')


def build():
    if (OUT/'dataset.json').exists():raise ValueError('Dataset already frozen')
    OUT.mkdir(parents=True,exist_ok=True);sentences=[];paths=[]
    for path in sorted(Path('data/latin-grammar-benchmark/perseus-r2.17').glob('*.conllu')):
        paths.append(path)
        for s in read_conllu(path):
            key=next((k for k in SPLITS if s['document'].startswith(k)),None)
            if key and SPLITS[key] in ('fit','calibration'):sentences.append({**s,'split':SPLITS[key],'work':s['document']})
    for path in sorted(Path('data/latin-grammar-benchmark/proiel-r2.17').glob('*.conllu')):
        paths.append(path);blocks=[]
        for b in path.read_text().split('\n\n'):
            source=next((l[11:] for l in b.splitlines() if l.startswith('# source = ')),'')
            if source.startswith('Commentarii belli Gallici,') or source.startswith("Jerome's Vulgate,"):
                blocks.append(b.replace('# source =','# newdoc id =',1))
        tmp=OUT/'proiel-input.conllu';tmp.write_text('\n\n'.join(blocks)+'\n\n')
        for s in read_conllu(tmp):sentences.append({**s,'split':'fit','work':s['document'].split(',')[0]})
    unique={};excluded=Counter()
    for s in sentences:
        ts=[t for t in s['tokens'] if t['pos']!='PUNCT']
        if not 3<=len(ts)<=96 or any(not re.fullmatch('[a-z]+',t['word']) for t in ts):excluded[s['split']]+=1;continue
        # Deduplicate across partitions and overlapping source exports.
        key=tuple((t['word'],t['head'],t['relation']) for t in ts)
        unique.setdefault(key,{**s,'tokens':ts})
    sentences=list(unique.values());fixtures=json.loads((SOURCE/'dataset.json').read_text())
    # Explicit plaintext overlap audit, not just source-name exclusions.
    testtexts={tuple(t['word'] for t in s['tokens']) for f in fixtures if f['split']=='test' for s in f['sentences']}
    assert not any(tuple(t['word'] for t in s['tokens']) in testtexts for s in sentences)
    entries=json.loads((SOURCE/'morphology.json').read_text())['entries'];words=sorted({t['word'] for s in sentences for t in s['tokens']}|{w for f in fixtures for w in set(f['pool'])|set(f['truth'].values())})
    missing=[w for w in words if w not in entries];annotator=WhitakerAnnotator(Path('data/vendor/whitakers-words'))
    for i,w in enumerate(missing):
        entries[w]=annotator.annotate(w)
        if i%1000==0:print('ANNOTATED',i,len(missing),flush=True)
    entries={w:entries[w] for w in words};write_json(OUT/'morphology.json',{'entries':entries,'resource':annotator.resource,'annotation_failures':annotator.annotation_failures})
    write_json(OUT/'dataset.json',sentences)
    manifest={'inputs_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths+[SOURCE/'dataset.json',SOURCE/'morphology.json']},'split':'whole-author/source: train Caesar/Jerome/Phaedrus/Petronius/Propertius; calibration Ovid/Vergil/Suetonius; test Cicero/Sallust/Tacitus/Augustus/Palladius. Merge public UD partitions then enforce experiment author split.','max_length':96,'min_length':3,'excluded_sentences':dict(excluded),'deduplication':'word/head/relation sequence; no exact test-sentence overlap','training_seed':2303,'epochs':8,'dimension':64,'batch_size':32,'lr':.002,'auxiliary_weights':{'relation':.2,'head_offset':.2},'temperature_grid':[.5,1,2,4],'checkpoint_selection':'calibration joint-role negative log likelihood only','attack_seeds':[1601,1613],'attack_budgets':[100,1000],'scope':'strongly assisted near-truth fixtures; repeated test authors, original forms in pools, mostly fixed correct mappings; no gold inference inputs'}
    write_json(OUT/'build-manifest.json',manifest)
    print('BUILT',Counter(s['split'] for s in sentences),Counter(s['work'] for s in sentences),flush=True)


def load():
    ss=json.loads((OUT/'dataset.json').read_text());entries=json.loads((OUT/'morphology.json').read_text())['entries'];train=[s for s in ss if s['split']=='fit'];cal=[s for s in ss if s['split']=='calibration']
    labels=sorted({role(t) for s in train for t in s['tokens']});relations=sorted({t['relation'].split(':')[0] for s in train for t in s['tokens']});morph=sorted({f for s in train for t in s['tokens'] for f in reading_features(entries,t['word'])})
    model=SentenceRoles(labels,relations,morph);encoder=Encoder(entries,morph)
    return train,cal,entries,model,encoder


def evaluate(model,encoder,sentences,temperature=1):
    idx={x:i for i,x in enumerate(model.labels)};ri={x:i for i,x in enumerate(model.relations)};loss=n=correct=content=cc=poscorrect=dep=dc=head=hc=0
    model.eval()
    with torch.inference_mode():
        for start in range(0,len(sentences),32):
            batch=sentences[start:start+32];logits,relations,heads=model(*encoder.batch([[t['word'] for t in s['tokens']] for s in batch]))
            for i,s in enumerate(batch):
                logp=F.log_softmax(logits[i,:len(s['tokens'])]/temperature,dim=-1)
                for j,t in enumerate(s['tokens']):
                    r=role(t);n+=1;target=idx.get(r);pred=model.labels[int(logp[j].argmax())]
                    if target is not None:loss-=float(logp[j,target]);correct+=pred==r
                    else:loss+=-np.log(1e-12)
                    if t['pos'] in POS:content+=1;cc+=pred==r;poscorrect+=pred[0]==r[0]
                    rel=t['relation'].split(':')[0]
                    if rel in ri:dep+=1;dc+=int(relations[i,j].argmax())==ri[rel]
                    h=head_bin(s['tokens'],j)
                    if h!=-100:head+=1;hc+=int(heads[i,j].argmax())==h
    return {'tokens':n,'nll':loss/n,'all_role_accuracy':correct/n,'content_tokens':content,'content_role_accuracy':cc/max(1,content),'content_pos_accuracy':poscorrect/max(1,content),'dependency_relation_accuracy':dc/max(1,dep),'head_offset_bin_accuracy':hc/max(1,head)}


def train_model():
    torch.set_num_threads(4);torch.manual_seed(2303);np.random.seed(2303)
    train,cal,entries,model,encoder=load();idx={x:i for i,x in enumerate(model.labels)};ri={x:i for i,x in enumerate(model.relations)};optimizer=torch.optim.AdamW(model.parameters(),lr=.002,weight_decay=.01);history=[];best=float('inf')
    for epoch in range(1,9):
        model.train();order=np.random.permutation(len(train));losses=[]
        for start in range(0,len(order),32):
            batch=[train[i] for i in order[start:start+32]];inputs=encoder.batch([[t['word'] for t in s['tokens']] for s in batch]);n=int(inputs[-1].max());targets=torch.full((len(batch),n),-100,dtype=torch.long);relations=targets.clone();heads=targets.clone()
            for i,s in enumerate(batch):
                for j,t in enumerate(s['tokens']):targets[i,j]=idx[role(t)];relations[i,j]=ri[t['relation'].split(':')[0]];heads[i,j]=head_bin(s['tokens'],j)
            optimizer.zero_grad();a,b,c=model(*inputs)
            loss=F.cross_entropy(a.flatten(0,1),targets.flatten(),label_smoothing=.05)+.2*F.cross_entropy(b.flatten(0,1),relations.flatten())+.2*F.cross_entropy(c.flatten(0,1),heads.flatten())
            loss.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),1);optimizer.step();losses.append(float(loss.detach()))
        metrics=evaluate(model,encoder,cal);history.append({'epoch':epoch,'train_loss':float(np.mean(losses)),'calibration':metrics});print('EPOCH',epoch,history[-1],flush=True)
        if metrics['nll']<best:best=metrics['nll'];torch.save(model.state_dict(),OUT/'model.pt');selected=epoch
    model.load_state_dict(torch.load(OUT/'model.pt',weights_only=True));temperatures=[{'temperature':t,**evaluate(model,encoder,cal,t)} for t in (.5,1,2,4)];chosen=min(temperatures,key=lambda x:x['nll'])
    write_json(OUT/'selection.json',{'history':history,'selected_epoch':selected,'temperatures':temperatures,'temperature':chosen['temperature'],'labels':model.labels,'relations':model.relations,'morphology_features':model.morphology,'scope':'Frozen before test inference and optimizer attacks'})
    paths=[Path(__file__),Path('src/voynich_smt/sentence_roles.py'),Path('benchmarks/latin_context_role.py'),Path('src/voynich_smt/relative_search.py'),Path('benchmarks/latin_relative_search.py'),OUT/'dataset.json',OUT/'morphology.json',OUT/'model.pt',OUT/'selection.json',OUT/'build-manifest.json']
    write_json(OUT/'manifest.json',{'sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}})


def audit_inputs():
    for manifest,key in ((OUT/'build-manifest.json','inputs_sha256'),(OUT/'manifest.json','sha256')):
        for p,h in json.loads(manifest.read_text())[key].items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h,p


def test_model(validate=False):
    audit_inputs();torch.set_num_threads(1);_,cal,entries,model,encoder=load();selection=json.loads((OUT/'selection.json').read_text());model.load_state_dict(torch.load(OUT/'model.pt',weights_only=True));model.eval();temperature=selection['temperature']
    fixtures=[f for f in json.loads((SOURCE/'dataset.json').read_text()) if f['split'] in ('calibration','test')];compatibility=Compatibility.__new__(Compatibility);compatibility.labels=model.labels
    masks={w:compatibility.compatible(entries,w) for f in fixtures for w in set(f['pool'])|set(f['truth'].values())}
    @lru_cache(maxsize=50000)
    def base(words):
        with torch.inference_mode():p=F.softmax(model(*encoder.batch([words]))[0][0]/temperature,dim=-1).numpy()
        mass=np.asarray([p[i]@masks[w] for i,w in enumerate(words)])
        # Unsupported words receive a constant floor, rather than escaping penalties.
        return np.array([np.log(np.maximum(mass,1e-12)).sum()/len(words)])
    comparisons=[];runs=[];unique={}
    for f in fixtures:
        for s in f['sentences']:
            if f['split']=='test':unique[(f['document'],s['id'])]=s
        scores={start:float(sum(len(seg)*base(tuple(m[t] for t in seg))[0] for seg in f['segments'])) for start,m in f['starts'].items()}
        comparisons.append({'fixture':f['id'],'split':f['split'],'scores':scores})
    testmetrics=evaluate(model,encoder,list(unique.values()),temperature)
    calibration_metrics=evaluate(model,encoder,cal,temperature)
    calpairs=[c for c in comparisons if c['split']=='calibration']
    original_rank=sum(c['scores']['truth']>c['scores'][k] for c in calpairs for k in ('corrupt_low','corrupt_high'))/max(1,2*len(calpairs))
    alternative_rank=sum(c['scores']['control_high']>c['scores'][k] for c in calpairs for k in ('corrupt_low','corrupt_high'))/max(1,2*len(calpairs))
    precheck={'calibration_role_accuracy':calibration_metrics['content_role_accuracy'],'calibration_original_pair_accuracy':original_rank,'calibration_alternative_pair_accuracy':alternative_rank,'thresholds':{'role_accuracy':.30,'original_and_alternative_pair_accuracy':.90},'passes':calibration_metrics['content_role_accuracy']>=.30 and min(original_rank,alternative_rank)>=.90,'test_role_metrics':testmetrics,'scope':'Exploratory readiness thresholds declared before seeing this model test results; failing restricts experiment to 1,000-step diagnostic, no long search.'}
    if validate:assert json.loads((OUT/'precheck.json').read_text())==precheck
    else:write_json(OUT/'precheck.json',precheck)
    print('PRECHECK',precheck,flush=True)
    # A bounded fresh attack diagnoses optimization failure even if prechecks fail.
    for f in fixtures:
        if f['split']!='test':continue
        for start,initial in f['starts'].items():
            im=grammatical_metrics(f['sentences'],initial,f['truth'],entries)
            if start=='control_high' and min(im['gold_edge_accuracy'],im['role_inflection_accuracy'])<1:continue
            for seed in (1601,1613):
                scorer=PassageScorer(f['segments'],initial,base,np.ones(1));rng=random.Random(seed);accepted=0;we=wr=0;snapshots=[]
                def snap(step):
                    assert np.isclose(scorer.score,scorer.full_score(),atol=1e-6)
                    return {'budget':step,'score':scorer.score,'mapping':dict(scorer.mapping),'grammar':grammatical_metrics(f['sentences'],scorer.mapping,f['truth'],entries),'worst_high_scoring_edge_loss':we,'worst_high_scoring_role_loss':wr}
                snapshots.append(snap(0))
                for step in range(1,1001):
                    t=rng.choice(f['active']);changes=None
                    if rng.random()<.25:
                        u=rng.choice(f['active'])
                        if u!=t:changes={t:scorer.mapping[u],u:scorer.mapping[t]}
                    else:
                        w=rng.choice(f['pool'])
                        if w not in scorer.mapping.values():changes={t:w}
                    if changes:
                        proposal=scorer.propose(changes)
                        if proposal.score>scorer.score+1e-10:
                            scorer.commit(proposal);accepted+=1;m=grammatical_metrics(f['sentences'],scorer.mapping,f['truth'],entries)
                            we=max(we,im['satisfied_gold_edges']-m['satisfied_gold_edges']);wr=max(wr,im['role_inflection_compatible_tokens']-m['role_inflection_compatible_tokens'])
                    if step in (100,1000):snapshots.append(snap(step))
                runs.append({'fixture':f['id'],'document':f['document'],'start':start,'seed':seed,'accepted':accepted,'snapshots':snapshots})
        print('ATTACKED',f['id'],flush=True)
    report={'test_metrics_unique_sentences':testmetrics,'comparisons':comparisons,'runs':runs,'quality':quality(runs),'calibration':evaluate(model,encoder,cal,temperature),'scope':'Expected role outputs exclude target input. Auxiliary dependency relation and head-offset labels only during training; no inferred full dependency tree. Strong assisted fixtures; prior test authors reused.'}
    if validate:assert json.loads((OUT/'report.json').read_text())==report;write_json(OUT/'validation.json',{'frozen_model_all_searches_replayed':True,'report_sha256':digest(report)})
    else:write_json(OUT/'report.json',report)
    print('RESULT',testmetrics,quality(runs),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['build','train','test','validate']);a=p.parse_args()
    {'build':build,'train':train_model,'test':test_model,'validate':lambda:test_model(True)}[a.stage]()
