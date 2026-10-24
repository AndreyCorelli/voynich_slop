"""Seven-stage offline capacity audit of a frozen reversible contraction inventory."""
import argparse
from collections import Counter,deque
from functools import lru_cache
import json
from pathlib import Path
from benchmarks import historical_word_lengths as historical
from benchmarks import expanded_medieval_latin as expanded
from benchmarks import latin_contractions as contractions
from benchmarks import manuscript_width_audit as manuscript
from benchmarks.eva_tokenization import grouped_word
from voynich_smt.data.corpus import digest,write_json
OUT=Path('experiments/results/contraction-distribution-audit')
PROFILES=('letters','ae-only','bounded-seven')


def distribution(hist,divisor=1):
    h={int(k):v for k,v in hist.items()}; count=sum(h.values())
    def rank(index):
        cumulative=0
        for k,n in sorted(h.items()):
            cumulative+=n
            if index<cumulative: return k/divisor
    def quantile(q):
        position=(count-1)*q; low=int(position); high=min(low+1,count-1)
        return rank(low)+(rank(high)-rank(low))*(position-low)
    return {'count':count,'mean':sum(k*n for k,n in h.items())/(count*divisor),'p05':quantile(.05),'p25':quantile(.25),'median':quantile(.5),'p75':quantile(.75),'p95':quantile(.95),'histogram':dict(sorted(h.items()))}


def window_hist(segments,values):
    hist=Counter()
    for segment in segments:
        queue=deque(); total=0
        for word in segment:
            if word is None: queue.clear(); total=0; continue
            value=values[word]; queue.append(value); total+=value
            if len(queue)>22: total-=queue.popleft()
            if len(queue)==22: hist[total]+=1
    return hist


def envelope(source,target):
    """Optimistic monotone coupling with arbitrary word/window reordering."""
    a={int(k):n for k,n in source.items()}; b={int(k):n for k,n in target.items()}; na=sum(a.values()); nb=sum(b.values())
    thresholds=sorted(set(a)|set(b)); shortfalls={str(t):sum(n for k,n in b.items() if k<=t)/nb-sum(n for k,n in a.items() if k<=t)/na for t in thresholds}
    # Integer common mass units avoid floating-point quantile boundary loss.
    left=iter(sorted(a.items())); right=iter(sorted(b.items())); x,n=next(left); y,m=next(right); n*=nb; m*=na; removed=0
    while True:
        mass=min(n,m); removed+=mass*max(x-y,0); n-=mass; m-=mass
        if n==0:
            try: x,n=next(left); n*=nb
            except StopIteration: break
        if m==0:
            try: y,m=next(right); m*=na
            except StopIteration: break
    return {'minimum_extra_unit_removal_per_item':removed/(na*nb),'maximum_short_item_fraction_deficit':max(0,max(shortfalls.values())),'short_item_fraction_deficits':shortfalls}


@lru_cache(maxsize=1)
def prepare():
    inventory=json.loads(contractions.CONFIG.read_text()); contractions.validate_inventory(inventory)
    sources={}; segments,metadata=historical.caesar_segments(); sources['caesar']={'segments':segments,'metadata':metadata,'language':'latin'}
    for name,file,start in (('aquinas','latin-aquinas-ente.html','Quia parvus error'),('caroli','latin-caroli.html','Secundis sedentibus')):
        segments,metadata=historical.latin_segments(file,start); sources[name]={'segments':segments,'metadata':metadata,'language':'latin'}
    for work in expanded.WORKS:
        segments,metadata,quality=expanded.load_work(work); sources[work['id']]={'segments':segments,'metadata':metadata,'quality':quality,'language':'latin'}
    for name,segments,metadata in historical.german_sources(): sources[name]={'segments':segments,'metadata':metadata,'language':'german-reference'}
    rawpath=Path('data/processed/zl-eva.json'); raw=json.loads(rawpath.read_text()); targets={}
    for rep in ('atomic','existing-grouped'):
        segments=[]; current=[]; folio=None
        for record in raw['records']:
            if record['folio']!=folio:
                if current: segments.append(current)
                current=[]; folio=record['folio']
            current.append(''.join(record['tokens']) if manuscript.clean(record) else None)
        if current: segments.append(current)
        words=[w for s in segments for w in s if w is not None]
        lengths={w:len(w) if rep=='atomic' else len(grouped_word(list(w))) for w in set(words)}
        targets[rep]={'words':distribution(Counter(lengths[w] for w in words)),'windows':distribution(window_hist(segments,lengths),22)}
    p={'inventory':inventory,'sources':sources,'targets':targets,'manuscript_source_sha256':digest(rawpath.read_text()),'code_sha256':{str(path):digest(path.read_text()) for path in (Path(__file__),Path(historical.__file__),Path(expanded.__file__),Path(contractions.__file__),Path(manuscript.__file__))},
       'scope':'Fixed existing seven Latin reversible units; no additions or solver. Full optional maximum-compression envelope, tokenweighted per-source word and overlapping22wordwindow distributions. German is letters-only reference, legacy normalization/short-form caveats, no Latin rules asserted for German. Atomic and existing groupedEVA references, not proven glyph inventories. Arbitrary monotone quantilecoupling gives optimistic additionalremoval and shorttailcapacity deficits under exact empiricalfrequency matching. Ignores order/sharedkey/repetition and attainableintermediatecounts. Maximalcompression is capacity not actualscribalusage. Meanemission headroom must >=1 for this exactfrequency benchmark; passingnotfeasibility. No languageprobabilities or historicalmechanism inference.'}
    p=json.loads(json.dumps(p)); path=OUT/'prepared.json'
    if path.exists(): assert json.loads(path.read_text())==p
    else: write_json(path,p)
    return p


