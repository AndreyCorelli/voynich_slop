"""Validate masks, frozen logits, exact forests and independent Z3 witnesses."""
from collections import Counter
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
from unittest.mock import patch
import numpy as np
import z3
from benchmarks.grammar_boundary_role_iteration8 import OUT,PREVIOUS,CONDITIONS,region,summarize_rows,diagnostic_counts,review_cases
from benchmarks.grammar_training_alignment_iteration7 import FixedMarkers
from benchmarks.grammar_marker_oracle_iteration6 import score_audit
from benchmarks.grammar_structure_iteration3_validate import FrozenAdapter
from benchmarks.grammar_linker_iteration4 import detailed_metrics
from benchmarks.grammar_markers_iteration5 import TREEBANKS
from voynich_smt.parent_ranking import ConditionalRanker,choices
from voynich_smt.marker_structure import infer_attached_links,attachment_features,validate_markers
from voynich_smt.predicate_structure import morph_features,validate_structure
from voynich_smt.data.corpus import digest,write_json


def run():
    load=lambda p:json.loads(p.read_text());manifest=load(OUT/'manifest.json');report=load(OUT/'report.json')
    assert digest(manifest)==report['manifest_sha256']
    assert hashlib.sha256(Path('benchmarks/grammar_boundary_role_iteration8.py').read_bytes()).hexdigest()==manifest['code_sha256']
    for p,h in manifest['input_sha256'].items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h
    old_validation=load(PREVIOUS/'validation.json');assert old_validation['validated']
    for name,h in old_validation['artifact_sha256'].items():assert hashlib.sha256((PREVIOUS/name).read_bytes()).hexdigest()==h
    truth={s:load(PREVIOUS/(s+'-truth.json')) for s in ['development','confirmation']}
    bases={(r['split'],r['stream'],r['training_markers']):r for r in load(PREVIOUS/'predictions.json')
        if r['training_markers'] in ['gold','oof'] and r['evaluation_markers']=='gold'}
    adapter=FrozenAdapter(load(PREVIOUS/'morphology-lattice.json'));raw=load(PREVIOUS/'models.json')
    models={n:ConditionalRanker(**raw['parents'][n]) for n in ['gold','oof']}
    # Recompute full candidate features/logits directly from frozen weights.
    for identity,base in bases.items():
        gold=truth[identity[0]][identity[1]];morph=[morph_features(adapter.analyze(w)) for w in gold['tokens']]
        for child in gold['finite']:
            expected=choices(gold['tokens'],child,gold['finite'],morph,typed=True,radius=None)
            features=[attachment_features(gold['tokens'],child,r['parent'],gold['finite'],morph,r['relation'],base['prediction']['marker_attachments'],False) for r in expected]
            logits=models[identity[2]].logits(features);saved=base['prediction']['arc_candidates'][str(child)]
            assert [(r['parent'],r['relation']) for r in expected]==[(r['parent'],r['relation']) for r in saved]
            assert np.allclose(logits,[r['logit'] for r in saved],rtol=0,atol=1e-10)
    rows=load(OUT/'predictions.json');index={};gaps={};rechecked=0
    for row in rows:
        identity=(row['split'],row['stream'],row['model']);key=identity+(row['condition'],)
        assert key not in index;index[key]=row
        base=bases[identity]['prediction'];gold=truth[row['split']][row['stream']];pred=row['prediction']
        bounds,roles=CONDITIONS[row['condition']];validate_structure(pred);validate_markers(pred,None)
        assert pred['predicates']==gold['finite'] and pred['marker_attachments']==base['marker_attachments']
        assert pred['token_anchors']==base['token_anchors']
        total=0;reference=0
        for child in gold['finite']:
            kind=gold['relations'][str(child)]
            expected=[r for r in base['arc_candidates'][str(child)] if
                (not bounds or r['parent'] is None or region(child,gold['boundaries'])==region(r['parent'],gold['boundaries'])) and
                (not roles or r['relation']==kind)]
            options=pred['arc_candidates'][str(child)]
            assert [(r['parent'],r['relation'],r['logit']) for r in expected]==[(r['parent'],r['relation'],r['logit']) for r in options]
            assert math.isclose(sum(r['conditional_probability'] for r in options),1,abs_tol=1e-10)
            normalizer=float(np.logaddexp.reduce([r['logit'] for r in expected]))
            for r in options:assert math.isclose(r['conditional_probability'],math.exp(r['logit']-normalizer),abs_tol=1e-12)
            parent=pred['parents'][str(child)];relation=pred['relations'][str(child)]
            total+=round(next(r['logit'] for r in options if (r['parent'],r['relation'])==(parent,relation))*1e6)
            reference+=round(next(r['logit'] for r in options if (r['parent'],r['relation'])==(gold['parents'][str(child)],kind))*1e6)
        assert total==pred['forest_score_integer']
        assert reference==row['audit']['reference_score_integer']
        assert score_audit(pred,gold)==row['audit']
        assert detailed_metrics(pred,gold)==row['metrics']
        assert diagnostic_counts(pred,gold)==row['diagnostic']
        gaps[key]=total-reference
        if row['condition']=='unrestricted' and base['status']=='optimal':
            assert pred['forest_score_integer']==base['forest_score_integer'];rechecked+=1
    for identity in bases:
        g=lambda mode:gaps[identity+(mode,)]
        assert 0<=g('both')<=g('boundaries')<=g('unrestricted')
        assert g('both')<=g('roles')<=g('unrestricted')
    assert len(rows)==report['conditions']==len(bases)*4==1056
    for s in report['summary']:
        rr=[r for r in rows if all(r[k]==s[k] for k in ['split','model','condition'])]
        assert {k:v for k,v in s.items() if k not in ['split','model','condition']}==summarize_rows(rr)
    assert sum(b['prediction']['status']!='optimal' for b in bases.values())==report['original_baseline_abstentions']
    cases=load(OUT/'review-cases.json');in_memory=deepcopy(rows)
    for r in in_memory:r['prediction']['arc_candidates']={int(c):v for c,v in r['prediction']['arc_candidates'].items()}
    assert cases==json.loads(json.dumps(review_cases(in_memory,truth)))
    review=load(OUT/'review.json');assert review['reviewed']==len(cases)==17
    assert hashlib.sha256(Path('benchmarks/grammar_boundary_role_iteration8_review.py').read_bytes()).hexdigest()==review['code_sha256']
    assert hashlib.sha256((TREEBANKS/'proiel-r2.17/la_proiel-ud-train.conllu').read_bytes()).hexdigest()==review['source_sha256']
    assert [c['case'] for c in review['cases']]==[c['case'] for c in cases]
    assert all(c['reference_derivation_verified'] for c in review['cases'])
    # Independent direct Z3 optimization for each unique reviewed stream, all four masks.
    selected=sorted({(c['split'],c['stream']) for c in cases});z3_count=0
    for split,stream in selected:
        gold=truth[split][stream];base=bases[split,stream,'gold']['prediction']
        for mode in CONDITIONS:
            row=index[split,stream,'gold',mode];pred=row['prediction']
            allowed={int(c):{(r['parent'],r['relation']) for r in rr} for c,rr in pred['arc_candidates'].items()}
            def restricted(tokens,child,predicates,morph,**kwargs):
                return [r for r in choices(tokens,child,predicates,morph,**kwargs) if (r['parent'],r['relation']) in allowed[child]]
            with patch('voynich_smt.parent_ranking.choices',restricted):
                actual=infer_attached_links(gold['tokens'],gold['finite'],adapter,models['gold'],FixedMarkers(base['marker_attachments']),timeout_ms=10000)
            assert actual['status']=='optimal', (split,stream,mode,'Z3 unresolved')
            assert actual['forest_score_integer']==pred['forest_score_integer'];z3_count+=1
    intervals=[]
    rng=np.random.default_rng(1729)
    for model in ['gold','oof']:
        base=[r for r in rows if (r['split'],r['model'],r['condition'])==('confirmation',model,'unrestricted')]
        draws=rng.integers(0,len(base),(2000,len(base)))
        for mode in ['boundaries','roles','both']:
            other=[r for r in rows if (r['split'],r['model'],r['condition'])==('confirmation',model,mode)]
            assert [r['stream'] for r in base]==[r['stream'] for r in other]
            counts=lambda rr:np.array([[r['metrics']['edges'][k] for k in ['tp','predicted','gold']] for r in rr])
            a,b=counts(base),counts(other);f=lambda x:2*x[...,0]/np.maximum(1,x[...,1]+x[...,2])
            delta=f(b[draws].sum(axis=1))-f(a[draws].sum(axis=1))
            intervals.append({'model':model,'condition':mode,'edge_f1_difference':float(f(b.sum(axis=0))-f(a.sum(axis=0))),
                'percentile_95_interval':np.quantile(delta,[.025,.975]).tolist(),'draws':2000,'seed':1729,
                'scope':'paired source streams; already inspected; not new-author generalization'})
    validation={'validated':True,'conditions':len(rows),'original_completed_optima_rechecked':rechecked,
        'newly_completed_baselines':report['original_baseline_abstentions'],'independent_Z3_conditions':z3_count,
        'reviewed_residuals':len(cases),'paired_intervals':intervals,'report_sha256':digest(report),
        'validator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'artifact_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.glob('*.json') if p.name!='validation.json'},
        'checks':['frozen inputs and scores','independent feature/logit reconstruction','boundary/role masks and reference availability',
            'acyclic typed witnesses and exact scores','nested gap monotonicity','unchanged original abstention accounting',
            'all metrics and deterministic development review selection','independent Z3 optimum cross-check on reviewed streams']}
    write_json(OUT/'validation.json',validation)
    print('Validated',len(rows),'conditions;',z3_count,'independent Z3 checks;',len(cases),'reviewed residuals.',flush=True)


if __name__=='__main__':run()
