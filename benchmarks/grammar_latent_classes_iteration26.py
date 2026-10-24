"""Frozen-transition anonymous word-class induction; target labels evaluated separately."""
from pathlib import Path
import hashlib
import numpy as np
from benchmarks.grammar_class_alignment_iteration25 import ROOT,TREEBANK,RESERVE,load,save,strings
from benchmarks.scalable_latin_caesar import words,PROIEL
from benchmarks.grammar_distributional_skeleton_iteration24_evaluate import metrics
from voynich_smt.class_alignment import tag_class
from voynich_smt.cipher_relations import encrypt
from voynich_smt.latent_cipher_classes import fixed_chain,fit,forward_backward,oracle_emissions,relation_table,relation_edges

OUT=ROOT/'iteration26'
SEEDS=(2601,2602,2603,2604,2605)
GRID=(.01,.03,.05,.1,.2,.35,.5,.7,.9)
ARMS=('word','ending','shuffled_context','shuffled_endings','word_jerome','word_palladius')

def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def observe(sentences,key=26031):
    cipher,_=encrypt(sentences,key);vocab={};endings={};we=[];seq=[]
    for row in cipher:
        ids=[]
        for w in row:
            if w not in vocab:
                vocab[w]=len(vocab);e=w[-2:];endings.setdefault(e,len(endings));we.append(endings[e])
            ids.append(vocab[w])
        seq.append(ids)
    return dict(sequences=seq,word_endings=we)

def prepare():
    if OUT.exists():raise ValueError('Preserve artifacts')
    files=sorted(set(ROOT.rglob('*manifest*.json'))|set(ROOT.rglob('*truth*.json')))
    used=set().union(*(set(strings(load(p))) for p in files));reserved={r['sent_id'] for g in load(RESERVE)['authors'].values() for r in g}
    previous=load(ROOT/'iteration24/datasets.json');oldids={s['sent_id'] for s in previous['background_tune']};oldtruth={};fresh={'Jerome':[],'Caesar':[]}
    labels={'nsubj':1,'obj':2,'iobj':2,'amod':3,'det':3,'conj':4}
    for block in TREEBANK.read_text().split('\n\n'):
        lines=block.splitlines();sid=next((l.split(' = ',1)[1] for l in lines if l.startswith('# sent_id = ')),None)
        source=next((l.split(' = ',1)[1].split(',')[0] for l in lines if l.startswith('# source = ')),None);author=PROIEL.get(source)
        if sid in reserved:continue
        wanted=sid in oldids or (sid not in used and author in fresh and len(fresh[author])<200)
        if not wanted:continue
        rows=[l.split('\t') for l in lines if l and not l.startswith('#')]
        if any('-' in r[0] for r in rows):continue
        kept=[r for r in rows if r[0].isdigit() and r[3]!='PUNCT'];norm=[words(r[1]) for r in kept]
        if not 3<=len(kept)<=60 or any(len(w)!=1 for w in norm):continue
        pos={r[0]:i for i,r in enumerate(kept)};raw={r[0]:r for r in rows};edges=[]
        for r in kept:
            h=r[6];seen=set()
            while h!='0' and h not in pos and h in raw and h not in seen:seen.add(h);h=raw[h][6]
            label=labels.get(r[7].split(':')[0])
            if label and h in pos:edges.append([pos[r[0]],pos[h],label])
        record=dict(sent_id=sid,author=author,tokens=[w[0] for w in norm],upos=[r[3] for r in kept],edges=edges)
        if sid in oldids:oldtruth[sid]=record
        else:fresh[author].append(record)
    assert all(len(v)==200 for v in fresh.values()) and len(oldtruth)==200
    train=[dict(s,classes=[tag_class(t,'fine') for t in s['properties']['upos']]) for s in previous['train']]
    data={'calibration':previous['tune'],'background_calibration':[oldtruth[s['sent_id']] for s in previous['background_tune']]}
    for name,author in [('jerome','Jerome'),('caesar','Caesar')]:data[name]=fresh[author][:100];data['background_'+name]=fresh[author][100:]
    truth={};obs={}
    for name in ('calibration','jerome','caesar'):
        combined=data['background_'+name]+data[name];offset=len(data['background_'+name]);obs[name]=dict(observe(combined),offset=offset,query_ids=[s['sent_id'] for s in data[name]])
        assert observe(combined,26032)==observe(combined)
        truth[name]=[[tag_class(t,'fine') for t in (s.get('upos') or s['properties']['upos'])] for s in combined]
    chains={name:fixed_chain([s['classes'] for s in train if name=='pooled' or s['author'].lower()==name],8) for name in ('pooled','jerome','palladius')}
    OUT.mkdir();save(OUT/'datasets.json',data);save(OUT/'observations.json',obs);save(OUT/'observation-truth.json',truth)
    save(OUT/'source-models.json',dict(chains=chains,relations=relation_table(train,8)))
    paths=[Path(__file__),Path('src/voynich_smt/latent_cipher_classes.py'),TREEBANK,RESERVE,ROOT/'iteration24/datasets.json']
    save(OUT/'manifest.json',dict(inputs={str(p):digest(p) for p in paths},prior_declarations={str(p):digest(p) for p in files},
        split_ids={name:[s['sent_id'] for s in rows] for name,rows in data.items()},seeds=SEEDS,threshold_grid=GRID,max_iter=80,tolerance=1e-7,
        primary='pooled word and ending',arms=ARMS,selection='Maximum regularized objective within each arm, never target labels',
        source='767 labeled source sentences; fixed 8 POS transitions including start/end; only emissions adapted',
        channels='Anonymous repeated word IDs and anonymous last-two-character groups; supplied sentence boundaries; full background+query transductive adaptation',
        ending_prior='Factorized p(ending|state)*p(word|ending,state), alpha_end=1 per state, alpha_word=.2 per ending group',
        controls='Within-sentence shuffled training context; type-permuted ending groups preserve group type counts, not token masses; separate oracle emissions/classes',
        calibration='Previously inspected iteration24 tune40 and background200 reused; relation thresholds maximize old-tune F1 only',
        fresh='100 queries + 100 background per author, disjoint from prior declarations and reserved200; key renaming canonicalization checked'))
    save(OUT/'fit-freeze.json',dict(inputs={str(p):digest(p) for p in OUT.glob('*.json')}))
    print('Prepared fresh100+100 queries and100+100 background; old40 calibration',flush=True)

