"""Evaluate saved fragment support against separately loaded reference owners."""
from collections import Counter
from benchmarks.grammar_construction_spans_iteration18 import OUT,SIXTEEN,load,save


def evaluate(rows,truth):
    groups={}
    refs={(r['stream'],str(r['position'])):r['owner'] for r in truth if r['form']=='Inf'}
    for row in rows:
        key=f"{row['mode']}/{row['boundaries']}"
        group=groups.setdefault(key,{arm:Counter() for arm in row['parents']})
        for arm,parents in row['parents'].items():
            c=group[arm];c['reference_infinitives']+=sum(s==row['stream'] for s,n in refs)
            for nf,values in parents.items():
                c['candidate_edges']+=len(values);c['nonempty_fragments']+=bool(values)
                owner=refs.get((row['stream'],nf))
                if (row['stream'],nf) not in refs:continue
                c['reference_owner_retained']+=owner in values
                c['unique_fragments']+=len(values)==1
                c['unique_correct']+=len(values)==1 and values[0]==owner
                raw=row['parents']['raw'][nf]
                if owner in raw and len(raw)>1:
                    c['ambiguous_reference_cases']+=1
                    c['ambiguous_true_retained']+=owner in values
                    c['ambiguous_resolved_correctly']+=values==[owner]
                    c['ambiguous_true_rejected']+=owner not in values
    return {key:{arm:dict(c) for arm,c in arms.items()} for key,arms in groups.items()}

if __name__=='__main__':
    rows=load(OUT/'predictions.json');save(OUT/'evaluation.json',evaluate(rows,load(SIXTEEN/'evaluation-truth.json')))
    print(evaluate(rows,load(SIXTEEN/'evaluation-truth.json'))['reference_scope/hidden'])
