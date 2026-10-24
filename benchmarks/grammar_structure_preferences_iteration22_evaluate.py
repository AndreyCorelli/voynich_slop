"""Separate oracle audits of tie-preserving, label-free candidate preferences."""
from collections import Counter
import json
import z3
from benchmarks.grammar_structure_preferences_iteration22 import OUT,TWENTYONE,SEVENTEEN,NINE,SIXTEEN,load,save
from benchmarks.grammar_argument_structures_iteration20_evaluate import source_nodes
from benchmarks.grammar_participial_structures_iteration21_evaluate import reference_edges,source_match
from voynich_smt.structure_preferences import POLICIES,FAMILIES,select,collisions


def collapse_unmarked(edges,clauses):
    result=set(map(tuple,edges))
    for subject,part in clauses:
        if (subject,part) not in result:continue
        targets=[b for a,b in result if a==part]
        if not targets:continue
        result.discard((subject,part))
        for target in targets:result.discard((part,target));result.add((subject,target))
    return sorted(result)


def equivalence_matches(nodes,unit,result):
    expected=reference_edges(nodes,unit,result['start'],result['end'])
    reference_clauses=[]
    for subject,part in expected:
        if nodes[subject]['upos'] not in ('NOUN','PRON') or nodes[part]['features'].get('VerbForm')!='Part':continue
        if any(nodes[p]['word']=='nisi' and nodes[p]['head']==part for p in range(result['start'],result['end'])):continue
        reference_clauses.append((subject,part))
    target=collapse_unmarked(expected,reference_clauses);labels=[]
    for structure in result['structures']:
        clauses=[(s['clause']['subject'],s['clause']['participle']) for s in structure['witness'] if 'clause' in s and s['clause']['marker'] is None]
        actual=collapse_unmarked([(a,b) for a,b,r in structure['links']],clauses)
        # Sensitivity analysis only: a first-conjunct UD object annotation may
        # leave sharing unspecified. Retain first-only and shared alternatives;
        # do not forgive second-only attachment or arbitrary object movement.
        if len(unit['members'])==2:
            shared={h for g in structure['groups'] if g['role']=='object' and set(g['targets'])==set(unit['members']) for h in g['heads']}
            actual=[(h,t) for h,t in actual if not (h in shared and t==unit['members'][1])]
        labels.append(actual==target and source_match(nodes,structure))
    return labels


def feasibility(cases,names,nonpositive_distance=False):
    weights={n:z3.Real(n) for n in names};solver=z3.Solver()
    if nonpositive_distance:solver.add(weights['dependency_distance']<=0)
    dot=lambda v:sum(weights[n]*v[n] for n in names)
    for case in cases:
        vectors=case['features'];labels=case['strict_labels'];positive=[i for i,good in enumerate(labels) if good];negative=[i for i,good in enumerate(labels) if not good]
        solver.add(z3.Or([z3.And([dot(vectors[i])>dot(vectors[j]) for j in negative]) for i in positive]))
    status=solver.check()
    result={'status':str(status),'cases':len(cases),'collision_cases':[c['id'] for c in cases if collisions(c['features'],c['strict_labels'],names)]}
    if status==z3.sat:
        model=solver.model();result['witness_weights']={n:str(model.eval(w,model_completion=True)) for n,w in weights.items()}
    return result


def assess(selected,labels):
    return dict(selected=selected,unique=len(selected)==1,reference_available=any(labels[i] for i in selected),
        all_selected_match=bool(selected) and all(labels[i] for i in selected),unique_correct=len(selected)==1 and labels[selected[0]])


def perception_convention_audit(rows,models,dev):
    """Sensitivity only: UD matrix object versus modeled embedded ACI subject.

    This permits a substantivized ADJ to correspond to a dictionary noun, while
    retaining source case/number/gender. It is never used to rank candidates.
    """
    source=source_nodes(dev)
    idx={(r['stream'],r['mode'],r['boundaries']):r['model'] for r in models if r['arm']=='units_open'}
    audits=[]
    for row in rows:
        if (row['morphology'],row['arm'],row['mode'],row['boundaries'])!=('oracle_missing','participles_nisi','reference_scope','hidden'):continue
        for entry in row['result']['units']:
            r=entry['result']
            if r['status']!='supported':continue
            unit=idx[row['stream'],row['mode'],row['boundaries']]['units'][entry['unit']]
            if unit['kind']!='perception_aci':continue
            nodes=[dict(n) for n in source[row['stream']]]
            expected=reference_edges(nodes,unit,r['start'],r['end']);rewrites=[]
            for part in unit['parts']:
                h=part.get('embedded_subject');nf=part['nonfinite']
                if h is not None and nodes[h]['upos']=='ADJ' and nodes[h]['relation']=='obj' and nodes[h]['head']==unit['parent'] and nodes[nf]['head']==unit['parent']:
                    rewrites.append(dict(position=h,source_head=unit['parent'],modeled_head=nf,source_upos='ADJ',modeled_pos='N'))
                    nodes[h]['upos']='NOUN'
                    expected=[[a,nf if a==h and b==unit['parent'] else b] for a,b in expected]
                    if not any(a==h for a,b in expected):expected.append([h,nf])
            if not rewrites:continue
            strict=[];relaxed=[]
            for s in r['structures']:
                links=sorted({(a,b) for a,b,role in s['links']})
                original=reference_edges(source[row['stream']],unit,r['start'],r['end'])
                strict.append(links==list(map(tuple,original)) and source_match(source[row['stream']],s))
                relaxed.append(links==sorted(map(tuple,expected)) and source_match(nodes,s))
            audits.append(dict(stream=row['stream'],unit=entry['unit'],members=unit['members'],parent=unit['parent'],rewrites=rewrites,strict_labels=strict,relaxed_labels=relaxed))
    return audits


