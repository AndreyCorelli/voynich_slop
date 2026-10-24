"""Independent minimum-unit, histogram, quantile-coupling and barrier audit."""
from collections import Counter
from fractions import Fraction
import json
from pathlib import Path
from benchmarks import contraction_distribution_audit as m
from voynich_smt.data.corpus import digest,write_json


def minimal(word,rules):
    costs=[None]*(len(word)+1); costs[-1]=0
    for i in range(len(word)-1,-1,-1):
        candidates=[1+costs[i+1]]
        for r in rules:
            text=r['expansion']; end=i+len(text)
            scope=r['position']
            if word[i:end]!=text: continue
            if scope in ('initial','whole') and i!=0: continue
            if scope in ('final','whole') and end!=len(word): continue
            candidates.append(1+costs[end])
        costs[i]=min(candidates)
    return costs[0]


def windows(segments,lengths):
    counts=Counter()
    for segment in segments:
        run=[]
        for w in [*segment,None]:
            if w is None:
                for i in range(len(run)-21): counts[sum(run[i:i+22])]+=1
                run=[]
            else: run.append(lengths[w])
    return counts


def checkdistribution(record,hist,divisor):
    assert {int(k):v for k,v in record['histogram'].items()}==dict(hist)
    assert record['count']==sum(hist.values())
    assert abs(record['mean']-sum(k*n for k,n in hist.items())/sum(hist.values())/divisor)<1e-12
    ordered=sorted(k for k,n in hist.items() for _ in range(n))
    for name,q in (('p05',.05),('p25',.25),('median',.5),('p75',.75),('p95',.95)):
        index=q*(len(ordered)-1); low=int(index); high=min(low+1,len(ordered)-1)
        expected=(ordered[low]+(ordered[high]-ordered[low])*(index-low))/divisor
        assert abs(record[name]-expected)<1e-12


def checkenvelope(source,target,record):
    a={int(k):n for k,n in source.items()}; b={int(k):n for k,n in target.items()}
    def cumulative(hist):
        n=sum(hist.values()); running=0; values=[]
        for length,count in sorted(hist.items()):
            running+=count; values.append((Fraction(running,n),length))
        return values
    ca,cb=cumulative(a),cumulative(b); points=sorted({Fraction(0),*[q for q,v in ca],*[q for q,v in cb]})
    def quantile(values,q): return next(length for end,length in values if q<end)
    removal=sum((z-x)*max(quantile(ca,(x+z)/2)-quantile(cb,(x+z)/2),0) for x,z in zip(points,points[1:]))
    assert abs(float(removal)-record['minimum_extra_unit_removal_per_item'])<1e-12
    deficits={str(t):sum(n for k,n in b.items() if k<=t)/sum(b.values())-sum(n for k,n in a.items() if k<=t)/sum(a.values()) for t in set(a)|set(b)}
    assert deficits==record['short_item_fraction_deficits']
    assert record['maximum_short_item_fraction_deficit']==max(0,max(deficits.values()))


def validate():
    p=m.prepare(); reports=[]; rows={}; wordtypes=occurrences=0
    for i in range(1,8):
        r=json.loads((m.OUT/f'iteration-{i}.json').read_text())
        assert r['plan']==json.loads((m.OUT/f'plan-{i}.json').read_text())
        assert r['plan']['prepared_sha256']==digest(p)
        assert r['plan']['previous_sha256']==(digest(reports[-1]) if reports else None)
        assert r['plan']['selection'] is False; reports.append(r); rows.update(r['results'])
    # Independently rebuild the two manuscript representations and barriers.
    raw=json.loads(Path('data/processed/zl-eva.json').read_text()); assert digest(Path('data/processed/zl-eva.json').read_text())==p['manuscript_source_sha256']
    for rep,target in p['targets'].items():
        segments=[]; current=[]; folio=None
        for r in raw['records']:
            if r['folio']!=folio:
                if current: segments.append(current)
                current=[]; folio=r['folio']
            units=r['tokens']; eligible=r.get('excluded_reason') is None and bool(units) and all(len(c)==1 and 'a'<=c<='z' for c in units)
            if not eligible: current.append(None); continue
            current.append(''.join(units))
        if current: segments.append(current)
        words=[w for s in segments for w in s if w is not None]; lengths={}
        for w in set(words):
            if rep=='atomic': lengths[w]=len(w); continue
            i=count=0
            while i<len(w):
                matches=[text for text in ('ch','sh','cth','ckh','cph','cfh') if w.startswith(text,i)]
                i+=max(map(len,matches)) if matches else 1; count+=1
            lengths[w]=count
        checkdistribution(target['words'],Counter(lengths[w] for w in words),1)
        checkdistribution(target['windows'],windows(segments,lengths),22)
    for source,profiles in rows.items():
        data=p['sources'][source]; frequencies=Counter(w for s in data['segments'] for w in s if w is not None)
        if data['language']=='german-reference': assert set(profiles)=={'letters'}
        for profile,row in profiles.items():
            rules=[r for r in p['inventory']['rules'] if r['id'] in p['inventory']['profiles'][profile]]
            table=row['word_table']; assert set(table)==set(frequencies); lengths={}
            expansion={'<'+r['id']+'>':r['expansion'] for r in rules}
            for word,n in frequencies.items():
                saved=table[word]; lengths[word]=minimal(word,rules)
                assert saved['count']==n and saved['letters']==len(word) and saved['minimum_units']==lengths[word]
                assert len(saved['witness'])==lengths[word] and ''.join(expansion.get(unit,unit) for unit in saved['witness'])==word
                wordtypes+=1; occurrences+=n
            checkdistribution(row['words'],Counter({k:sum(n for w,n in frequencies.items() if lengths[w]==k) for k in set(lengths.values())}),1)
            checkdistribution(row['windows'],windows(data['segments'],lengths),22)
            letters=sum(len(w)*n for w,n in frequencies.items()); units=sum(lengths[w]*n for w,n in frequencies.items())
            assert row['letters']==letters and row['minimum_units']==units and row['letters_saved_fraction']==1-units/letters
            for stage,kind in ((5,'words'),(6,'windows')):
                for rep,target in p['targets'].items():
                    record=reports[stage]['comparisons'][source][profile][rep]
                    checkenvelope(row[kind]['histogram'],target[kind]['histogram'],record)
                    assert record['mean_units']==row[kind]['mean'] and record['target_mean']==target[kind]['mean']
                    headroom=target[kind]['mean']/row[kind]['mean']; assert record['mean_emission_headroom']==headroom
                    assert record['minimum_additional_mean_shortening_fraction']==max(0,1-headroom)
    result={'status':'passed','sources':len(rows),'source_profile_rows':sum(len(v) for v in rows.values()),'independent_minimum_word_type_checks':wordtypes,'token_occurrences_across_profiles':occurrences,'target_histograms_and_barriers':True,'independent_quantile_coupling':True,'solver_calls':0,'scope':'Reverse dynamic programming minima, witness expansions, full word/window histograms and rational quantile integrals independently reconstructed; cached historical parsing reused.'}
    write_json(m.OUT/'validation.json',result); print(result,flush=True)

if __name__=='__main__': validate()
