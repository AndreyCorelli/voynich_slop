"""Evaluation-only ownership targets and construction metrics."""
from collections import Counter
from benchmarks.scalable_latin_caesar import words
import hashlib
from pathlib import Path
from benchmarks.grammar_nonfinite_ownership_iteration16 import OUT,NINE,FIFTEEN,ARMS,load,save
from benchmarks.grammar_relative_constituents_iteration15 import signature
from benchmarks.grammar_relative_constituents_iteration15_evaluate import reference_paths,TREEBANK


def ownership_truth(dev):
    wanted={s['sent_id'] for stream in dev for s in stream['sentences']};raw={}
    for block in TREEBANK.read_text().split('\n\n'):
        sid=next((l.split(' = ',1)[1] for l in block.splitlines() if l.startswith('# sent_id = ')),None)
        if sid not in wanted:continue
        rows=[l.split('\t') for l in block.splitlines() if l and not l.startswith('#') and l.split('\t')[0].isdigit() and l.split('\t')[3]!='PUNCT']
        positions={r[0]:i for i,r in enumerate(rows)}
        raw[sid]=[dict(surface=r[1],upos=r[3],features=dict(x.split('=',1) for x in r[5].split('|') if '=' in x),head=positions.get(r[6]),relation=r[7]) for r in rows]
    metadata=load(NINE/'sentence-complexes.json')['development']
    complexes={s['sent_id']:{c['head']:c['representative'] for c in s['predicate_complexes']} for s in metadata};truth=[]
    for i,s in enumerate(dev):
        offset=0
        for info,end in zip(s['sentences'],s['boundaries']):
            sid=info['sent_id'];nodes=raw[sid];mapping=complexes[sid]
            assert [words(n['surface'])[0] for n in nodes]==s['tokens'][offset:end]
            for pos,n in enumerate(nodes):
                if n['upos'] not in ('VERB','AUX') or n['features'].get('VerbForm') not in ('Inf','Part'):continue
                path=[];node=pos;seen=set();owner=None
                while node is not None and node not in seen:
                    seen.add(node);path.append(dict(position=node+offset,**nodes[node]))
                    representative=mapping.get(node,node if node+offset in s['finite'] else None)
                    if representative is not None:
                        owner=representative+offset;break
                    node=nodes[node]['head']
                assert pos+offset not in s['finite']
                truth.append(dict(stream=i,sent_id=sid,position=pos+offset,surface=s['tokens'][pos+offset],form=n['features']['VerbForm'],
                    owner=owner,path=path,features=n['features']))
            offset=end
    return truth


def ownership_metrics(rows,truth,*,nearest=False):
    lookup={(t['stream'],t['position']):t for t in truth};counts=Counter()
    streams={r['stream'] for r in rows}
    references=[t for t in truth if t['stream'] in streams]
    for r in rows:
        for rec in r['ownership']['records']:
            ref=lookup.get((r['stream'],rec['position']));counts['morphological_proposals']+=1
            counts['reference_proposals']+=ref is not None
            counts['spurious_proposals']+=ref is None
            parents=rec['nearest_parents'] if nearest else rec['possible_parents']
            resolved=(len(parents)==1 and not rec['selection_optional']) if nearest else rec['status']=='unique'
            counts['conditional_unique_owner']+=len(parents)==1
            counts['conditional_correct_owner']+=bool(len(parents)==1 and ref and ref['owner']==parents[0])
            counts['unique_selected_owner']+=resolved
            counts['correct_selected_owner']+=bool(resolved and ref and ref['owner']==parents[0])
            counts['reference_owner_reachable']+=bool(ref and ref['owner'] in parents)
            counts['reference_owner_in_lexical_pool']+=bool(ref and ref['owner'] in rec['candidate_parents'])
            counts['selected_spurious_owner']+=bool(resolved and ref is None)
            counts[f"status_{rec['status'] if not nearest else 'nearest'}"]+=1
    counts['reference_nonfinite']=len(references);counts['reference_with_finite_owner']=sum(t['owner'] is not None for t in references)
    obj=dict(counts)
    obj['selected_precision']=counts['correct_selected_owner']/counts['unique_selected_owner'] if counts['unique_selected_owner'] else None
    obj['correct_coverage']=counts['correct_selected_owner']/len(references) if references else None
    return obj


