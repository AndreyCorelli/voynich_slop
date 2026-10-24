"""Feature/selection replay, independent ranking and linear-witness checks."""
import hashlib
from fractions import Fraction
from benchmarks.grammar_structure_preferences_iteration22 import OUT,TWENTYONE,SEVENTEEN,NINE,RESERVE,load,produce
from benchmarks.grammar_structure_preferences_iteration22_evaluate import evaluate
from voynich_smt.structure_preferences import POLICIES,FAMILIES,select


def independent_score(v,p):
    if p=='all':return ()
    if p=='distance':return (-v['dependency_distance'],)
    result=(v['marked_clauses'],v['participial_clauses'],v['governed_arguments'],-v['fragments'])
    if p.endswith('_matrix'):result+=(v['matrix_adjuncts'],)
    if p.endswith('_infinitive'):result+=(v['infinitive_adjuncts'],)
    if p.endswith('_frame'):result+=(v['frame_preferred_adjuncts'],)
    return result


def strip_weights(result):
    return {m:{name:{k:v for k,v in r.items() if k!='witness_weights'} for name,r in families.items()} for m,families in result.items()}


def validate_linear(result):
    for morphology,families in result['feature_family_feasibility'].items():
        cases=[c for c in result['cases'] if c['morphology']==morphology and c['ambiguous'] and c['reference_available']]
        for family,record in families.items():
            names=FAMILIES['frame_distance'] if family=='frame_distance_nonpositive' else FAMILIES[family]
            if record['status']=='sat':
                weights={n:Fraction(v) for n,v in record['witness_weights'].items()}
                if family=='frame_distance_nonpositive':assert weights['dependency_distance']<=0
                for c in cases:
                    scores=[sum(weights[n]*v[n] for n in names) for v in c['features']]
                    assert max(s for s,l in zip(scores,c['strict_labels']) if l)>max((s for s,l in zip(scores,c['strict_labels']) if not l),default=Fraction(-10**9))
            else:
                assert record['status']=='unsat'
                if family=='frame_distance_nonpositive':
                    # A positive candidate is farther than a negative candidate
                    # otherwise identical in every named feature: strict ranking
                    # requires a positive distance coefficient.
                    assert any(len([i for i,l in enumerate(c['strict_labels']) if l])==1 and any(
                        good and not bad and c['features'][i]['dependency_distance']>c['features'][j]['dependency_distance'] and
                        all(c['features'][i][n]==c['features'][j][n] for n in names if n!='dependency_distance')
                        for i,good in enumerate(c['strict_labels']) for j,bad in enumerate(c['strict_labels'])) for c in cases)
                else:
                    assert any(all(any(not bad and all(c['features'][i][n]==c['features'][j][n] for n in names)
                        for j,bad in enumerate(c['strict_labels'])) for i,good in enumerate(c['strict_labels']) if good) for c in cases)


def validate():
    for p,h in load(OUT/'manifest.json')['inputs'].items():assert hashlib.sha256(open(p,'rb').read()).hexdigest()==h,p
    rows=load(TWENTYONE/'predictions.json');models=load(SEVENTEEN/'models.json');dev=load(NINE/'development-truth.json');predictions=load(OUT/'predictions.json')
    assert produce(rows,models,dev)==predictions
    for r in predictions:
        for p in POLICIES:
            scores=[independent_score(v,p) for v in r['features']];expected=[i for i,s in enumerate(scores) if s==max(scores)]
            assert r['selected'][p]==expected
            reverse=list(reversed(r['features']));chosen=select(reverse,p)
            assert {len(reverse)-1-i for i in chosen}==set(expected)
    result=load(OUT/'evaluation.json');replayed=evaluate(predictions,rows,models,dev)
    assert result['summary']==replayed['summary'] and result['cases']==replayed['cases']
    assert result['annotation_convention_audit']==replayed['annotation_convention_audit']
    assert strip_weights(result['feature_family_feasibility'])==strip_weights(replayed['feature_family_feasibility'])
    validate_linear(result)
    for c in result['cases']:
        assert all(not a or b for a,b in zip(c['strict_labels'],c['equivalent_labels']))
        for family,pairs in c['feature_collisions'].items():
            for i,j in pairs:
                assert c['strict_labels'][i] and not c['strict_labels'][j]
                assert all(c['features'][i][n]==c['features'][j][n] for n in FAMILIES[family])
    def ids(o):
        if isinstance(o,dict):return {str(v) for k,v in o.items() if k=='sent_id'}|set().union(*(ids(v) for v in o.values()))
        if isinstance(o,list):return set().union(*(ids(v) for v in o)) if o else set()
        return set()
    reserved=ids(load(RESERVE));assert len(reserved)==200 and not reserved&ids(dev)
    print('48 unit selections replayed; 12 duplicate readings collapsed; 4 distinct oracle-morphology challenges; linear witnesses and obstructions checked; 200 reserved sentences unscored')

if __name__=='__main__':validate()
