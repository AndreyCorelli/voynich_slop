"""Separate owner evaluation and local-role audit of the oracle ablation."""
from benchmarks.grammar_oracle_morphology_iteration19 import OUT,EIGHTEEN,SEVENTEEN,SIXTEEN,NINE,load,save
from benchmarks.grammar_construction_spans_iteration18_evaluate import evaluate


def evaluate_oracle(rows,baseline,truth):
    wrapped=[]
    for b,r in zip(baseline,rows):
        assert (b['stream'],b['mode'],b['boundaries'])==(r['stream'],r['mode'],r['boundaries'])
        wrapped.append({**r,'parents':{'raw':b['parents']['raw'],**r['model']['parents']}})
    return evaluate(wrapped,truth)


def audit(rows,baseline,models,truth):
    refs={(t['stream'],t['position']):t for t in truth if t['form']=='Inf'}
    index={(m['stream'],m['mode'],m['boundaries']):m['model'] for m in models if m['arm']=='units_open'}
    result=[]
    for b,r in zip(baseline,rows):
        if r['mode']!='reference_scope' or r['boundaries']!='hidden':continue
        if r['stream'] not in (34,49,56,61):continue
        units=index[r['stream'],r['mode'],r['boundaries']]['units']
        for nf,parents in r['model']['parents']['typed'].items():
            ref=refs.get((r['stream'],int(nf)))
            if not ref or ref['owner'] not in b['parents']['raw'].get(nf,[]):continue
            if b['parents']['typed'][nf]==parents and b['parents']['pos'][nf]==r['model']['parents']['pos'][nf]:continue
            evidence=[dict(unit=u['unit'],members=units[u['unit']]['members'],result=u['typed']) for u in r['model']['units'] if int(nf) in units[u['unit']]['members'] and units[u['unit']]['parent']==ref['owner']]
            result.append(dict(stream=r['stream'],position=int(nf),surface=ref['surface'],reference_owner=ref['owner'],
                baseline_typed=b['parents']['typed'][nf],oracle_typed=parents,oracle_pos=r['model']['parents']['pos'][nf],evidence=evidence))
    return result

if __name__=='__main__':
    baseline=load(EIGHTEEN/'predictions.json');truth=load(SIXTEEN/'evaluation-truth.json');rows=load(OUT/'predictions.json')
    result=evaluate_oracle(rows,baseline,truth)
    result['leave_one_out']={k:evaluate_oracle(v,baseline,truth) for k,v in load(OUT/'leave-one-out.json').items()}
    save(OUT/'evaluation.json',result)
    save(OUT/'audit.json',audit(rows,baseline,load(SEVENTEEN/'models.json'),truth))
    print(result['reference_scope/hidden'])
    print('leave-one-out retained:',{k:v['reference_scope/hidden']['typed']['reference_owner_retained'] for k,v in result['leave_one_out'].items()})
