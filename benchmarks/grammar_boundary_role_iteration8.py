"""Frozen-score parent-pool boundary/role oracles; no model fitting."""
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import time
import networkx as nx
import numpy as np
from benchmarks.grammar_training_alignment_iteration7 import OUT as PREVIOUS
from benchmarks.grammar_marker_oracle_iteration6 import score_audit
from benchmarks.grammar_linker_iteration4 import detailed_metrics, summarize
from benchmarks.scalable_latin_caesar import PROIEL
from voynich_smt.predicate_structure import validate_structure
from voynich_smt.marker_structure import validate_markers
from voynich_smt.data.corpus import write_json, digest

OUT=Path('experiments/results/grammar-restoration/iteration8')
CONDITIONS={'unrestricted':(False,False),'boundaries':(True,False),'roles':(False,True),'both':(True,True)}


def region(position,boundaries):
    return next(i for i,b in enumerate(boundaries) if position<b)


def masked_options(prediction,gold,boundaries=False,roles=False):
    result={}
    for child,options in prediction['arc_candidates'].items():
        child=int(child);kind=gold['relations'].get(child,gold['relations'].get(str(child)))
        retained=[deepcopy(r) for r in options if
            (not boundaries or r['parent'] is None or region(child,gold['boundaries'])==region(r['parent'],gold['boundaries'])) and
            (not roles or r['relation']==kind)]
        if not retained:raise ValueError('Oracle restriction left no candidates')
        normalizer=float(np.logaddexp.reduce([r['logit'] for r in retained]))
        for r in retained:r['conditional_probability']=float(np.exp(r['logit']-normalizer))
        result[child]=retained
    return result


def solve_options(prediction,options):
    """Exact maximum directed forest, preserving integer objective/tie scores."""
    result=deepcopy(prediction);graph=nx.DiGraph();graph.add_node(-1)
    for child,rows in options.items():
        for r in rows:
            parent=-1 if r['parent'] is None else r['parent'];weight=round(r['logit']*1e6)
            if not graph.has_edge(parent,child) or graph[parent][child]['weight']<weight:
                graph.add_edge(parent,child,weight=weight,relation=r['relation'])
    tree=nx.maximum_spanning_arborescence(graph,preserve_attrs=True) if options else graph
    assert len(tree.edges)==len(options)
    parents={c:None if p==-1 else p for p,c in tree.edges};relations={c:d['relation'] for _,c,d in tree.edges(data=True)}
    score=sum(d['weight'] for _,_,d in tree.edges(data=True))
    roots=[]
    for p in result['token_anchors']:
        if p is None:roots.append(None);continue
        while parents[p] is not None:p=parents[p]
        roots.append(p)
    result.update(status='optimal',parents=parents,relations=relations,arc_candidates=options,
        forest_score_integer=score,root_groups=roots,
        inferred_boundaries=[i for i in range(1,result['tokens']) if roots[i] is not None and roots[i-1] is not None and roots[i]!=roots[i-1]])
    validate_structure(result);validate_markers(result,None)
    return result


def diagnostic_counts(prediction,gold):
    truth={int(c):p for c,p in gold['parents'].items()};nonroot=[c for c,p in truth.items() if p is not None]
    parents={int(c):p for c,p in prediction['parents'].items()};options=prediction['arc_candidates']
    def candidates(c):return {r['parent'] for r in options.get(c,options.get(str(c),[])) if r['parent'] is not None}
    ambiguous=[c for c in nonroot if len(candidates(c))>1]
    return {'nonroot_total':len(nonroot),'nonroot_correct':sum(parents[c]==truth[c] for c in nonroot),
        'ambiguous_nonroot_total':len(ambiguous),'ambiguous_nonroot_correct':sum(parents[c]==truth[c] for c in ambiguous),
        'cross_sentence_choices':sum(p is not None and region(c,gold['boundaries'])!=region(p,gold['boundaries']) for c,p in parents.items()),
        'correct_typed_forest':all(parents[c]==p and prediction['relations'].get(c,prediction['relations'].get(str(c)))==gold['relations'].get(c,gold['relations'].get(str(c))) for c,p in truth.items())}


def summarize_rows(rows):
    counts={k:sum(r['diagnostic'][k] for r in rows) for k in rows[0]['diagnostic']}
    for prefix in ['nonroot','ambiguous_nonroot']:
        counts[prefix+'_accuracy']=counts[prefix+'_correct']/max(1,counts[prefix+'_total'])
    gaps=[r['audit']['optimum_minus_reference_integer'] for r in rows]
    return {'metrics':summarize([r['metrics'] for r in rows]),'diagnostic':counts,
        'reference_strictly_outscored':sum(g>0 for g in gaps),'reference_tied':sum(g==0 for g in gaps)}