def evaluate(predictions,rows,models,dev):
    source=source_nodes(dev)
    ridx={(r['stream'],r['mode'],r['boundaries'],r['morphology']):r for r in rows if r['arm']=='participles_nisi'}
    midx={(r['stream'],r['mode'],r['boundaries']):r['model'] for r in models if r['arm']=='units_open'}
    cases=[];seen={};duplicates=0
    for record in predictions:
        stream=record['stream'];row=ridx[stream,'reference_scope','hidden',record['morphology']]
        entry=next(u for u in row['result']['units'] if u['unit']==record['unit']);result=entry['result'];unit=midx[stream,'reference_scope','hidden']['units'][record['unit']]
        expected=reference_edges(source[stream],unit,result['start'],result['end'])
        pos=[source_match(source[stream],s) for s in result['structures']]
        labels=[sorted({(h,t) for h,t,role in s['links']})==list(map(tuple,expected)) and p for s,p in zip(result['structures'],pos)]
        equivalent=equivalence_matches(source[stream],unit,result)
        key=(record['morphology'],stream,record['start'],record['end'],tuple(record['members']),record['parent'])
        if key in seen:
            assert seen[key]==(record['features'],labels,equivalent,pos,record['selected']);duplicates+=1;continue
        seen[key]=(record['features'],labels,equivalent,pos,record['selected'])
        case=dict(**record,id=f"{stream}:{','.join(map(str,record['members']))}->{record['parent']}",
            text=' '.join(dev[stream]['tokens'][record['start']:record['end']]),strict_labels=labels,equivalent_labels=equivalent,source_reading_labels=pos,
            reference_available=any(labels),ambiguous=len(labels)>1,
            policies={policy:{'strict':assess(record['selected'][policy],labels),'equivalent':assess(record['selected'][policy],equivalent)} for policy in POLICIES},
            feature_collisions={family:collisions(record['features'],labels,names) for family,names in FAMILIES.items()})
        eligible=[i for i,good in enumerate(pos) if good]
        case['oracle_readings']={}
        for policy in POLICIES:
            chosen=[eligible[i] for i in select([record['features'][i] for i in eligible],policy)]
            case['oracle_readings'][policy]=assess(chosen,labels)
        cases.append(case)
    summaries={};solvers={}
    for morphology in ('dictionary','oracle_missing'):
        cohort=[c for c in cases if c['morphology']==morphology and c['ambiguous'] and c['reference_available']]
        report=dict(distinct_supported_units=sum(c['morphology']==morphology for c in cases),ambiguous_selectable_cases=len(cohort),
            ambiguous_without_reference=[c['id'] for c in cases if c['morphology']==morphology and c['ambiguous'] and not c['reference_available']],policies={},oracle_reading_policies={})
        for policy in POLICIES:
            for oracle,target in ((False,report['policies']),(True,report['oracle_reading_policies'])):
                count=Counter()
                for c in cohort:
                    a=c['oracle_readings'][policy] if oracle else c['policies'][policy]['strict']
                    count['cases']+=1
                    for k in ('unique','reference_available','all_selected_match','unique_correct'):count[k]+=a[k]
                    count['unique_wrong']+=a['unique'] and not a['unique_correct']
                    count['retained_candidates']+=len(a['selected'])
                target[policy]=dict(count)
        summaries[morphology]=report
        solvers[morphology]={name:feasibility(cohort,names) for name,names in FAMILIES.items()}
        solvers[morphology]['frame_distance_nonpositive']=feasibility(cohort,FAMILIES['frame_distance'],nonpositive_distance=True)
    return dict(summary=summaries,feature_family_feasibility=solvers,deduplicated_unit_readings=duplicates,cases=cases,annotation_convention_audit=perception_convention_audit(rows,models,dev))

if __name__=='__main__':
    result=evaluate(load(OUT/'predictions.json'),load(TWENTYONE/'predictions.json'),load(SEVENTEEN/'models.json'),load(NINE/'development-truth.json'))
    save(OUT/'evaluation.json',result)
    print(json.dumps(result['summary'],indent=2));print(json.dumps(result['feature_family_feasibility'],indent=2))
