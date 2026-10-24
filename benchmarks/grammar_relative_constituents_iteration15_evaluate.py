"""Evaluation only: annotated nominal identity and intervening verb path.

UD paths are a reproducible proxy, not expert-adjudicated antecedent truth.
This file is not imported by the inference module or prediction runner.
"""
from collections import Counter
import hashlib
from pathlib import Path
from benchmarks.grammar_relative_constituents_iteration15 import OUT,NINE,FOURTEEN,ARMS,load,save,signature

TREEBANK=Path('data/latin-grammar-benchmark/proiel-r2.17/la_proiel-ud-train.conllu')


def reference_paths(dev):
    metadata=load(NINE/'sentence-complexes.json')['development']
    wanted={s['sent_id'] for stream in dev for s in stream['sentences']};raw={}
    for block in TREEBANK.read_text().split('\n\n'):
        sid=next((l.split(' = ',1)[1] for l in block.splitlines() if l.startswith('# sent_id = ')),None)
        if sid not in wanted:continue
        rows=[l.split('\t') for l in block.splitlines() if l and not l.startswith('#') and l.split('\t')[0].isdigit() and l.split('\t')[3]!='PUNCT']
        positions={r[0]:i for i,r in enumerate(rows)}
        raw[sid]=[dict(surface=r[1],upos=r[3],head=positions.get(r[6]),relation=r[7]) for r in rows]
    complexes={s['sent_id']:{c['representative']:c['head'] for c in s['predicate_complexes']} for s in metadata}
    truth={}
    for i,s in enumerate(dev):
        for m,v in s['markers'].items():
            if v['kind']!='relative':continue
            child=v['target'];parent=s['parents'][str(child)];offset=0
            for info,end in zip(s['sentences'],s['boundaries']):
                if child<end:break
                offset=end
            sid=info['sent_id'];nodes=raw[sid];mapping=complexes[sid]
            head=mapping.get(child-offset,child-offset)
            stop=mapping.get(parent-offset,parent-offset) if parent is not None else None
            node=nodes[head]['head'];path=[];seen=set()
            while node is not None and node!=stop and node not in seen:
                seen.add(node);path.append(dict(position=node+offset,**nodes[node]));node=nodes[node]['head']
            nominal=next((n for n in path if n['upos'] in ('NOUN','PROPN','PRON','ADJ','NUM')),None)
            following=path[path.index(nominal)+1:] if nominal else []
            verbs=[n['position'] for n in following if n['upos'] in ('VERB','AUX') and n['position'] not in s['finite']]
            target=(nominal['position'],verbs[0] if verbs else None,parent) if nominal and parent is not None and len(verbs)<=1 else None
            truth[i,int(m)]=dict(stream=i,marker=int(m),child=child,parent=parent,sent_id=sid,
                annotated_nominal=nominal['position'] if nominal else None,nonfinite_path=verbs,
                target_chain=target,annotation_path=path,text=' '.join(s['tokens']))
    return truth


def metrics(rows,truth):
    counts=Counter();transitions=Counter()
    for r in rows:
        ref=truth.get((r['stream'],r['marker']));result=r['result'];chains=signature(result)
        valid=r['scope_correct'] and ref is not None
        target=tuple(ref['target_chain']) if ref and ref['target_chain'] is not None else None
        head=ref['annotated_nominal'] if ref else None
        counts['cases']+=1;counts['scope_correct']+=valid
        counts[f"status_{result['status']}"]+=1
        if len(result['parents'])==1:
            counts['unique_parent']+=1
            correct=bool(valid and result['parents']==[ref['parent']])
            counts['parent_correct']+=correct
            baseline=bool(valid and r['baseline_parent']==ref['parent'])
            counts['baseline_parent_correct_on_claims']+=baseline
            transitions['parent_corrections']+=bool(correct and not baseline)
            transitions['parent_regressions']+=bool(baseline and not correct)
        if len(result['antecedents'])==1:
            counts['unique_antecedent']+=1
            counts['antecedent_correct']+=bool(valid and head is not None and result['antecedents']==[head])
        if len(chains)==1:
            counts['unique_chain']+=1
            correct=bool(valid and target is not None and chains[0]==target)
            counts['chain_correct']+=correct
            counts['nonfinite_chain_claims']+=chains[0][1] is not None
            counts['nonfinite_chain_correct']+=bool(correct and target[1] is not None)
        counts['antecedent_reachable']+=bool(valid and head is not None and head in result['antecedents'])
        counts['chain_reachable']+=bool(valid and target is not None and target in chains)
    obj=dict(counts);obj.update(transitions)
    for label in ('parent','antecedent','chain'):
        obj[f'{label}_precision']=counts[f'{label}_correct']/counts[f'unique_{label}'] if counts[f'unique_{label}'] else None
    return obj


def run():
    dev=load(NINE/'development-truth.json');rows=load(OUT/'predictions.json');truth=reference_paths(dev)
    summary={f'{mode}/{bounds}/{arm}':metrics([r for r in rows if (r['mode'],r['boundaries'],r['arm'])==(mode,bounds,arm)],truth)
        for mode in ('reference_scope','predicted_scope') for bounds in ('hidden','reference') for arm in ARMS}
    audit=[]
    for (i,marker),ref in truth.items():
        s=dev[i];record={**ref,'arms':{}}
        for arm in ARMS:
            r=next(r for r in rows if (r['stream'],r['marker'],r['mode'],r['boundaries'],r['arm'])==(i,marker,'reference_scope','hidden',arm))
            record['arms'][arm]={'status':r['result']['status'],'candidate_chains':signature(r['result']),
                'surfaces':[[s['tokens'][h],s['tokens'][v] if v is not None else None,s['tokens'][p]] for h,v,p in signature(r['result'])]}
        audit.append(record)
    report={'scope':'Inspected development only; finite positions supplied; path identity is an annotation proxy, not expert adjudication.',
        'controlled_passed':len(load(OUT/'controlled.json')),
        'reference_cases':len(truth),'reference_with_nominal':sum(t['annotated_nominal'] is not None for t in truth.values()),
        'reference_nominal_plus_nonfinite':sum(bool(t['nonfinite_path']) for t in truth.values()),
        'reference_representable_path_shape':sum(t['target_chain'] is not None for t in truth.values()),
        'summary':summary,'previous_iteration_parent_metrics':load(FOURTEEN/'report.json')['natural'],
        'limitations':['flat bounded NP grammar; no complete clause parse','no missing-word morphology repair',
            'no free-relative or arbitrary coordination analysis','active nominative participle requires an explicit compatible subject',
            'modal inventory deb/poss; optional declared object frames hab/loc','supplied finite positions and optional scope/boundary oracles',
            'larger radius and consistency corrections mean readings_direct is a new control, not an exact iteration14 replay'],
        'reserved_validation':'200 sentences remain unscored'}
    save(OUT/'evaluation-truth.json',list(truth.values()));save(OUT/'construction-audit.json',audit);save(OUT/'report.json',report)
    inputs=[TREEBANK,NINE/'sentence-complexes.json',FOURTEEN/'report.json',Path(__file__)]
    save(OUT/'evaluation-manifest.json',{'inputs':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}})
    print({k:v for k,v in report.items() if k not in ('summary','previous_iteration_parent_metrics')})
    for k,v in summary.items():
        if '/hidden/' in k:print(k, {n:v.get(n,0) for n in ('unique_parent','parent_correct','unique_antecedent','antecedent_correct','unique_chain','chain_correct','chain_reachable','nonfinite_chain_claims','nonfinite_chain_correct')})

if __name__=='__main__':run()
