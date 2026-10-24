"""Replay structure predictions without target annotations entering inference."""
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
from collections import Counter
import math

from benchmarks.grammar_structure_iteration3 import OUT,GATE,THRESHOLDS,metrics,aggregate,prf
from voynich_smt.data.corpus import digest,write_json
from voynich_smt.grammar_diagnostic import MorphAnalysis
from voynich_smt.predicate_structure import StructureModel,Logistic,validate_structure,sentence_features
from voynich_smt.coherent_grammar import finite


class FrozenAdapter:
    def __init__(self,lattice):self.lattice=lattice
    def analyze(self,word):
        return tuple(MorphAnalysis(r['pos'],tuple(map(tuple,r['features']))) for r in self.lattice[word])


def run():
    load=lambda name:json.loads((OUT/name).read_text())
    manifest=load('manifest.json');report=load('report.json');saved_model=load('model.json')
    for p,h in {**manifest['source_sha256'],**manifest['code_sha256']}.items():
        assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h
    assert digest(manifest)==report['manifest_sha256']
    public={r['id']:r for r in load('public.json')};truth={r['id']:r for r in load('evaluation-only-truth.json')}
    adapter=FrozenAdapter(load('morphology-lattice.json'))
    model=StructureModel(adapter,Logistic(**saved_model['finite']),Logistic(**saved_model['parent']),saved_model['threshold'])
    threshold_rows=[]
    for threshold in THRESHOLDS:
        predicted=[];gold=[]
        for key,r in public.items():
            if truth[key]['author']!='Cicero':continue
            probs=model.finite_model.probability(sentence_features(r['tokens'],adapter))
            predicted += [(key,i) for i,w in enumerate(r['tokens']) if any(finite(a) for a in adapter.analyze(w)) and probs[i]>=threshold]
            gold += [(key,i) for i in truth[key]['finite']]
        threshold_rows.append({'threshold':threshold,**prf(predicted,gold)})
    assert threshold_rows==saved_model['threshold_development']
    assert max(threshold_rows,key=lambda r:(r['f1'],r['threshold']))['threshold']==saved_model['threshold']==report['threshold']
    checked=0
    def verify(prediction,tokens,gold,boundaries=None,any_finite=False):
        nonlocal checked
        validate_structure(prediction)
        result=model.infer(tokens,boundaries,any_finite=any_finite)
        # Forest scores may tie: verify recorded forest feasibility and its score
        # against the replayed optimum rather than requiring identical witnesses.
        assert result['status']==prediction['status']
        assert result['predicates']==prediction['predicates']
        assert result['known_tokens']==prediction['known_tokens']
        assert all(math.isclose(a,b,abs_tol=1e-12) for a,b in zip(result['predicate_probabilities'],prediction['predicate_probabilities']))
        def score(r):
            total=0
            for c,p in r['parents'].items():
                options=r['arc_candidates'].get(c,r['arc_candidates'].get(str(c),[]))
                total+=round(next(row['logit'] for row in options if row['parent']==p)*1000000)
            return total
        assert score(result)==score(prediction)
        if boundaries:
            def region(i):return next(j for j,b in enumerate(boundaries) if i<b)
            assert all(p is None or region(int(c))==region(p) for c,p in prediction['parents'].items())
        checked+=1
        return metrics(prediction,gold)
    rows=load('predictions.json')
    for row in rows:
        gold=truth[row['id']];tokens=public[row['id']]['tokens']
        assert tokens==gold['tokens']
        boundaries=gold['boundaries'] if row['mode']=='supplied' else None
        assert verify(row['prediction'],tokens,gold,boundaries)==row['metrics']
        assert metrics(row['prediction'],gold,'root')==row['root_baseline']
        assert metrics(row['prediction'],gold,'previous')==row['previous_baseline']
        baseline=model.infer(tokens,boundaries,any_finite=True)
        assert metrics(baseline,gold)==row['any_finite_metrics']
    for summary in report['summary']:
        chosen=[r for r in rows if r['author']==summary['author'] and r['mode']==summary['mode']]
        for k in ['metrics','root_baseline','previous_baseline','any_finite_metrics']:
            assert aggregate([r[k] for r in chosen])==summary[k]
    corrupt=load('corruption.json');pool=set(load('source-replacement-pool.json'))
    for row in corrupt:
        gold=truth[row['id']];tokens=public[row['id']]['tokens'];mapping=row['mapping']
        assert len(mapping)==round(row['rate']*len(set(tokens)))==row['changed_types']
        assert len(set(mapping.values()))==len(mapping) and not (set(mapping.values())&set(tokens))
        assert set(mapping.values())<=pool
        altered=[mapping.get(w,w) for w in tokens]
        assert sum(a!=b for a,b in zip(tokens,altered))==row['changed_tokens']
        assert verify(row['prediction'],altered,gold)==row['metrics']
    for summary in report['robustness']:
        rr=[r['metrics'] for r in corrupt if r['author']==summary['author'] and r['rate']==summary['rate']]
        assert aggregate(rr)=={k:v for k,v in summary.items() if k not in ['author','rate']}
    repair_count=0
    repair_path=OUT/'oracle-repairs.json'
    if repair_path.exists():
        repairs=load('oracle-repairs.json')
        by_case={(r['id'],r['seed'],r['rate']):r for r in corrupt}
        for row in repairs['rows']:
            old=by_case[(row['id'],row['seed'],row['rate'])];original=public[row['id']]['tokens'];gold=truth[row['id']]
            remaining={w:v for w,v in old['mapping'].items() if w!=row['oracle_restored_entry']}
            assert remaining==row['mapping_after'] and len(remaining)==len(old['mapping'])-1
            assert row['before']==old['metrics']
            altered=[remaining.get(w,w) for w in original]
            assert verify(row['prediction'],altered,gold)==row['after']
            assert math.isclose(row['after']['predicates']['f1']-row['before']['predicates']['f1'],row['finite_f1_delta'],abs_tol=1e-12)
            repair_count+=1
        assert repair_count==72
    held=[s for s in report['summary'] if s['author']!='Cicero' and s['mode']=='latent']
    gate=all(s['metrics']['predicates']['f1']>=GATE['predicate_f1'] and s['metrics']['edges']['f1']>=
        max(s['root_baseline']['edges']['f1'],s['previous_baseline']['edges']['f1'])+GATE['edge_f1_gain'] for s in held)
    assert gate==report['gate_pass']
    assert len(public)==12 and len(corrupt)==180
    write_json(OUT/'validation.json',{'validated':True,'score_replays':checked,'oracle_single_entry_repairs':repair_count,'finite_threshold_verified_on_development_only':True,
        'gate_pass':gate,'report_sha256':digest(report),
        'artifact_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.glob('*.json') if p.name!='validation.json'},
        'validator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'checks':['complete token coverage and acyclic skeletons','candidate forest score equals replay optimum',
                  'public token-only replay with optional oracle boundaries','all metrics and baselines','injective full-entry corruption maps','frozen gate decision']})
    print(f'Validated {checked} main/corruption predictions, all summaries, thresholds and gates.')


if __name__=='__main__':run()
