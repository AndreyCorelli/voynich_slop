"""Independent weighted minimum-path and distribution validation."""
from collections import Counter
import json
from benchmarks import broader_contraction_capacity as m
from benchmarks.contraction_distribution_validation import windows,checkdistribution,checkenvelope
from voynich_smt.data.corpus import digest,write_json


def allowed(word,i,r):
    end=i+len(r['expansion'])
    if word[i:end]!=r['expansion']: return False
    if r['position'] in ('initial','whole') and i: return False
    if r['position'] in ('final','whole') and end!=len(word): return False
    if 'left' in r and (i==0 or word[i-1]!=r['left']): return False
    if 'right' in r and end<len(word) and word[end] in 'aeiou': return False
    return True


def minimum(word,rules,one):
    costs=[len(word)]*(len(word)+1); costs[-1]=0
    for i in range(len(word)-1,-1,-1):
        costs[i]=1+costs[i+1]
        for r in rules:
            if allowed(word,i,r): costs[i]=min(costs[i],(1 if one else r['units'])+costs[i+len(r['expansion'])])
    return costs[0]


def validate():
    p=m.prepare(); reports=[]; rows={}; types=tokens=0
    for i in range(1,8):
        r=json.loads((m.OUT/f'iteration-{i}.json').read_text())
        assert r['plan']==json.loads((m.OUT/f'plan-{i}.json').read_text())
        assert r['plan']['prepared_sha256']==digest(p) and r['plan']['selection'] is False
        assert r['plan']['previous_sha256']==(digest(reports[-1]) if reports else None)
        reports.append(r)
        for s,profiles in r['results'].items(): rows.setdefault(s,{}).update(profiles)
    for source,profiles in rows.items():
        segments=p['sources'][source]['segments']; frequencies=Counter(w for s in segments for w in s if w is not None)
        for profile,row in profiles.items():
            rules=[r for r in p['inventory']['rules'] if r['id'] in p['inventory']['profiles'][profile]]; lookup={'<'+r['id']+'>':r for r in rules}; one=profile=='one-unit-macro-envelope'; lengths={}; hits=Counter(); table=row['word_table']
            assert set(table)==set(frequencies)
            for word,n in frequencies.items():
                saved=table[word]; lengths[word]=minimum(word,rules,one)
                assert saved['count']==n and saved['letters']==len(word) and saved['minimum_units']==lengths[word]
                offset=cost=0
                for symbol in saved['witness']:
                    if symbol in lookup:
                        r=lookup[symbol]; assert allowed(word,offset,r); offset+=len(r['expansion']); cost+=1 if one else r['units']; hits[r['id']]+=n
                    else:
                        assert len(symbol)==1 and word[offset]==symbol; offset+=1; cost+=1
                assert offset==len(word) and cost==lengths[word]; types+=1; tokens+=n
            hist=Counter()
            for w,n in frequencies.items(): hist[lengths[w]]+=n
            checkdistribution(row['words'],hist,1); checkdistribution(row['windows'],windows(segments,lengths),22)
            letters=sum(len(w)*n for w,n in frequencies.items()); units=sum(lengths[w]*n for w,n in frequencies.items())
            assert row['letters']==letters and row['minimum_units']==units and row['letters_saved_fraction']==1-units/letters
            assert dict(hits)==row['rule_occurrences_in_one_minimum_path']
            summary=reports[-1]['summary'][source][profile]; assert summary=={'minimum_mean':row['words']['mean'],'letter_saving':row['letters_saved_fraction']}
            for kind in ('words','windows'):
                for rep,target in p['targets'].items():
                    record=reports[-1]['comparisons'][source][profile][kind][rep]
                    checkenvelope(row[kind]['histogram'],target[kind]['histogram'],record)
                    assert record['mean_emission_headroom']==target[kind]['mean']/row[kind]['mean']
    result={'status':'passed','sources':len(rows),'profiles_per_source':4,'independent_weighted_minimum_word_type_checks':types,'token_occurrences_across_profiles':tokens,'rule_scope_cost_and_witness_checks':True,'rational_quantile_integral_checks':True,'solver_calls':0,'scope':'Reverse weighted dynamic programming, legal scope/cost/expansion paths, histograms and quantile comparisons independently checked; source parsing and historical evidence judgments reused.'}
    write_json(m.OUT/'validation.json',result); print(result,flush=True)

if __name__=='__main__': validate()