def audit(data,profile,inventory):
    rules=[r for r in inventory['rules'] if r['id'] in inventory['profiles'][profile]]
    frequencies=Counter(w for s in data['segments'] for w in s if w is not None); table={}
    for word in frequencies:
        paths=contractions.unitizations(word,rules); minimum=min(paths); witness=paths[minimum]
        assert contractions.expand(witness,rules)==word
        table[word]={'count':frequencies[word],'letters':len(word),'minimum_units':minimum,'witness':witness}
    letters=sum(len(w)*n for w,n in frequencies.items()); units=sum(table[w]['minimum_units']*n for w,n in frequencies.items())
    return {'profile':profile,'words':distribution(Counter({})) if not table else distribution(Counter({k:sum(v['count'] for v in table.values() if v['minimum_units']==k) for k in set(v['minimum_units'] for v in table.values())})),
            'windows':distribution(window_hist(data['segments'],{w:v['minimum_units'] for w,v in table.items()}),22),'letters_saved_fraction':1-units/letters,'letters':letters,'minimum_units':units,'word_table':table}


def iteration(i):
    p=prepare(); path=OUT/f'iteration-{i}.json'
    if path.exists(): return json.loads(path.read_text())
    previous=json.loads((OUT/f'iteration-{i-1}.json').read_text()) if i>1 else None
    selected=['caesar'] if i==2 else ['aquinas','caroli'] if i==3 else [w['id'] for w in expanded.WORKS] if i==4 else [s for s,d in p['sources'].items() if d['language']=='german-reference'] if i==5 else []
    plan={'iteration':i,'prepared_sha256':digest(p),'previous_sha256':digest(previous) if previous else None,'sources':selected,'selection':False}; write_json(OUT/f'plan-{i}.json',plan); result={'plan':plan,'results':{}}
    for source in selected:
        profiles=PROFILES if p['sources'][source]['language']=='latin' else ('letters',)
        result['results'][source]={profile:audit(p['sources'][source],profile,p['inventory']) for profile in profiles}
    if i in (6,7):
        rows={s:v for j in range(2,6) for s,v in json.loads((OUT/f'iteration-{j}.json').read_text())['results'].items()}; result['comparisons']={}
        kind='words' if i==6 else 'windows'
        for source,profiles in rows.items():
            result['comparisons'][source]={profile:{rep:envelope(row[kind]['histogram'],target[kind]['histogram'])|{'mean_units':row[kind]['mean'],'target_mean':target[kind]['mean'],'mean_emission_headroom':target[kind]['mean']/row[kind]['mean'],'minimum_additional_mean_shortening_fraction':max(0,1-target[kind]['mean']/row[kind]['mean'])} for rep,target in p['targets'].items()} for profile,row in profiles.items()}
        result['assessment']='Maximum-compression envelope versus fullworddistribution.' if i==6 else 'Compare22wordwindow distributions; stop this inventory rather than broaden rules to obtain capacity. Sample-specific empirical benchmarks do not exclude Latin or German.'
    write_json(path,result); print('Stage',i,{s:{k:round(v['letters_saved_fraction'],4) for k,v in profiles.items()} for s,profiles in result['results'].items()},flush=True); return result

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--run',action='store_true'); args=parser.parse_args()
    if args.run:
        for i in range(1,8): iteration(i)
    else: prepare()