def relative_metrics(rows,truth):
    counts=Counter()
    for r in rows:
        result=r['result'];sig=signature(result);ref=truth.get((r['stream'],r['marker']));valid=r['scope_correct'] and ref is not None
        target=tuple(ref['target_chain']) if ref and ref['target_chain'] is not None else None
        resolved=all(w.get('ownership')!='ambiguous' for w in result['chains'])
        counts['cases']+=1;counts[f"status_{result['status']}"]+=1
        if len(result['antecedents'])==1:
            counts['unique_antecedent']+=1
            counts['antecedent_correct']+=bool(valid and result['antecedents']==[ref['annotated_nominal']])
        if len(result['parents'])==1 and resolved:
            counts['unique_parent']+=1
            correct=bool(valid and result['parents']==[ref['parent']]);counts['parent_correct']+=correct
            baseline=bool(valid and r['baseline_parent']==ref['parent']);counts['baseline_parent_correct_on_claims']+=baseline
            counts['parent_corrections']+=bool(correct and not baseline);counts['parent_regressions']+=bool(baseline and not correct)
        if len(sig)==1 and resolved:
            counts['unique_chain']+=1
            correct=bool(valid and target is not None and sig[0]==target);counts['chain_correct']+=correct
            counts['nonfinite_chain_claims']+=sig[0][1] is not None
            counts['nonfinite_chain_correct']+=bool(correct and target[1] is not None)
        counts['chain_reachable']+=bool(valid and target is not None and target in sig)
        counts['ownership_ambiguity_cases']+=not resolved
    obj=dict(counts)
    for label in ('parent','antecedent','chain'):
        obj[f'{label}_precision']=counts[f'{label}_correct']/counts[f'unique_{label}'] if counts[f'unique_{label}'] else None
    return obj


def run():
    dev=load(NINE/'development-truth.json');truth=ownership_truth(dev);rtruth=reference_paths(dev)
    owners=load(OUT/'ownership.json');rows=load(OUT/'predictions.json')
    osummary={};rsummary={}
    for mode in ('reference_scope','predicted_scope'):
        for bounds in ('hidden','reference'):
            for arm in (*ARMS,'nearest'):
                selected=[r for r in owners if (r['mode'],r['boundaries'],r['arm'])==(mode,bounds,'independent' if arm=='nearest' else arm)]
                osummary[f'{mode}/{bounds}/{arm}']=ownership_metrics(selected,truth,nearest=arm=='nearest')
            for arm in ('original',*ARMS,'nearest'):
                rsummary[f'{mode}/{bounds}/{arm}']=relative_metrics([r for r in rows if (r['mode'],r['boundaries'],r['arm'])==(mode,bounds,arm)],rtruth)
    report={'scope':'Reused development; finite positions supplied; annotated ownership is nearest projected finite ancestor, not expert adjudication.',
        'controlled_probes':len(load(OUT/'controlled.json')),'annotated_nonfinite':len(truth),'reference_relative_cases':len(rtruth),
        'ownership':osummary,'relative':rsummary,
        'limitations':['simple one-INF frame; coordinated infinitives can force component abstention',
            'noncrossing and minimal marker intervals are bounded structural assumptions',
            'active INF and nominative active participles only; optional lexical selection for participles/homographs',
            'relative candidate pools frozen; reporting complexes license ownership but do not introduce new relative candidates',
            'no fresh confirmation, full parse, dictionary optimization or scorer integration'],
        'heldout':'200 reserved sentences remain unscored'}
    audit=[]
    for nf in truth:
        if nf['surface'] not in ('fecundare','locare','habens'):continue
        s=dev[nf['stream']]
        record={**nf,'text':' '.join(s['tokens']),'conditions':{}}
        for row in owners:
            if row['stream']==nf['stream'] and row['mode']=='reference_scope' and row['boundaries']=='hidden':
                record['conditions'][row['arm']]=next((r for r in row['ownership']['records'] if r['position']==nf['position']),None)
        audit.append(record)
    save(OUT/'evaluation-truth.json',truth);save(OUT/'report.json',report);save(OUT/'construction-audit.json',audit)
    inputs=[TREEBANK,NINE/'sentence-complexes.json',Path(__file__),Path('benchmarks/grammar_relative_constituents_iteration15_evaluate.py')]
    save(OUT/'evaluation-manifest.json',{'inputs':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}})
    print(f'{len(truth)} annotated nonfinite predicates')
    for label,summary in [('OWNERSHIP',osummary),('RELATIVE',rsummary)]:
        print(label)
        for key,v in summary.items():
            if '/hidden/' in key:
                fields=('unique_selected_owner','correct_selected_owner','reference_owner_reachable','conditional_unique_owner','conditional_correct_owner') if label=='OWNERSHIP' else ('unique_chain','chain_correct','nonfinite_chain_claims','nonfinite_chain_correct')
                print(key,{k:v.get(k,0) for k in fields})

if __name__=='__main__':run()
