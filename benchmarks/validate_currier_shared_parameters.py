"""Audit both shared-parameter stages, expected collisions and level/contrast fit."""
from collections import Counter
import json
import math
from pathlib import Path
import random
from statistics import mean
from benchmarks import currier_shared_parameters as experiment
from benchmarks import currier_shared_contractions as contractions
from benchmarks import currier_mechanism_comparison as base
from benchmarks import currier_alphabet_comparison as cipher
from voynich_smt.data.corpus import digest,write_json

def expected_direct(words,book,mode,seed):
    frequency=Counter(words);n=len(words);length=0;collision=0
    for w,f in frequency.items():
        if mode=='independent':
            length+=f*sum(sum(len(code) for code in book[u])/len(book[u]) for u in w)/n
            collision+=(f/n)**2/math.prod(len(book[u]) for u in w)
        else:
            # Independent copy of the frozen deterministic selection formula.
            import hashlib
            out=[]
            for i,u in enumerate(w):
                key=json.dumps([seed,list(w),i],separators=(',',':'))
                choice=int(hashlib.sha256(key.encode()).hexdigest()[:8],16)%len(book[u]);out+=book[u][choice]
            length+=f*len(out)/n;collision+=(f/n)**2
    return {'mean_word_length':length,'within_folio_repeat_pair_rate':collision}

def validate():
    old=json.loads((experiment.OUT/'report.json').read_text());new=json.loads((contractions.OUT/'report.json').read_text());parent=json.loads(cipher.PARENT.read_text());raw=json.loads(experiment.census.SOURCE.read_text());config=json.loads(contractions.CONFIG.read_text())
    for module,report in ((experiment,old),(contractions,new)):
        p=json.loads((module.OUT/'prepared.json').read_text());assert digest(p)==report['prepared_sha256']
        for path,sha in p['code_sha256'].items():assert digest(Path(path).read_text())==sha
        assert p['parent_sha256']==digest(parent)
    assert digest(raw)==json.loads((experiment.OUT/'prepared.json').read_text())['source_sha256']
    cp=json.loads((contractions.OUT/'prepared.json').read_text());assert cp['baseline_sha256']==digest(old) and cp['config_sha256']==digest(config)
    rows=old['conditional_source_half_candidates']+new['candidates'];books={**old['encoders'],**new['encoders']}
    expansions={'<'+r['id']+'>':r['expansion'] for r in config['rules']}
    for source,paths in new['unitizations'].items():
        assert all(''.join(expansions.get(u,u) for u in path)==w for w,path in paths.items())
    for row in rows:
        book=books[row['id']];codes=[tuple(c) for cs in book.values() for c in cs]
        assert len(codes)==len(set(codes)) and all(not (len(a)<len(b) and b[:len(a)]==a) for a in codes for b in codes)
        assert set(g for c in codes for g in c)<=set(parent['glyphs'])
        stream=base.natural_stream(parent['sources'][row['source']]);half=len(stream)//2
        for label,part in [('A',stream[:half]),('B',stream[half:])]:
            words=[w for w in part if w is not None]
            if row['model'].startswith('contracted'):words=[tuple(new['unitizations'][row['source']][w]) for w in words]
            expected=expected_direct(words,book,'independent' if row['model'].endswith('independent') else 'deterministic',row['seed']+10)
            for k,v in expected.items():assert abs(v-row['predictions'][label][k])<1e-10
        for k,v in row['delta'].items():assert abs(v-(row['predictions']['B'][k]-row['predictions']['A'][k]))<1e-12
        error=abs(row['predictions']['A']['mean_word_length']-old['observed']['development']['A']['mean_word_length'])
        assert abs(error-row['A_development_mean_absolute_error'])<1e-12
    assert len(rows)==63
    selected=min(rows,key=lambda r:(r['A_development_mean_absolute_error'],r['id']));assert selected==new['selected_on_A_mean_only']
    fs,_,_=experiment.census.extract(raw['records'],'clean-words');split={label:experiment.split_folios(fs[label]) for label in ('A','B')}
    for label in ('A','B'):
        assert set(split[label]['development']).isdisjoint(split[label]['evaluation'])
        for part in ('development','evaluation'):assert experiment.observable(split[label][part])==old['observed'][part][label]
    # Separate absolute-level intervals to reject models matching only a contrast.
    rng=random.Random(94001);levels={}
    for label in ('A','B'):
        folios=list(split[label]['evaluation'].values());draws=[]
        for _ in range(1000):
            sample=rng.choices(folios,k=len(folios));draws.append(sum(len(w) for ws in sample for w in ws)/sum(map(len,sample)))
        levels[label]=[sorted(draws)[24],sorted(draws)[974]]
    matches=[r['id'] for r in rows if all(levels[l][0]<=r['predictions'][l]['mean_word_length']<=levels[l][1] for l in ('A','B')) and all(r['delta_inside_evaluation_interval'].values())]
    result={'validated':True,'candidate_count':len(rows),'absolute_mean_intervals':levels,'joint_level_and_contrast_matches':matches,
      'selected':selected['id'],'checks':'Both frozen stages and contraction config; prefix-free unique keys/output alphabet; reversible contraction expansion; independently calculated shared-key expected lengths/collision rates; delta/error calculations; selection by A-only mean; disjoint manuscript folio splits; absolute-level resampling check.'}
    write_json(experiment.OUT/'validation.json',result);write_json(contractions.OUT/'validation.json',result)
    print(json.dumps(result,indent=2))

if __name__=='__main__':validate()
