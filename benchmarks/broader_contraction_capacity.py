"""Seven frozen stages: documented broader macros and separate ambiguity envelopes."""
import argparse
from collections import Counter
from functools import lru_cache
import json
from pathlib import Path
from benchmarks import contraction_distribution_audit as prior
from voynich_smt.data.corpus import digest,write_json
CONFIG=Path('experiments/configs/latin-contractions-broader-v1.json')
OUT=Path('experiments/results/broader-contraction-capacity')


def applies(word,i,r):
    end=i+len(r['expansion'])
    return (word.startswith(r['expansion'],i) and (r['position'] not in ('initial','whole') or i==0)
            and (r['position'] not in ('final','whole') or end==len(word))
            and (not r.get('left') or i>0 and word[i-1]==r['left'])
            and (not r.get('right') or end==len(word) or word[end] not in 'aeiou'))


def minimum(word,rules,one_unit=False):
    paths=[None]*(len(word)+1); paths[0]=(0,[])
    for i in range(len(word)):
        if paths[i] is None: continue
        options=[(i+1,1,word[i])]
        options.extend((i+len(r['expansion']),1 if one_unit else r['units'],'<'+r['id']+'>') for r in rules if applies(word,i,r))
        for end,cost,label in options:
            candidate=(paths[i][0]+cost,paths[i][1]+[label])
            if paths[end] is None or candidate[0]<paths[end][0]: paths[end]=candidate
    return paths[-1]


def audit(source,profile,config):
    rules=[r for r in config['rules'] if r['id'] in config['profiles'][profile]]; frequencies=Counter(w for s in source['segments'] for w in s if w is not None); table={}; hits=Counter()
    expansion={'<'+r['id']+'>':r['expansion'] for r in rules}; one=profile=='one-unit-macro-envelope'
    for word,n in frequencies.items():
        units,path=minimum(word,rules,one); assert ''.join(expansion.get(v,v) for v in path)==word
        table[word]={'count':n,'letters':len(word),'minimum_units':units,'witness':path}
        for v in path:
            if v.startswith('<'): hits[v[1:-1]]+=n
    letters=sum(len(w)*n for w,n in frequencies.items()); units=sum(v['minimum_units']*v['count'] for v in table.values()); histogram=Counter()
    for v in table.values(): histogram[v['minimum_units']]+=v['count']
    return {'profile':profile,'letters':letters,'minimum_units':units,'letters_saved_fraction':1-units/letters,'rule_occurrences_in_one_minimum_path':dict(hits),'words':prior.distribution(histogram),'windows':prior.distribution(prior.window_hist(source['segments'],{w:v['minimum_units'] for w,v in table.items()}),22),'word_table':table}


@lru_cache(maxsize=1)
def prepare():
    base=prior.prepare(); config=json.loads(CONFIG.read_text()); ids={r['id'] for r in config['rules']}; assert len(ids)==len(config['rules'])
    for r in config['rules']: assert r['expansion'].isalpha() and 1<=r['units']<len(r['expansion']) and r['position'] in ('any','initial','final','whole') and r['source_url']
    for ids_profile in config['profiles'].values(): assert set(ids_profile)<=ids and len(ids_profile)==len(set(ids_profile))
    p={'prior_prepared_sha256':digest(base),'inventory':config,'inventory_sha256':digest(config),'sources':{s:d for s,d in base['sources'].items() if d['language']=='latin'},'targets':base['targets'],'code_sha256':digest(Path(__file__).read_text()),'prior_code_sha256':digest(Path(prior.__file__).read_text()),'scope':'Research-supported broader27macro core, two separate37rule nasal-disambiguated envelopes and27macro one-unit ceiling. No newrules afterfreeze. Retained-letter costs in core, additive nonoverlapping macros. Vowel nasal positions are explicit approximations, not fullsyllabification. Compare exact empirical frequency capacity word/windows versus fixed atomic/groupedEVA. No sharedkey, homophonic choices, solver, hiddenrecovery, naturalusage rate or historicalinference.'}
    p=json.loads(json.dumps(p)); path=OUT/'prepared.json'
    if path.exists(): assert json.loads(path.read_text())==p
    else: write_json(path,p)
    return p


def iteration(i):
    p=prepare(); path=OUT/f'iteration-{i}.json'
    if path.exists(): return json.loads(path.read_text())
    previous=json.loads((OUT/f'iteration-{i-1}.json').read_text()) if i>1 else None
    profile='broader-core' if i in (2,3) else 'final-nasal-envelope' if i==4 else 'syllable-nasal-envelope' if i==5 else 'one-unit-macro-envelope' if i==6 else None
    sources=['caesar'] if i==2 else [s for s in p['sources'] if s!='caesar'] if i==3 else list(p['sources']) if i in (4,5,6) else []
    plan={'iteration':i,'prepared_sha256':digest(p),'previous_sha256':digest(previous) if previous else None,'profile':profile,'sources':sources,'selection':False}; write_json(OUT/f'plan-{i}.json',plan); r={'plan':plan,'results':{}}
    for source in sources: r['results'][source]={profile:audit(p['sources'][source],profile,p['inventory'])}
    if i==7:
        results={}
        for j in range(2,7):
            for s,profiles in json.loads((OUT/f'iteration-{j}.json').read_text())['results'].items(): results.setdefault(s,{}).update(profiles)
        r['summary']={}; r['comparisons']={}
        for s,profiles in results.items():
            r['summary'][s]={}; r['comparisons'][s]={}
            for profile,row in profiles.items():
                r['summary'][s][profile]={'minimum_mean':row['words']['mean'],'letter_saving':row['letters_saved_fraction']}
                r['comparisons'][s][profile]={kind:{rep:prior.envelope(row[kind]['histogram'],target[kind]['histogram'])|{'mean_emission_headroom':target[kind]['mean']/row[kind]['mean']} for rep,target in p['targets'].items()} for kind in ('words','windows')}
        r['decision']='Report mean and tail separately; capacity-positive ambiguous/one-unit envelopes do not establish a uniquely decodable historical encoder. Stop all fixed profiles without widening inventory.'
        print(json.dumps(r['summary']),flush=True)
    write_json(path,r); print('Stage',i,profile,{s:round(v[profile]['words']['mean'],4) for s,v in r['results'].items()},flush=True); return r

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--run',action='store_true'); args=parser.parse_args()
    if args.run:
        for i in range(1,8): iteration(i)
    else: prepare()
