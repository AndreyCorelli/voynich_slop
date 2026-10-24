"""Evaluation-only candidate coverage and joint reference-subgraph support."""
from collections import Counter
import hashlib
from pathlib import Path
from voynich_smt.complement_units import ComplementModel
from benchmarks.grammar_relative_constituents_iteration15_validate import FrozenAdapter
from benchmarks.grammar_complement_units_iteration17 import OUT,SIXTEEN,NINE,TEN,ARMS,load,save


def requirements(record,truth):
    return [(r['position'],truth[r['position']]['owner']) for r in record['model']['records']
        if r['position'] in truth and truth[r['position']]['owner'] in r['possible_parents']]


def coverage(rows,truth):
    totals=Counter()
    for row in rows:
        lookup={t['position']:t for t in truth if t['stream']==row['stream']}
        totals['annotated_nonfinite']+=len(lookup)
        for r in row['model']['records']:
            ref=lookup.get(r['position']);parents=r['possible_parents']
            totals['proposals']+=1;totals['annotated_proposals']+=ref is not None
            totals['reference_owner_available']+=bool(ref and ref['owner'] in parents)
            totals['conditional_unique']+=len(parents)==1
            totals['conditional_unique_correct']+=bool(len(parents)==1 and ref and parents==[ref['owner']])
            totals['unknown_possible']+=r['unknown_possible'];totals['firm_claims']+=r['firm_owner'] is not None
    return dict(totals)


def run():
    rows=load(OUT/'models.json');dev=load(NINE/'development-truth.json');old=load(TEN/'predictions.json')
    truth=load(SIXTEEN/'evaluation-truth.json');lookup={(t['stream'],t['position']):t for t in truth}
    adapter=FrozenAdapter(load(OUT/'morphology-lattice.json'));summary={};queries=[];targets=[];coord=[]
    for mode in ('reference_scope','predicted_scope'):
        for bounds in ('hidden','reference'):
            for arm in ARMS:summary[f'{mode}/{bounds}/{arm}']=coverage([r for r in rows if (r['mode'],r['boundaries'],r['arm'])==(mode,bounds,arm)],truth)
    for i,s in enumerate(dev):
        pred=next(r['prediction'] for r in old if (r['stream'],r['training'],r['features'],r['markers'],r['condition'])==(i,'oof','interactions','predicted','unrestricted'))
        local={t['position']:t for t in truth if t['stream']==i}
        for mode in ('reference_scope','predicted_scope'):
            scopes=({int(m):v['target'] for m,v in s['markers'].items() if v['kind']=='relative'} if mode=='reference_scope' else
                {m['position']:m['target'] for m in pred['marker_attachments'] if 'relative' in m['kinds'] and m['target'] is not None})
            for bounds in ('hidden','reference'):
                context={r['arm']:r for r in rows if (r['stream'],r['mode'],r['boundaries'])==(i,mode,bounds)}
                common=requirements(context['base_open'],local);expanded=requirements(context['units_open'],local)
                results={}
                for arm,options in ARMS.items():
                    model=ComplementModel(s['tokens'],s['finite'],adapter,scopes=tuple(scopes.items()),boundaries=s['boundaries'] if bounds=='reference' else (),**options)
                    results[arm]={'common_feasible':model.can_assign(common),'expanded_feasible':model.can_assign(expanded)}
                    queries.append(dict(stream=i,mode=mode,boundaries=bounds,arm=arm,
                        common_requirements=common,expanded_requirements=expanded,**results[arm]))
                for key in ('common_feasible','expanded_feasible'):
                    assert int(results['base_open'][key])<=int(results['frames_open'][key])<=int(results['units_open'][key])
                if mode=='reference_scope' and bounds=='hidden' and i in (4,41,45,47,61):
                    targets.append(dict(stream=i,text=' '.join(s['tokens']),requirements=expanded,results=results))
        row=next(r for r in rows if (r['stream'],r['mode'],r['boundaries'],r['arm'])==(i,'reference_scope','hidden','units_open'))
        paired={tuple(u['members']) for u in row['model']['units'] if len(u['members'])==2}
        for a,b in sorted(paired):
            left,right=lookup.get((i,a)),lookup.get((i,b));offset=next((begin for begin,end in zip((0,*s['boundaries'][:-1]),s['boundaries']) if begin<=b<end),None)
            annotated_coord=bool(left and right and left['form']=='Inf' and right['form']=='Inf' and
                left['owner'] is not None and left['owner']==right['owner'] and
                right['path'][0]['relation'].split(':')[0]=='conj' and right['path'][0]['head'] is not None and right['path'][0]['head']+offset==a)
            coord.append(dict(stream=i,members=[a,b],surfaces=[s['tokens'][a],s['tokens'][b]],
                annotated_direct_coordination=annotated_coord,text=' '.join(s['tokens'])))
    feasibility={}
    for mode in ('reference_scope','predicted_scope'):
        for bounds in ('hidden','reference'):
            for arm in ARMS:
                selected=[q for q in queries if (q['mode'],q['boundaries'],q['arm'])==(mode,bounds,arm)]
                feasibility[f'{mode}/{bounds}/{arm}']={
                    'common_streams':sum(bool(q['common_requirements']) for q in selected),
                    'common_feasible':sum(bool(q['common_requirements']) and q['common_feasible'] for q in selected),
                    'expanded_streams':sum(bool(q['expanded_requirements']) for q in selected),
                    'expanded_feasible':sum(bool(q['expanded_requirements']) and q['expanded_feasible'] for q in selected)}
    report={'scope':'Inspected development with supplied finite positions; annotation queries are evaluation only and do not choose production owners.',
        'controlled_probes':len(load(OUT/'controlled.json')),'coverage':summary,'feasibility':feasibility,
        'coordination_pairs':len(coord),'annotated_direct_coordination_pairs':sum(c['annotated_direct_coordination'] for c in coord),
        'firm_owner_claims':0,'unknown_policy':'Every NF may remain unknown, without a penalty or coverage preference.',
        'relative_restoration':'Not integrated or rerun; conditional candidate coverage is not restoration accuracy.',
        'reserved_validation':'200 sentences remain unscored'}
    save(OUT/'report.json',report);save(OUT/'reference-queries.json',queries);save(OUT/'target-audit.json',targets);save(OUT/'coordination-audit.json',coord)
    paths=[Path(__file__),SIXTEEN/'evaluation-truth.json']
    save(OUT/'evaluation-manifest.json',{'inputs':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}})
    for arm in ARMS:print(arm,summary[f'reference_scope/hidden/{arm}'],feasibility[f'reference_scope/hidden/{arm}'])
    print('Coordination pairs:',len(coord),'annotated:',sum(c['annotated_direct_coordination'] for c in coord))
    for t in targets:print(t['stream'],t['requirements'],t['results'])

if __name__=='__main__':run()
