"""Masked-context role inference: no target surface or gold inference labels."""
import argparse, hashlib, json, random, re
from collections import Counter, defaultdict
from functools import lru_cache
from pathlib import Path
import numpy as np
from voynich_smt.latin_sentence_cases import read_conllu, expected, analyses, canonical
from voynich_smt.relative_search import PassageScorer
from benchmarks.latin_relative_search import grammatical_metrics
from benchmarks.latin_adversarial_objective import OUT as SOURCE, quality
from voynich_smt.data.corpus import write_json
OUT=Path('experiments/results/latin-context-role')
FIELDS=('Case','Number','Gender','Person')
POS={'NOUN':'N','PROPN':'N','ADJ':'ADJ','VERB':'V','AUX':'V'}

def role(t):
    p=POS.get(t['pos'],t['pos']); e=expected(t)
    wanted=('Case','Number','Gender') if p in ('N','ADJ') else ('Number','Person') if p=='V' else ()
    return (p,)+tuple(e.get(k,'_') if k in wanted else '_' for k in FIELDS)

def context(words,i):
    # Target is deliberately absent, including its spelling and morphology.
    fs=['bias', 'position:'+str(min(4,5*i//max(1,len(words))))]
    for d in (-3,-2,-1,1,2,3):
        j=i+d
        if not 0<=j<len(words):fs.append(f'{d}:boundary');continue
        w=words[j];fs.extend((f'{d}:word:{w}',f'{d}:suffix:{w[-2:]}',f'{d}:suffix3:{w[-3:]}'))
    return fs

class Model:
    def __init__(self, sentences):
        labels=sorted({role(t) for s in sentences for t in s['tokens']}); self.labels=labels; idx={l:i for i,l in enumerate(labels)}
        counts=defaultdict(lambda:np.zeros(len(labels))); totals=np.zeros(len(labels)); self.tokens=0
        for s in sentences:
            words=[t['word'] for t in s['tokens']]
            for i,t in enumerate(s['tokens']):
                c=idx[role(t)]; totals[c]+=1; self.tokens+=1
                for f in context(words,i):counts[f][c]+=1
        import torch
        torch.set_num_threads(4); torch.manual_seed(1703)
        self.vocabulary={f:i+1 for i,(f,v) in enumerate(sorted(counts.items())) if v.sum()>=3}
        examples=[]; targets=[]
        for s in sentences:
            words=[t['word'] for t in s['tokens']]
            for i,t in enumerate(s['tokens']):
                ids=[self.vocabulary.get(f,0) for f in context(words,i)]
                examples.append(ids+[0]*(20-len(ids))); targets.append(idx[role(t)])
        x=torch.tensor(examples); y=torch.tensor(targets)
        layer=torch.nn.Embedding(max(self.vocabulary.values())+1,len(labels),padding_idx=0)
        torch.nn.init.zeros_(layer.weight)
        optimizer=torch.optim.Adam(layer.parameters(),lr=.01)
        for epoch in range(15):
            order=torch.randperm(len(y)); losses=[]
            for batch in order.split(256):
                optimizer.zero_grad(); logits=layer(x[batch]).sum(dim=1)
                loss=torch.nn.functional.cross_entropy(logits,y[batch])+1e-5*layer.weight.square().mean()
                loss.backward(); optimizer.step(); losses.append(float(loss.detach()))
            print('TRAIN',epoch+1,float(np.mean(losses)),flush=True)
        self.weights=layer.weight.detach().numpy().copy()
    def predict(self,words):
        a=np.asarray([self.weights[[self.vocabulary.get(f,0) for f in context(words,i)]].sum(axis=0) for i in range(len(words))])
        a-=a.max(axis=1,keepdims=True); a=np.exp(a); return a/a.sum(axis=1,keepdims=True)
    def compatible(self,entries,word):
        readings=analyses(lambda w:entries.get(w,[]),word); good=[]
        for p,*features in self.labels:
            good.append(any(inf['part_of_speech']==p and all(v=='_' or inf['features'].get(k)==v for k,v in zip(FIELDS,features)) for _,inf in readings))
        return np.asarray(good)

def training():
    ss=[]; sources=Counter()
    for path in sorted(Path('data/latin-grammar-benchmark/proiel-r2.17').glob('*train.conllu')):
        # Whole source exclusions, including all Cicero and Palladius.
        blocks=[]
        for b in path.read_text().split('\n\n'):
            source=next((l[11:] for l in b.splitlines() if l.startswith('# source = ')),'')
            if not (source.startswith('Commentarii belli Gallici,')):continue
            blocks.append(b.replace('# source =','# newdoc id =',1)); sources[source.split(',')[0]]+=1
        tmp=OUT/'training-input.conllu';tmp.write_text('\n\n'.join(blocks)+'\n\n')
        for s in read_conllu(tmp):
            ts=[t for t in s['tokens'] if t['pos']!='PUNCT']
            if ts and all(re.fullmatch('[a-z]+',t['word']) for t in ts):ss.append({**s,'tokens':ts})
    if not ss:raise ValueError('No training sources')
    return ss,sources

def run(validate=False):
    OUT.mkdir(parents=True,exist_ok=True); ss,sources=training(); model=Model(ss)
    if validate:
        assert np.array_equal(np.load(OUT/'model-weights.npy'),model.weights)
    else:
        np.save(OUT/'model-weights.npy',model.weights)
        write_json(OUT/'model-vocabulary.json',{'labels':model.labels,'vocabulary':model.vocabulary})
    fixtures=json.loads((SOURCE/'dataset.json').read_text()); entries=json.loads((SOURCE/'morphology.json').read_text())['entries']
    mask={w:model.compatible(entries,w) for f in fixtures for w in set(f['truth'].values())|set(f['pool'])}
    @lru_cache(maxsize=100000)
    def base(words):
        p=model.predict(words); mass=np.asarray([p[i]@mask.get(w,np.zeros(len(model.labels),bool)) for i,w in enumerate(words)])
        # Score all dictionary-analyzable positions, never select them using gold.
        valid=np.asarray([bool(entries.get(w)) for w in words]); return np.array([np.log(np.maximum(mass[valid],1e-12)).sum()/len(words)])
    runs=[]; comparisons=[]; correct=total=0
    for f in fixtures:
        if f['split']!='test':continue
        for s in f['sentences']:
            words=tuple(t['word'] for t in s['tokens']); p=model.predict(words)
            for i,t in enumerate(s['tokens']):
                if t['pos'] not in POS:continue
                total+=1; correct+=model.labels[int(p[i].argmax())]==role(t)
        scores={start:float(sum(len(seg)*base(tuple(m[t] for t in seg))[0] for seg in f['segments'])) for start,m in f['starts'].items()}
        comparisons.append({'fixture':f['id'],'scores':scores})
        for start,initial in f['starts'].items():
            initial_metrics=grammatical_metrics(f['sentences'],initial,f['truth'],entries)
            if start=='control_high' and min(initial_metrics['gold_edge_accuracy'],initial_metrics['role_inflection_accuracy'])<1:continue
            for seed in (1201,1213):
                rng=random.Random(seed); scorer=PassageScorer(f['segments'],initial,base,np.ones(1)); accepted=0; trace=[]; we=wr=0
                def snap(step):
                    m=grammatical_metrics(f['sentences'],scorer.mapping,f['truth'],entries)
                    assert np.isclose(scorer.full_score(),scorer.score)
                    return {'budget':step,'score':scorer.score,'grammar':m,'mapping':dict(scorer.mapping),'worst_high_scoring_edge_loss':we,'worst_high_scoring_role_loss':wr}
                trace.append(snap(0))
                for step in range(1,1001):
                    t=rng.choice(f['active']); changes=None
                    if rng.random()<.25:
                        u=rng.choice(f['active'])
                        if u!=t:changes={t:scorer.mapping[u],u:scorer.mapping[t]}
                    else:
                        w=rng.choice(f['pool'])
                        if w not in scorer.mapping.values():changes={t:w}
                    if changes:
                        proposal=scorer.propose(changes)
                        if proposal and proposal.score>scorer.score+1e-12:
                            scorer.commit(proposal);accepted+=1
                            m=grammatical_metrics(f['sentences'],scorer.mapping,f['truth'],entries)
                            we=max(we,initial_metrics['satisfied_gold_edges']-m['satisfied_gold_edges']);wr=max(wr,initial_metrics['role_inflection_compatible_tokens']-m['role_inflection_compatible_tokens'])
                    if step in (100,1000):trace.append(snap(step))
                runs.append({'fixture':f['id'],'document':f['document'],'start':start,'seed':seed,'accepted':accepted,'snapshots':trace})
        print('ATTACKED',f['id'],flush=True)
    report={'training_tokens':model.tokens,'training_sentences':len(ss),'training_sources':dict(sources),'classes':len(model.labels),'gold_role_top1_accuracy':correct/total,'gold_role_evaluated_tokens':total,'comparisons':comparisons,'runs':runs,'quality':quality(runs),'scope':'Masked target-context multinomial logistic pilot. Train-only PROIEL Caesar; all test authors excluded. Original plaintext used only evaluation, no gold scoring. Existing strongly assisted fixtures, reused test passages, overlapping blocks.'}
    paths=[Path(__file__),SOURCE/'dataset.json',SOURCE/'morphology.json',Path('src/voynich_smt/relative_search.py')]+sorted(Path('data/latin-grammar-benchmark/proiel-r2.17').glob('*train.conllu'))
    manifest={'files':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},'seeds':[1201,1213],'budgets':[100,1000],'training_epochs':15,'training_seed':1703,'learning_rate':.01,'feature_min_count':3,'selection':'single fixed model; no test tuning'}
    if validate:
        assert json.loads((OUT/'manifest.json').read_text())==manifest
        assert json.loads((OUT/'report.json').read_text())==report
        write_json(OUT/'validation.json',{'full_replay':True})
    else:write_json(OUT/'manifest.json',manifest);write_json(OUT/'report.json',report)
    print(json.dumps({k:v for k,v in report.items() if k not in ('runs','comparisons')}),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--validate',action='store_true');run(p.parse_args().validate)
