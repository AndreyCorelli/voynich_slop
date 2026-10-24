"""Frozen, all-content-position lexical compatibility diagnostic; no search."""
from pathlib import Path
from collections import Counter,defaultdict
import json,hashlib,math
import numpy as np
from voynich_smt.grammar_lexical_bridge import pos_model,candidate_pos
ROOT=Path('experiments/results/grammar-restoration');OUT=ROOT/'iteration70'
def load(p):return json.loads(Path(p).read_text())
def save(p,x):Path(p).write_text(json.dumps(x,indent=2)+'\n')
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
POS={'N':'NOUN','V':'VERB','VPAR':'VERB','SUPINE':'VERB','ADJ':'ADJ','PRON':'PRON','ADV':'ADV','PREP':'ADP','CONJ':'CCONJ','NUM':'NUM','INTERJ':'INTJ'}
CASE={'NOM':'Nom','ACC':'Acc','GEN':'Gen','DAT':'Dat','ABL':'Abl','VOC':'Voc','LOC':'Loc'}
CONTENT={'NOUN','PROPN','VERB','AUX','ADJ','ADV'}
def coarse(p):return {'PROPN':'NOUN','AUX':'VERB'}.get(p,p)
def profile(t):return (coarse(t['pos']),t['features'].get('Case',''),t['features'].get('Number',''))
def readings(rows):
    return sorted(set((POS.get(r['pos'],r['pos']),CASE.get(dict(r['features']).get('Case'),''),{'S':'Sing','P':'Plur'}.get(dict(r['features']).get('Number'),'')) for r in rows))
def compatible(g,r):return g[0]==r[0] and all(not a or not b or a==b for a,b in zip(g[1:],r[1:]))
def context(pos,i):return [f'{d}:{pos[i+d] if 0<=i+d<len(pos) else "BOUNDARY"}' for d in (-2,-1,1,2)]
def fit(sentences,pm,lex):
    counts=Counter();features=defaultdict(Counter);freq=Counter()
    for s in sentences:
        tokens=s['tokens'];pp=[candidate_pos(t['word'],pm,lex.get(t['word'],[]))[0] for t in tokens]
        for i,t in enumerate(tokens):
            freq[t['word']]+=1
            if t['pos'] not in CONTENT:continue
            key=(t['rel'].split(':')[0],profile(t));counts[key]+=1;features[key].update(context(pp,i))
    labels=sorted(counts);vocab=sorted({f for c in features.values() for f in c});prior=np.array([counts[k] for k in labels],float);prior/=prior.sum()
    likelihood=np.array([[(features[k][f]+1)/(4*counts[k]+len(vocab)) for f in vocab] for k in labels])
    return dict(labels=labels,prior=prior.tolist(),vocab=vocab,likelihood=likelihood.tolist(),frequency=dict(freq))
def posterior(model,features):
    log=np.log(model['prior']);v={x:i for i,x in enumerate(model['vocab'])};ll=np.asarray(model['likelihood'])
    for f in features:
        if f in v:log=log+np.log(ll[:,v[f]])
    p=np.exp(log-log.max());return p/p.sum()
def mass(model,p,rs):return float(sum(q for (_,g),q in zip(model['labels'],p) if any(compatible(g,r) for r in rs)))
def target_sentences(records):
    wanted={r['sent_id']:r for r in records};result=[]
    # Only tokenize annotations inside previously declared target sentence blocks.
    for block in Path('data/latin-grammar-benchmark/proiel-r2.17/la_proiel-ud-train.conllu').read_text().split('\n\n'):
        sid=next((l.split(' = ',1)[1] for l in block.splitlines() if l.startswith('# sent_id = ')),None)
        if sid not in wanted:continue
        rows=[l.split('\t') for l in block.splitlines() if l and not l.startswith('#')];rows=[r for r in rows if r[0].isdigit() and r[3]!='PUNCT'];words=wanted[sid]['tokens'];assert len(rows)==len(words)
        result.append(dict(sent_id=sid,tokens=[dict(word=w,pos=r[3],rel=r[7],features=dict(x.split('=',1) for x in r[5].split('|') if '=' in x)) for w,r in zip(words,rows)]))
    assert len(result)==100
    return result