def arm_input(obs,arm):
    seq=[s[:] for s in obs['sequences']];we=obs['word_endings'][:];rng=np.random.default_rng(2600)
    if arm=='shuffled_context':
        for s in seq:rng.shuffle(s)
    if arm=='shuffled_endings':we=rng.permutation(we).tolist()
    return seq,we

def train_arm(models,obs,arm):
    seq,we=arm_input(obs,arm);template=arm[5:] if arm.startswith('word_') else 'pooled';chain=models['chains'][template]
    fits=[fit(chain,seq,we,seed,sharing=arm in ('ending','shuffled_endings')) for seed in SEEDS]
    selected=max(range(len(fits)),key=lambda i:fits[i]['objective'])
    return dict(fits=fits,selected=selected,template=template)

def decode(models,obs,result):
    return forward_backward(models['chains'][result['template']],result['fits'][result['selected']]['emissions'],obs['sequences'])[1][obs['offset']:]

def edges(gamma,model,threshold):return [relation_edges(g,model,threshold) for g in gamma]

def calibrate(models,obs,data,truth):
    results={};policies={}
    for arm in ARMS:
        print('Calibration',arm,flush=True);results[arm]=train_arm(models,obs,arm)
        gamma=decode(models,obs,results[arm]);scores=[metrics(edges(gamma,models['relations'],t),data)['micro']['f1'] for t in GRID]
        policies[arm]=GRID[int(np.argmax(scores))]
    for arm in ('oracle_emissions','oracle_classes'):
        gamma=oracle_gamma(models,obs,truth,arm)
        scores=[metrics(edges(gamma,models['relations'],t),data)['micro']['f1'] for t in GRID];policies[arm]=GRID[int(np.argmax(scores))]
    return results,policies

def oracle_gamma(models,obs,truth,arm):
    if arm=='oracle_classes':return [np.eye(8)[s] for s in truth[obs['offset']:]]
    emission=oracle_emissions(models['chains']['pooled'],obs['sequences'],obs['word_endings'],truth)
    return forward_backward(models['chains']['pooled'],emission,obs['sequences'])[1][obs['offset']:]

def run():
    if not OUT.exists():prepare()
    if (OUT/'target-fits.json').exists():raise ValueError('Preserve target fits')
    for p,h in load(OUT/'fit-freeze.json')['inputs'].items():assert digest(p)==h,p
    models=load(OUT/'source-models.json');observations=load(OUT/'observations.json');data=load(OUT/'datasets.json');truth=load(OUT/'observation-truth.json')
    results,policies=calibrate(models,observations['calibration'],data['calibration'],truth['calibration'])
    save(OUT/'calibration-fits.json',results);save(OUT/'policies.json',policies)
    save(OUT/'target-freeze.json',dict(inputs={str(p):digest(p) for p in [OUT/'policies.json',OUT/'calibration-fits.json',OUT/'manifest.json',OUT/'source-models.json']}))
    results={}
    for split in ('jerome','caesar'):
        results[split]={}
        for arm in ARMS:
            print('Target',split,arm,flush=True);results[split][arm]=train_arm(models,observations[split],arm)
    save(OUT/'target-fits.json',results)
    print('Unsupervised fits saved; fresh labels not used in fit or selection',flush=True)

if __name__=='__main__':run()
