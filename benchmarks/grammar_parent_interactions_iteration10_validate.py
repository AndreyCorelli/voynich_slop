"""Refit the development ablation and verify paired parent changes and optima."""
from collections import Counter
import hashlib
import json
from pathlib import Path
from unittest.mock import patch
import numpy as np
from benchmarks.grammar_parent_interactions_iteration10 import (OUT,PREVIOUS,SEVEN,GATE,interaction_groups,scored_candidates,summaries_for,gate_decision,paired_comparisons)
from benchmarks.grammar_training_alignment_iteration7 import FixedMarkers
from benchmarks.grammar_training_alignment_iteration7_validate import same_model
from benchmarks.grammar_structure_iteration3_validate import FrozenAdapter
from benchmarks.grammar_marker_oracle_iteration6 import OracleMarkerProvider,score_audit
from benchmarks.grammar_markers_iteration5 import marker_metrics
from benchmarks.grammar_linker_iteration4 import detailed_metrics
from benchmarks.grammar_boundary_role_iteration8 import CONDITIONS,masked_options,solve_options,diagnostic_counts,region
from voynich_smt.parent_ranking import ConditionalRanker,choices
from voynich_smt.marker_structure import MarkerModel,infer_attached_links,validate_markers
from voynich_smt.predicate_structure import validate_structure
from voynich_smt.data.corpus import write_json,digest


def parent_changes(index,truth,training,markers,condition):
    counts=Counter();cases=[]
    for i,gold in enumerate(truth):
        a=index['development',i,training,'marker_only',markers,condition]['prediction']
        b=index['development',i,training,'interactions',markers,condition]['prediction']
        for child,reference in gold['parents'].items():
            before=a['parents'][child];after=b['parents'][child]
            ca,cb=before==reference,after==reference
            outcome='corrected' if cb and not ca else 'regressed' if ca and not cb else 'both_correct' if ca else 'both_wrong'
            counts[outcome]+=1
            if before==after:continue
            c=int(child);start=0
            for sent,end in zip(gold['sentences'],gold['boundaries']):
                if c<end:break
                start=end
            cases.append({'stream':i,'sent_id':sent['sent_id'],'child':c,'surface':gold['tokens'][c],
                'reference_parent':reference,'reference_surface':gold['tokens'][reference] if reference is not None else 'ROOT',
                'before_parent':before,'before_surface':gold['tokens'][before] if before is not None else 'ROOT',
                'after_parent':after,'after_surface':gold['tokens'][after] if after is not None else 'ROOT',
                'outcome':outcome,'after_cross_sentence':after is not None and region(c,gold['boundaries'])!=region(after,gold['boundaries']),
                'sentence_text':' '.join(gold['tokens'][start:end])})
    return {'training':training,'markers':markers,'condition':condition,'parent_outcomes':dict(counts),'changed_parent_cases':cases}