def run():
    assert not OUT.exists();OUT.mkdir()
    paths=[Path(__file__),ROOT/'iteration44/annotations-truth.json',ROOT/'iteration49/manifest.json',ROOT/'iteration23/datasets.json',ROOT/'iteration23/morphology-lattice.json',ROOT/'iteration1/morphology-lattice.json',Path('data/latin-grammar-benchmark/proiel-r2.17/la_proiel-ud-train.conllu'),Path('experiments/holdouts/grammar-construction-next.json')]
    (OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='Reuse exactly100declared iteration23Caesar sentences; source49fold0fit only. Every content token gets mostsourcefrequent different cached dictionary word sharing coarse POS; no targetgrammar used to choose distractor. Original always offered, even unknown. Perfect surrounding plaintext and sentence boundaries supplied. Mask center word/POS; predict joint dependency-role/POS/Case/Number distribution with fixed add-one naive Bayes using candidate-derived neighborPOS +/-2. Sum posterior over labels compatible with any joint candidate reading (never recombine analyses). Compare role+profile prior, permuted context, sourcefrequency. Explicit gold-role conditional and gold-morphology oracle arms are isolated; neither enters inferred score. Unknown dictionary reading gets zero compatibility, no exclusions. No hyperparameter selection. Gate learned strictwin>=65%, >=prior+10pp and >=shuffle+5pp; ties fail. If fails no dictionarysearch; ifpasses additional historicalfirstcorruption gate required. Reserveunscored; no new annotations queried.'))
    data=load(ROOT/'iteration44/annotations-truth.json');ids=load(ROOT/'iteration49/manifest.json')['partitions']['0']['fit'];source=[data[i] for i in ids];assert all(s['author']!='Caesar' for s in source)
    lex=load(ROOT/'iteration23/morphology-lattice.json');lex.update(load(ROOT/'iteration1/morphology-lattice.json'));pm=pos_model(s['tokens'] for s in source);model=fit(source,pm,lex);save(OUT/'model.json',model);save(OUT/'model-freeze.json',dict(model=digest(OUT/'model.json'),source_pos=digest(ROOT/'iteration44/annotations-truth.json')))
    pool=defaultdict(list)
    for w,rr in lex.items():
        for p in {r[0] for r in readings(rr)}:pool[p].append(w)
    for p in pool:pool[p].sort(key=lambda w:(-model['frequency'].get(w,0),w))
    targets=target_sentences(load(ROOT/'iteration23/datasets.json')['test_caesar']);cases=[];rng=np.random.default_rng(7001)
    for s in targets:
        tt=s['tokens'];pp=[candidate_pos(t['word'],pm,lex.get(t['word'],[]))[0] for t in tt];shuffled=list(rng.permutation(pp))
        for i,t in enumerate(tt):
            if t['pos'] not in CONTENT:continue
            other=next(w for w in pool[coarse(t['pos'])] if w!=t['word']);r0=readings(lex.get(t['word'],[]));r1=readings(lex[other]);post=posterior(model,context(pp,i));spost=posterior(model,context(shuffled,i));role=t['rel'].split(':')[0];rp=np.array([q if label[0]==role else 0 for label,q in zip(model['labels'],model['prior'])]);rp=rp/rp.sum() if rp.sum() else np.array(model['prior']);g=profile(t)
            scores={name:[mass(model,p,r) for r in (r0,r1)] for name,p in [('context',post),('shuffle',spost),('prior',model['prior']),('oracle_role',rp)]};scores['oracle_morph']=[int(any(compatible(g,r) for r in rr)) for rr in (r0,r1)];scores['frequency']=[model['frequency'].get(w,0) for w in (t['word'],other)]
            cases.append(dict(sid=s['sent_id'],index=i,word=t['word'],other=other,role=role,gold_profile=g,readings=[r0,r1],context=context(pp,i),shuffled_context=context(shuffled,i),scores=scores))
    save(OUT/'predictions.json',cases);save(OUT/'prediction-freeze.json',dict(predictions=digest(OUT/'predictions.json')))
    result=evaluate(cases);save(OUT/'evaluation.json',result);print(json.dumps(result,indent=2))
def evaluate(cases):
    result={}
    for name in cases[0]['scores']:
        delta=[r['scores'][name][0]-r['scores'][name][1] for r in cases];result[name]=dict(win=sum(d>1e-10 for d in delta),loss=sum(d< -1e-10 for d in delta),tie=sum(abs(d)<=1e-10 for d in delta));result[name]['strict_accuracy']=result[name]['win']/len(cases)
    c=result['context']['strict_accuracy'];passed=c>=.65 and c>=result['prior']['strict_accuracy']+.10 and c>=result['shuffle']['strict_accuracy']+.05
    return dict(n=len(cases),sentences=len({r['sid'] for r in cases}),unknown_originals=sum(not r['readings'][0] for r in cases),arms=result,gate_passed=passed,role_groups={role:dict(n=len(rr),context_wins=sum(r['scores']['context'][0]>r['scores']['context'][1]+1e-10 for r in rr)) for role in sorted({r['role'] for r in cases}) for rr in [[r for r in cases if r['role']==role]]},scope='Reused pairwise diagnostic, not lexical recovery; perfect surrounding words and sentence boundaries; frequent same-coarsePOS distractor; oracle roles/morphology privileged.')
if __name__=='__main__':run()