def review_cases(rows,truth):
    cases=[];counts=Counter()
    for row in rows:
        if (row['split'],row['model'],row['condition'])!=('development','gold','both'):continue
        gold=truth[row['split']][row['stream']];author=PROIEL[gold['sentences'][0]['work']]
        for local in row['audit']['per_child']:
            if local['error']=='correct_parent' or counts[author]>=10:continue
            child=local['child'];start=0
            for s,b in zip(gold['sentences'],gold['boundaries']):
                if child<b:sentence=s;end=b;break
                start=b
            candidates=row['prediction']['arc_candidates'][child]
            cases.append({'case':len(cases)+1,'author':author,'split':row['split'],'stream':row['stream'],
                'sent_id':sentence['sent_id'],'sentence_start':start,'sentence_end':end,
                'sentence_text':' '.join(gold['tokens'][start:end]),'child':child,'child_surface':gold['tokens'][child],
                'reference_parent':local['reference_parent'],'reference_surface':gold['tokens'][local['reference_parent']],
                'chosen_parent':local['chosen_parent'],'chosen_surface':gold['tokens'][local['chosen_parent']],
                'relation':local['reference_relation'],'local_audit':local,'candidates':candidates,
                'markers':[m for m in row['prediction']['marker_attachments'] if m['target']==child],
                'sentence_predicates':[{'position':p,'surface':gold['tokens'][p]} for p in gold['finite'] if start<=p<end]})
            counts[author]+=1
    return cases


def run():
    if OUT.exists():raise ValueError('Preserve existing output')
    started=time.monotonic();load=lambda n:json.loads((PREVIOUS/n).read_text())
    truth={s:load(s+'-truth.json') for s in ['development','confirmation']}
    inputs=['models.json','predictions.json','development-truth.json','confirmation-truth.json','morphology-lattice.json','validation.json']
    manifest={'version':1,'scope':'previously inspected source-only oracle diagnostics; frozen weights, predicates, markers and retained logits; no fitting',
        'models':['gold','oof'],'conditions':CONDITIONS,'solver':'exact integer Edmonds; recompute unrestricted baseline',
        'input_sha256':{str(PREVIOUS/n):hashlib.sha256((PREVIOUS/n).read_bytes()).hexdigest() for n in inputs},
        'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    write_json(OUT/'manifest.json',manifest);rows=[];original_abstentions=0
    for base in load('predictions.json'):
        if base['training_markers'] not in ['gold','oof'] or base['evaluation_markers']!='gold':continue
        gold=truth[base['split']][base['stream']];original_abstentions+=base['prediction']['status']!='optimal'
        for condition,(bounds,roles) in CONDITIONS.items():
            prediction=solve_options(base['prediction'],masked_options(base['prediction'],gold,bounds,roles))
            if condition=='unrestricted' and base['prediction']['status']=='optimal':
                assert prediction['forest_score_integer']==base['prediction']['forest_score_integer']
            audit=score_audit(prediction,gold);assert audit['reference_forest_available']
            rows.append({'split':base['split'],'stream':base['stream'],'model':base['training_markers'],'condition':condition,
                'prediction':prediction,'metrics':detailed_metrics(prediction,gold),'audit':audit,'diagnostic':diagnostic_counts(prediction,gold)})
    summaries=[]
    for split in truth:
        for model in ['gold','oof']:
            for condition in CONDITIONS:
                selected=[r for r in rows if (r['split'],r['model'],r['condition'])==(split,model,condition)]
                summaries.append({'split':split,'model':model,'condition':condition,**summarize_rows(selected)})
    write_json(OUT/'predictions.json',rows);write_json(OUT/'review-cases.json',review_cases(rows,truth))
    report={'manifest_sha256':digest(manifest),'summary':summaries,'conditions':len(rows),
        'original_baseline_abstentions':original_abstentions,'new_solver_abstentions':0,
        'elapsed_seconds':time.monotonic()-started,'limitations':['previously inspected same-author passages','gold role oracle reveals ROOT identity',
            'gold role/boundary masks can make parent choices trivial','no model fitting or lexical restoration']}
    write_json(OUT/'report.json',report)
    for s in summaries:
        if s['split']=='confirmation':print(s['model'],s['condition'],'edge',round(s['metrics']['edges']['f1'],4),
            'nonroot',round(s['diagnostic']['nonroot_accuracy'],4),'ambiguous',s['diagnostic']['ambiguous_nonroot_correct'],'/',s['diagnostic']['ambiguous_nonroot_total'],
            'wrong refs',s['reference_strictly_outscored'],flush=True)


if __name__=='__main__':run()