def run():
    load=lambda p:json.loads(p.read_text());manifest=load(OUT/'manifest.json');report=load(OUT/'report.json')
    assert digest(manifest)==report['manifest_sha256'] and manifest['gate']==GATE
    for p,h in {**manifest['input_sha256'],**manifest['code_sha256']}.items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h
    prior_validation=load(PREVIOUS/'validation.json');assert prior_validation['validated']
    for n,h in prior_validation['artifact_sha256'].items():assert hashlib.sha256((PREVIOUS/n).read_bytes()).hexdigest()==h
    raw=load(PREVIOUS/'models.json');saved_models=load(OUT/'models.json')
    adapter=FrozenAdapter(load(SEVEN/'morphology-lattice.json'));marker=MarkerModel(raw['marker_vocabulary'],ConditionalRanker(**raw['marker']))
    train=load(PREVIOUS/'train-truth.json')
    gold_attached=[OracleMarkerProvider(marker,s['markers'],'oracle_full').predict(s['tokens'],s['finite'],adapter) for s in train]
    models={}
    for training,attached in [('gold',gold_attached),('oof',load(PREVIOUS/'oof-markers.json'))]:
        groups=interaction_groups(train,attached,adapter);assert len(groups)==saved_models['group_counts'][training]==1385
        ranker=ConditionalRanker.fit_groups(groups);same_model(ranker,saved_models['parents'][training+'_interactions'])
        models[training,'interactions']=ConditionalRanker(**saved_models['parents'][training+'_interactions'])
        assert saved_models['parents'][training+'_marker_only']==raw['parents']['revised_'+training]
        models[training,'marker_only']=ConditionalRanker(**saved_models['parents'][training+'_marker_only'])
    print('Two interaction parent refits and frozen controls verified',flush=True)
    rows=load(OUT/'predictions.json');summaries=summaries_for(rows)
    assert summaries==report['summary'];gate=gate_decision(summaries)
    assert gate==report['development_gate']==load(OUT/'development-gate.json')
    assert report['confirmation_evaluated']==gate['passed']
    if not gate['passed']:
        assert all(r['split']=='development' for r in rows)
        assert not (OUT/'post-gate-inputs.json').exists()
    prior_rows=load(PREVIOUS/'predictions.json')
    priors={(r['split'],r['stream'],r['model'],r['markers'],r['condition']):r for r in prior_rows if r['model'] in ['revised_gold','revised_oof']}
    truth={split:load(PREVIOUS/(split+'-truth.json')) for split in sorted({r['split'] for r in rows})}
    cache={};index={};gaps={};baseline_checks=0
    for row in rows:
        identity=(row['split'],row['stream'],row['training'],row['features'],row['markers']);key=identity+(row['condition'],)
        assert key not in index;index[key]=row;gold=truth[row['split']][row['stream']]
        if identity not in cache:
            template=priors[row['split'],row['stream'],'revised_gold','gold','unrestricted']['prediction']
            provider=marker if row['markers']=='predicted' else OracleMarkerProvider(marker,gold['markers'],'oracle_full')
            cache[identity]=scored_candidates(template,gold,adapter,models[row['training'],row['features']],provider,row['features']=='interactions')
        scored=cache[identity];bounds,roles=CONDITIONS[row['condition']]
        expected=solve_options(scored,masked_options(scored,gold,bounds,roles));saved=row['prediction']
        validate_structure(saved);validate_markers(saved,None)
        assert saved['forest_score_integer']==expected['forest_score_integer']
        assert saved['marker_attachments']==expected['marker_attachments'] and saved['predicates']==gold['finite']
        for c,options in saved['arc_candidates'].items():assert options==expected['arc_candidates'][int(c)]
        selected=sum(round(next(r['logit'] for r in saved['arc_candidates'][c] if (r['parent'],r['relation'])==(p,saved['relations'][c]))*1e6) for c,p in saved['parents'].items())
        assert selected==saved['forest_score_integer']
        assert score_audit(saved,gold)==row['audit'] and row['audit']['reference_forest_available']
        assert detailed_metrics(saved,gold)==row['metrics']
        assert diagnostic_counts(saved,gold)==row['diagnostic']
        assert marker_metrics(saved,gold,marker.vocabulary)==row['marker_metrics']
        if row['features']=='marker_only':
            previous=priors[row['split'],row['stream'],'revised_'+row['training'],row['markers'],row['condition']]
            assert saved['forest_score_integer']==previous['prediction']['forest_score_integer']
            assert row['metrics']==previous['metrics'];baseline_checks+=1
        # Feature arms must see the exact same evidence and allowed parents.
        counterpart=identity[:3]+('marker_only',)+identity[4:]+(row['condition'],)
        if row['features']=='interactions':
            control=index[counterpart]['prediction']
            assert saved['marker_attachments']==control['marker_attachments']
            for c,opts in saved['arc_candidates'].items():
                assert [(r['parent'],r['relation']) for r in opts]==[(r['parent'],r['relation']) for r in control['arc_candidates'][c]]
        gaps[key]=row['audit']['optimum_minus_reference_integer']
    for identity in cache:
        g=lambda mode:gaps[identity+(mode,)]
        assert 0<=g('both')<=g('boundaries')<=g('unrestricted') and g('both')<=g('roles')<=g('unrestricted')
    assert len(rows)==report['conditions']==2112*(2 if gate['passed'] else 1)
    assert paired_comparisons(rows)==report['paired_comparisons']
    reviewed=load(PREVIOUS/'review.json');streams=sorted({c['stream'] for c in reviewed['remaining_residuals']});z3_count=0
    for stream in streams:
        gold=truth['development'][stream]
        for evidence in ['gold','predicted']:
            for condition in CONDITIONS:
                saved=index['development',stream,'oof','interactions',evidence,condition]['prediction']
                allowed={int(c):{(r['parent'],r['relation']) for r in opts} for c,opts in saved['arc_candidates'].items()}
                def restricted(tokens,child,predicates,morph,**kwargs):
                    return [r for r in choices(tokens,child,predicates,morph,**kwargs) if (r['parent'],r['relation']) in allowed[child]]
                with patch('voynich_smt.parent_ranking.choices',restricted):
                    actual=infer_attached_links(gold['tokens'],gold['finite'],adapter,models['oof','interactions'],FixedMarkers(saved['marker_attachments']),interactions=True,timeout_ms=10000)
                assert actual['status']=='optimal' and actual['forest_score_integer']==saved['forest_score_integer'],(stream,evidence,condition)
                z3_count+=1
    reviews=[parent_changes(index,truth['development'],training,markers,condition) for training in ['gold','oof'] for markers in ['gold','predicted'] for condition in ['unrestricted','roles','both']]
    sensitivity=[]
    for training in ['gold','oof']:
        for features in ['marker_only','interactions']:
            for condition in ['roles','both']:
                changed=0
                for i in range(len(truth['development'])):
                    a=index['development',i,training,features,'gold',condition]['prediction']
                    b=index['development',i,training,features,'predicted',condition]['prediction']
                    changed+=a['parents']!=b['parents']
                sensitivity.append({'training':training,'features':features,'condition':condition,'marker_evidence_changed_forests':changed})
    write_json(OUT/'review.json',{'scope':'paired development parent changes; mechanical error classification plus saved sentence contexts',
        'comparisons':reviews,'fixed_role_marker_sensitivity':sensitivity})
    # Paired ambiguous-parent accuracy intervals, retaining empty-stream counts.
    ambiguous_intervals=[]
    rng=np.random.default_rng(1729)
    for evidence in ['gold','predicted']:
        get=lambda features:[r for r in rows if (r['split'],r['training'],r['features'],r['markers'],r['condition'])==('development','oof',features,evidence,'both')]
        a,b=get('marker_only'),get('interactions');draws=rng.integers(0,len(a),(2000,len(a)))
        counts=lambda rr:np.array([[r['diagnostic']['ambiguous_nonroot_correct'],r['diagnostic']['ambiguous_nonroot_total']] for r in rr])
        aa,bb=counts(a),counts(b);acc=lambda x:x[...,0]/np.maximum(1,x[...,1]);delta=acc(bb[draws].sum(axis=1))-acc(aa[draws].sum(axis=1))
        ambiguous_intervals.append({'markers':evidence,'difference':float(acc(bb.sum(axis=0))-acc(aa.sum(axis=0))),
            'percentile_95_interval':np.quantile(delta,[.025,.975]).tolist(),'draws':2000,'seed':1729,'scope':'paired development streams; descriptive'})
    validation={'validated':True,'source_models_refit':2,'conditions':len(rows),'baseline_conditions_reproduced':baseline_checks,
        'independent_Z3_conditions':z3_count,'gate_verified':gate,'ambiguous_parent_intervals':ambiguous_intervals,
        'report_sha256':digest(report),'validator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'artifact_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.glob('*.json') if p.name!='validation.json'},
        'checks':['frozen repaired reference/marker fits and OOF evidence','two identical-group parent refits','baseline optimum and metric identities',
            'identical candidate pools and marker evidence across arms','candidate scores and acyclic exact optima','exact reference gaps and nested monotonicity',
            'all summaries, paired intervals and predeclared development gate','independent Z3 cross-check','confirmation remains unevaluated when gate fails']}
    write_json(OUT/'validation.json',validation)
    print('Validated',len(rows),'conditions;',z3_count,'Z3 checks; development gate',gate['passed'],flush=True)


if __name__=='__main__':run()
