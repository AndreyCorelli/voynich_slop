"""Oracle dependency/role objectives; unchanged near-truth attack optimizer."""
import argparse,hashlib,json,random
from functools import lru_cache
from pathlib import Path
import numpy as np
from benchmarks.latin_adversarial_objective import OUT as SOURCE,STARTS,BUDGETS,quality
from benchmarks.latin_relative_search import grammatical_metrics
from voynich_smt.data.corpus import digest,write_json
OUT=Path('experiments/results/latin-oracle-structure')
MODELS={'edges_only':(1,0),'roles_only':(0,1),'edges_and_roles':(1,1)}


def run(validate=False):
    files=[SOURCE/'dataset.json',SOURCE/'morphology.json',Path(__file__),Path('benchmarks/latin_relative_search.py')]
    protocol={'files_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},'models':MODELS,'seeds':[907,919],'budgets':BUDGETS,'optimizer':'unchanged strict ascent, 25% swaps, 75% injective single replacement','objective':'negative count of violations against supplied gold edges and/or original token POS/role inflections; equal unit costs','scope':'strong oracle, no inferred dependency trees; same assisted fixtures/candidate pools. Preservation at a zero-violation maximum is by construction; repair is a search test.'}
    manifest={'protocol':protocol,'sha256':digest(protocol)}
    if (OUT/'manifest.json').exists():assert validate and json.loads((OUT/'manifest.json').read_text())==json.loads(json.dumps(manifest))
    else:write_json(OUT/'manifest.json',manifest)
    fixtures=json.loads((SOURCE/'dataset.json').read_text());entries=json.loads((SOURCE/'morphology.json').read_text())['entries'];results=[];excluded=[]
    for f in fixtures:
        if f['split']!='test':continue
        keys=sorted(f['truth']);index={t:i for i,t in enumerate(keys)}
        @lru_cache(maxsize=200000)
        def metrics(values):return grammatical_metrics(f['sentences'],dict(zip(keys,values)),f['truth'],entries)
        for name,(ew,rw) in MODELS.items():
            def score(m):return -ew*(m['eligible_gold_edges']-m['satisfied_gold_edges'])-rw*(m['role_inflection_eligible_tokens']-m['role_inflection_compatible_tokens'])
            for start in STARTS:
                initial=dict(f['starts'][start]);initial_values=tuple(initial[k] for k in keys);initial_metrics=metrics(initial_values)
                if start=='control_high' and (initial_metrics['gold_edge_accuracy']<1 or initial_metrics['role_inflection_accuracy']<1):
                    excluded.append({'fixture':f['id'],'model':name,'reason':'Control does not satisfy all measured oracle constraints'});continue
                for seed in (907,919):
                    rng=random.Random(seed);mapping=dict(initial);state=initial_values;current=score(initial_metrics);accepted=0;trace=[];worst_edges=worst_roles=0
                    def snapshot(step):
                        m=metrics(state);assert score(m)==current
                        return {'budget':step,'score':current,'grammar':m,'mapping':dict(mapping),'worst_high_scoring_edge_loss':worst_edges,'worst_high_scoring_role_loss':worst_roles}
                    trace.append(snapshot(0))
                    for step in range(1,5001):
                        changes=None;t=rng.choice(f['active'])
                        if rng.random()<.25:
                            other=rng.choice(f['active'])
                            if other!=t:changes={t:mapping[other],other:mapping[t]}
                        else:
                            target=rng.choice(f['pool'])
                            if target not in mapping.values():changes={t:target}
                        if changes:
                            values=list(state)
                            for k,v in changes.items():values[index[k]]=v
                            candidate=tuple(values);m=metrics(candidate);value=score(m)
                            if value>current:
                                mapping.update(changes);state=candidate;current=value;accepted+=1
                                worst_edges=max(worst_edges,initial_metrics['satisfied_gold_edges']-m['satisfied_gold_edges']);worst_roles=max(worst_roles,initial_metrics['role_inflection_compatible_tokens']-m['role_inflection_compatible_tokens'])
                        if step in BUDGETS:trace.append(snapshot(step))
                    results.append({'fixture':f['id'],'document':f['document'],'model':name,'start':start,'seed':seed,'accepted':accepted,'snapshots':trace})
            print('ATTACKED',f['id'],name,flush=True)
    summaries={}
    for name in MODELS:
        runs=[r for r in results if r['model']==name];bybudget=[]
        for budget in BUDGETS:
            rr=[{**r,'snapshots':[r['snapshots'][0],next(s for s in r['snapshots'] if s['budget']==budget)]} for r in runs];q=quality(rr)
            corrupt=[r for r in rr if r['start'].startswith('corrupt_')];q['corrupted_all_constraints_restored']=sum(r['snapshots'][-1]['grammar']['gold_edge_accuracy']==1 and r['snapshots'][-1]['grammar']['role_inflection_accuracy']==1 for r in corrupt);q['corrupted_runs']=len(corrupt);bybudget.append({'budget':budget,**q})
        nonworse=[]
        for r in runs:
            a=next(s for s in r['snapshots'] if s['budget']==100)['grammar'];b=r['snapshots'][-1]['grammar'];nonworse.append(b['satisfied_gold_edges']>=a['satisfied_gold_edges'] and b['role_inflection_compatible_tokens']>=a['role_inflection_compatible_tokens'])
        summaries[name]={'budgets':bybudget,'budget_nonregression':float(np.mean(nonworse)),'fresh_palladius':quality([r for r in runs if r['document']=='palladius.opus_agriculturae'])}
    report={'manifest_sha256':manifest['sha256'],'runs':results,'summaries':summaries,'excluded_controls':excluded,'scope':'Oracle checks are supplied to objective and reused for evaluation; not an independent validation of linguistic correctness. Does not recover a parse or infer roles.'}
    if validate:assert json.loads((OUT/'report.json').read_text())==report;write_json(OUT/'validation.json',{'all_oracle_searches_replayed':True,'report_sha256':digest(report)})
    else:write_json(OUT/'report.json',report)
    print('RESULT',summaries,flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--validate',action='store_true');run(p.parse_args().validate)
