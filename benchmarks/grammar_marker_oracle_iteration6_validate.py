"""Verify frozen-weight oracle interventions and exact reference-forest gaps."""
from collections import Counter
import hashlib
import json
import math
from pathlib import Path

from benchmarks.grammar_marker_oracle_iteration6 import OUT,FIVE,OracleMarkerProvider,score_audit,MODES
from benchmarks.grammar_structure_iteration3_validate import FrozenAdapter
from benchmarks.grammar_linker_iteration4 import detailed_metrics,summarize
from benchmarks.grammar_markers_iteration5 import marker_metrics,aggregate_markers
from voynich_smt.data.corpus import digest,write_json
from voynich_smt.parent_ranking import ConditionalRanker
from voynich_smt.marker_structure import MarkerModel,infer_attached_links,validate_markers
from voynich_smt.predicate_structure import validate_structure


def run():
    load=lambda n:json.loads((OUT/n).read_text())
    previous=lambda n:json.loads((FIVE/n).read_text())
    manifest=load('manifest.json');report=load('report.json');rows=load('predictions.json')
    assert manifest['code_sha256']==hashlib.sha256(Path('benchmarks/grammar_marker_oracle_iteration6.py').read_bytes()).hexdigest()
    for p,h in manifest['input_sha256'].items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h
    assert digest(manifest)==report['manifest_sha256']
    adapter=FrozenAdapter(previous('morphology-lattice.json'));raw=previous('models.json');vocab=previous('manifest.json')['marker_vocabulary']
    learned=MarkerModel(vocab,ConditionalRanker(**raw['marker']))
    models={n:ConditionalRanker(**raw[n]) for n in ['marker_only','marker_interactions']}
    targets={r['id']:r for r in previous('target-evaluation-only-truth.json')};source=previous('confirmation-truth.json')
    baseline={('target',r['id'],r['model'],r['evidence'],r['boundaries']):r for r in previous('target-predictions.json')}
    for r in previous('source-predictions.json'):
        if (r['split'],r['evidence'],r['boundaries'])==('confirmation','oracle_predicates','hidden') and r['model'] in models:
            baseline['source_confirmation',r['stream'],r['model'],r['evidence'],r['boundaries']]=r
    new=0;reused=0;original_abstentions=0;replay_abstentions=0;rescored_refs=0
    unique=set()
    for row in rows:
        identity=(row['dataset'],row['id'] if row['dataset']=='target' else row['stream'],row['model'],row['evidence'],row['boundaries'])
        assert identity+(row['marker_mode'],) not in unique;unique.add(identity+(row['marker_mode'],))
        gold=targets[row['id']] if row['dataset']=='target' else source[row['stream']]
        base=baseline[identity];saved=row['prediction'];positions=base['prediction']['predicates']
        assert positions==saved['predicates']
        if row['evidence']=='oracle_predicates':assert positions==gold['finite']
        boundaries=gold['boundaries'] if row['boundaries']=='supplied' else None
        validate_structure(saved);validate_markers(saved,boundaries)
        if row['marker_mode']=='predicted':
            assert saved==base['prediction'];reused+=1
        else:
            provider=OracleMarkerProvider(learned,gold['markers'],row['marker_mode'])
            attached=provider.predict(gold['tokens'],positions,adapter,boundaries)
            assert saved['marker_attachments']==attached
            gold_markers={int(k):v for k,v in gold['markers'].items()}
            expected_positions={i for i,w in enumerate(gold['tokens']) if w in vocab}
            if row['marker_mode']=='oracle_full':expected_positions|=set(gold_markers)
            assert {m['position'] for m in attached}==expected_positions
            for marker in attached:
                i=marker['position'];reference=gold_markers.get(i)
                if row['marker_mode']=='oracle_scope':assert marker['kinds']==vocab[gold['tokens'][i]]
                elif reference:assert marker['kinds']==[reference['kind']]
                expected=reference['target'] if reference else None
                available=[r['target'] for r in marker['alternatives']]
                assert marker['target']==(expected if expected in available else None)
                assert marker['blocked_reference_target']==(expected is not None and expected not in available)
            replay=infer_attached_links(gold['tokens'],positions,adapter,models[row['model']],provider,
                interactions=row['model']=='marker_interactions',boundaries=boundaries)
            if saved['status']=='optimal' and replay['status']!='optimal':
                replay=infer_attached_links(gold['tokens'],positions,adapter,models[row['model']],provider,
                    interactions=row['model']=='marker_interactions',boundaries=boundaries,timeout_ms=10000)
            if saved['status']=='optimal':
                assert replay['status']=='optimal' and replay['forest_score_integer']==saved['forest_score_integer']
            else:original_abstentions+=1
            replay_abstentions+=replay['status']!='optimal'
            for child,options in saved['arc_candidates'].items():
                actual=replay['arc_candidates'][int(child)];assert len(actual)==len(options)
                for a,b in zip(actual,options):assert a['parent']==b['parent'] and a['relation']==b['relation'] and math.isclose(a['logit'],b['logit'],abs_tol=1e-10)
            new+=1
        assert detailed_metrics(saved,gold)==row['metrics']
        assert marker_metrics(saved,gold,vocab)==row['marker_metrics']
        assert score_audit(saved,gold)==row['score_audit']
        audit=row['score_audit']
        if audit['reference_forest_available']:
            # Independent exact scoring of the feasible reference skeleton.
            parents={int(c):p for c,p in gold['parents'].items()};relations={int(c):r for c,r in gold['relations'].items()}
            reference_score=0
            for child,parent in parents.items():
                options=saved['arc_candidates'].get(child,saved['arc_candidates'].get(str(child),[]))
                reference_score+=round(next(r['logit'] for r in options if r['parent']==parent and r['relation']==relations[child])*1000000)
            assert reference_score==audit['reference_score_integer']
            if saved['status']=='optimal':
                assert saved['forest_score_integer']-reference_score==audit['optimum_minus_reference_integer']>=0
                rescored_refs+=1
            else:assert audit['optimum_minus_reference_integer'] is None
        if saved['status']=='optimal':
            selected_score=sum(round(next(r['logit'] for r in saved['arc_candidates'][c] if r['parent']==p and r['relation']==saved['relations'][c])*1000000) for c,p in saved['parents'].items())
            assert selected_score==saved['forest_score_integer']
    assert len(rows)==report['conditions']==684 and new==report['new_forests']==456 and reused==report['reused_baselines']==228
    for summary in report['summary']:
        selected=[r for r in rows if (r['dataset'],r['author'] or '',r['model'],r['evidence'],r['boundaries'],r['marker_mode'])==
            tuple(summary[k] for k in ['dataset','author','model','evidence','boundaries','marker_mode'])]
        assert summarize([r['metrics'] for r in selected])==summary['metrics']
        assert aggregate_markers([r['marker_metrics'] for r in selected])==summary['markers']
        assert sum(r['score_audit']['optimum_minus_reference_integer'] is not None and r['score_audit']['optimum_minus_reference_integer']>0 for r in selected)==summary['reference_forests_strictly_outscored']
    write_json(OUT/'validation.json',{'validated':True,'conditions':len(rows),'new_forests_replayed':new,'verified_reused_baselines':reused,
        'new_saved_abstentions':original_abstentions,'replay_abstentions':replay_abstentions,'reference_forests_independently_scored':rescored_refs,
        'report_sha256':digest(report),'validator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'artifact_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.glob('*.json') if p.name!='validation.json'},
        'checks':['frozen model/input hashes','isolated marker occurrence/scope/class intervention','no predicate insertion or role conflict',
                  'forest optimum and typed witness','exact feasible-reference score gaps','all metrics and source abstention denominators']})
    print('Validated',len(rows),'conditions;',new,'new forest replays and',reused,'baseline identities;',rescored_refs,'exact reference scores.')


if __name__=='__main__':run()
