"""Independent labeled-assignment expectation, inventory, decoding and split audits."""
from collections import Counter
import json
from statistics import mean
from benchmarks import adjacent_order_replication as m
from benchmarks import multilingual_character as corpus
from voynich_smt.data.corpus import digest, write_json


def group(b,i):
    n=b['positions'][i]; return ('0' if n==0 else '1' if n==1 else '2-3' if n<4 else '4+',len(b['words'][i]))


def independent(b):
    edges=[]
    for i in range(1,len(b['words'])):
        a=[j for j in range(len(b['words'])) if group(b,j)==group(b,i-1)]; z=[j for j in range(len(b['words'])) if group(b,j)==group(b,i)]
        pairs=[(j,k) for j in a for k in z if j!=k]; expected=sum(b['words'][j]==b['words'][k] for j,k in pairs)/len(pairs)
        edges.append({'observed':int(b['words'][i]==b['words'][i-1]),'expected':expected,'within':b['line_ids'][i]==b['line_ids'][i-1]})
    return edges


def inventory(b): return Counter((group(b,i),''.join(w)) for i,w in enumerate(b['words']))


def validate():
    p=m.prepare(); old=corpus.prepare(); reports=[]; results={}; decoded=edges_checked=0
    for source,data in p['sources'].items():
        train={s for b in data['training'] for s in b['source_slots']}; held={s for b in data['heldout'] for s in b['source_slots']}; assert len(train)==1024 and len(held)==2848 and not train&held
        if source!='german-253':
            previous={s for name,c in old['cases'].items() if c['source']==source and c['variant'] in ('primary','replication') for split in ('train','heldout') for b in c[split] for s in b['source_slots']}
            assert not (train|held)&previous
    for n,c in p['cases'].items():
        for original,payload,encoded in zip(p['sources'][c['source']]['heldout'],c['payload'],c['encoded'],strict=True):
            assert inventory(original)==inventory(payload) and original['positions']==payload['positions'] and original['line_ids']==payload['line_ids']
            assert list(map(len,original['words']))==list(map(len,payload['words']))
            key=c['key']; inverse={v:k for k,v in key['payload'].items()}; assert len(inverse)==26
            for i,(truth,w) in enumerate(zip(payload['words'],encoded['words'],strict=True)):
                marked=i>0 and encoded['line_ids'][i]==encoded['line_ids'][i-1] and i%16==0
                if marked: assert w[0]==key['marker'][encoded['words'][i-1][-1]]
                assert [inverse[v] for v in (w[1:] if marked else w)]==truth; decoded+=1
    for i in range(1,8):
        r=json.loads((m.OUT/f'iteration-{i}.json').read_text()); assert r['plan']==json.loads((m.OUT/f'plan-{i}.json').read_text())
        assert r['plan']['prepared_sha256']==digest(p) and r['plan']['previous_sha256']==(digest(reports[-1]) if reports else None) and r['plan']['cases']==p['stages'][str(i)]; reports.append(r)
        for n,result in r['results'].items():
            results[n]=result
            for representation in ('payload','encoded'):
                expected_rows=[]
                for row,b in zip(result[representation]['rows'],p['cases'][n][representation],strict=True):
                    expected=independent(b); assert row['edges']==expected; edges_checked+=len(expected)
                    allgain=mean(e['observed']-e['expected'] for e in expected); assert abs(row['adjusted']-allgain)<1e-12
                    within=[e for e in expected if e['within']]; expected_rows.append({'observed_repeat':mean(e['observed'] for e in expected),'expected_repeat':mean(e['expected'] for e in expected),'adjusted':allgain,'within_adjusted':mean(e['observed']-e['expected'] for e in within) if within else None})
                for k in ('observed_repeat','expected_repeat','adjusted','within_adjusted'): assert abs(result[representation][k]-mean(row[k] for row in expected_rows if row[k] is not None))<1e-12
    grouped={s:{kind:{rep:mean(results[f'{s}-{kind}-{seed}'][rep]['adjusted'] for seed in m.SEEDS) for rep in ('payload','encoded')} for kind in m.KINDS} for s in m.SOURCES}
    assert reports[5]['grouped']==grouped and reports[6]['grouped']==grouped
    write_json(m.OUT/'validation.json',{'status':'passed','stages':7,'cases':len(results),'independent_edge_expectations':edges_checked,'independently_decoded_words':decoded,'disjoint_excerpt_checks':True,'block_position_length_inventories':True,'summary':grouped}); print('Validated',edges_checked,'edge expectations and',decoded,'decoded words',flush=True)

if __name__=='__main__': validate()
