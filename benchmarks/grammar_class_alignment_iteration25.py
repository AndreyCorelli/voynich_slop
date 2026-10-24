"""Freeze source templates, then align anonymous target classes exactly."""
from collections import Counter
from pathlib import Path
import hashlib
import numpy as np
from benchmarks.grammar_distributional_skeleton_iteration24 import OUT as PREVIOUS,TREEBANK,ROOT,load,save,strings
from benchmarks.grammar_relative_constituents_iteration15 import RESERVE
from benchmarks.scalable_latin_caesar import words,PROIEL
from voynich_smt.class_alignment import tag_class,fit_source,encode,align,shuffle_context

OUT=ROOT/'iteration25'
NOISE=(0.,.10,.25,.50)
KEY=25031
REKEY=25032


def proxy_groups(sentences):
    counts=Counter(w for s in sentences for w in s['tokens']);first={}
    for s in sentences:
        for w in s['tokens']:first.setdefault(w,len(first))
    rank={w:i for i,w in enumerate(sorted(counts,key=lambda w:(-counts[w],first[w])))}
    return [[min(7,rank[w]) for w in s['tokens']] for s in sentences]


def build_observations(data,key):
    records=[];truth=[]
    for split in ('test_jerome','test_caesar'):
        combined=data['background_'+split.split('_')[1]]+data[split];offset=len(combined)-len(data[split])
        for family,k in (('coarse',3),('fine',8),('frequency_proxy',3)):
            gold=[[tag_class(t,'coarse' if family=='frequency_proxy' else family) for t in s['upos']] for s in combined]
            raw=proxy_groups(combined) if family=='frequency_proxy' else gold
            observed=8 if family=='frequency_proxy' else k
            for noise in ((0.,) if family=='frequency_proxy' else NOISE):
                encoded,inverse=encode(raw,observed,key,noise=noise,noise_seed=2501)
                for condition in ('ordered','shuffled_context') if noise==0 else ('ordered',):
                    identifier=f'{split}/{family}/{noise}/{condition}'
                    records.append(dict(id=identifier,split=split,family=family,noise=noise,condition=condition,observed=observed,k=k,bijective=family!='frequency_proxy',
                        sequences=shuffle_context(encoded) if condition=='shuffled_context' else encoded,
                        query_sequences=encoded[offset:],query_ids=[s['sent_id'] for s in data[split]]))
                    truth.append(dict(id=identifier,labels=gold[offset:],inverse_key=inverse))
    return records,truth


def prepare():
    if OUT.exists():raise ValueError('Preserve prior artifacts')
    files=sorted(set(ROOT.rglob('*manifest*.json'))|set(ROOT.rglob('*truth*.json')))
    used=set().union(*(set(strings(load(p))) for p in files));reserved={r['sent_id'] for group in load(RESERVE)['authors'].values() for r in group}
    fresh={'Jerome':[],'Caesar':[]}
    for block in TREEBANK.read_text().split('\n\n'):
        lines=block.splitlines();sid=next((l.split(' = ',1)[1] for l in lines if l.startswith('# sent_id = ')),None)
        source=next((l.split(' = ',1)[1].split(',')[0] for l in lines if l.startswith('# source = ')),None);author=PROIEL.get(source)
        if sid in reserved or sid in used or author not in fresh or len(fresh[author])>=300:continue
        rows=[l.split('\t') for l in lines if l and not l.startswith('#')]
        if any('-' in r[0] for r in rows):continue
        kept=[r for r in rows if r[0].isdigit() and r[3]!='PUNCT'];norm=[words(r[1]) for r in kept]
        if not 3<=len(kept)<=60 or any(len(w)!=1 for w in norm):continue
        fresh[author].append(dict(sent_id=sid,author=author,tokens=[w[0] for w in norm],upos=[r[3] for r in kept]))
    assert all(len(v)==300 for v in fresh.values())
    train=[dict(sent_id=s['sent_id'],author=s['author'],tokens=s['tokens'],upos=s['properties']['upos']) for s in load(PREVIOUS/'datasets.json')['train']]
    data=dict(train=train,test_jerome=fresh['Jerome'][:100],test_caesar=fresh['Caesar'][:100],background_jerome=fresh['Jerome'][100:],background_caesar=fresh['Caesar'][100:])
    models={}
    for template,selection in [('pooled',train),('jerome',[s for s in train if s['author']=='Jerome']),('palladius',[s for s in train if s['author']=='Palladius'])]:
        models[template]={family:fit_source([[tag_class(t,family) for t in s['upos']] for s in selection],k) for family,k in [('coarse',3),('fine',8)]}
    observations,truth=build_observations(data,KEY);rekey,rekeytruth=build_observations(data,REKEY)
    OUT.mkdir();save(OUT/'datasets.json',data);save(OUT/'models.json',models);save(OUT/'observations.json',observations);save(OUT/'observation-truth.json',truth)
    save(OUT/'rekey-observations.json',rekey);save(OUT/'rekey-truth.json',rekeytruth)
    paths=[Path(__file__),Path('src/voynich_smt/class_alignment.py'),TREEBANK,RESERVE,PREVIOUS/'datasets.json']
    save(OUT/'manifest.json',dict(inputs={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        prior_declarations={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},split_ids={name:[s['sent_id'] for s in ss] for name,ss in data.items()},
        channels='Main channel reveals oracle token POS classes under an unknown permutation. It is an alignment upper-bound, not class induction from ciphertext.',
        inventories={'coarse':3,'fine':8,'frequency_proxy':'8 groups (7 most frequent word types plus all other types), mapped many-to-one to 3 coarse classes'},
        source_templates=['pooled','jerome','palladius'],primary='pooled',noise=NOISE,noise_kind='Independent per-token replacement by a different class before renaming; same noisy tokens under rekeys.',
        objective='All bijections enumerated (6/40320); proxy all 3^8 maps. Frequency/Markov/joint fixed a priori; proxy aggregate JS fit plus a Markov collapse control.',
        smoothing=.5,key=KEY,rekey=REKEY,random_maps=100,
        background='200 separate sentences per target; anonymous class sequences available, hence privileged oracle-class observations in main channel. Proxy uses word frequency only.',
        scope='Fresh IDs; source classes known for training; no target semantic labels or keys enter align(); boundaries supplied; no parses evaluated.'))
    frozen=[OUT/n for n in ('datasets.json','models.json','observations.json','observation-truth.json','rekey-observations.json','rekey-truth.json','manifest.json')]
    save(OUT/'fit-freeze.json',dict(inputs={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in frozen},note='All source templates/objectives/channels frozen before target scoring.'))
    print('Prepared',{k:(len(v),sum(len(s['tokens']) for s in v)) for k,v in data.items()},flush=True)


def produce(models,observations):
    rows=[]
    for obs in observations:
        for template in ('pooled','jerome','palladius'):
            if template!='pooled' and (obs['noise']!=0 or obs['condition']!='ordered'):continue
            model=models[template]['coarse' if obs['family']=='frequency_proxy' else obs['family']]
            result=align(model,obs['sequences'],obs['observed'],bijective=obs['bijective'])
            rows.append(dict(id=obs['id'],template=template,methods=result))
    return rows


def run():
    if not OUT.exists():prepare()
    if (OUT/'predictions.json').exists():raise ValueError('Preserve predictions')
    for p,h in load(OUT/'fit-freeze.json')['inputs'].items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h,p
    rows=produce(load(OUT/'models.json'),load(OUT/'observations.json'));save(OUT/'predictions.json',rows)
    print(f'{len(rows)} exact alignment problems saved; no target labels used in objective or selection.',flush=True)

if __name__=='__main__':run()
