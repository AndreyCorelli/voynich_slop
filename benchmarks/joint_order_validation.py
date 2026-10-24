"""Independent labeled-index boundary and repeat audits for joint constraints."""
import json
from statistics import mean
from benchmarks import joint_order_constraints as m
from benchmarks.adjacent_order_validation import group, independent, inventory
from voynich_smt.data.corpus import digest, write_json


def validate():
    base,p=m.prepare(); previous=None; edges=decoded=cases=0
    for stage in range(1,8):
        r=json.loads((m.OUT/f'iteration-{stage}.json').read_text())
        assert r['plan']==json.loads((m.OUT/f'plan-{stage}.json').read_text())
        assert r['plan']['prepared_sha256']==digest(p)
        assert r['plan']['previous_sha256']==(digest(previous) if previous else None)
        previous=r
        for name,result in r['results'].items():
            cases+=1; source=r['plan']['source']; data=base['sources'][source]; gains=[]; repeats=[]
            for original,b,e,stored,repeat in zip(data['heldout'],result['payload'],result['encoded'],result['mapped']['blocks'],result['repeat']['rows'],strict=True):
                assert inventory(original)==inventory(b)
                assert b['positions']==original['positions'] and b['line_ids']==original['line_ids']
                rows=[]
                for i in range(1,len(b['words'])):
                    if b['line_ids'][i]!=b['line_ids'][i-1]: continue
                    a=[j for j in range(len(b['words'])) if group(b,j)==group(b,i-1)]
                    z=[j for j in range(len(b['words'])) if group(b,j)==group(b,i)]
                    pairs=[(j,k) for j in a for k in z if j!=k]
                    expectation=sum(data['mapping'].get(b['words'][j][-1])==b['words'][k][0] for j,k in pairs)/len(pairs)
                    observed=int(data['mapping'].get(b['words'][i-1][-1])==b['words'][i][0])
                    rows.append({'observed':observed,'expected':expectation}); edges+=1
                assert rows==stored['rows']; gain=mean(v['observed']-v['expected'] for v in rows)
                assert abs(gain-stored['adjusted'])<1e-12; gains.append(gain)
                repeatrows=independent(e); assert repeatrows==repeat['edges']; edges+=len(repeatrows)
                repeats.append(mean(v['observed']-v['expected'] for v in repeatrows))
                key=result['key']; inverse={v:k for k,v in key['payload'].items()}
                for i,(truth,w) in enumerate(zip(b['words'],e['words'],strict=True)):
                    marked=i>0 and e['line_ids'][i]==e['line_ids'][i-1] and i%16==0
                    if marked: assert w[0]==key['marker'][e['words'][i-1][-1]]
                    assert [inverse[v] for v in (w[1:] if marked else w)]==truth; decoded+=1
            assert abs(mean(gains)-result['mapped']['adjusted'])<1e-12
            assert abs(mean(repeats)-result['repeat']['adjusted'])<1e-12
    report={'status':'passed','cases':cases,'edge_expectations':edges,'decoded_words':decoded,'scope':'Independent index-pair expectations, inventory preservation, inverse encoding, plan chain. Not independent raw-source parsing or proof of beam optimality.'}
    write_json(m.OUT/'validation.json',report); print(report)

if __name__=='__main__': validate()
