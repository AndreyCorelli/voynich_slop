from dataclasses import asdict
import numpy as np
import pytest

from voynich_smt.grammar_diagnostic import MorphAnalysis
from voynich_smt.predicate_structure import (StructureModel,Logistic,morph_features,
    candidate_parents,validate_structure)
from benchmarks.grammar_structure_iteration3 import read_conllu,metrics,aggregate


class Adapter:
    def analyze(self,w):
        if w=='unknown':return ()
        if w=='noun':return (MorphAnalysis('N',(('Case','NOM'),)),)
        return (MorphAnalysis('V',(('Mood','IND'),('Number','S'),('Person','3'))),)


class FiniteModel:
    def probability(self,x):return np.ones(len(x))*.99


class LinkModel:
    def logits(self,x):
        # All nonroot arcs score one; roots zero. The optimum must retain one
        # root to avoid a cycle, irrespective of tie-breaking among trees.
        return np.array([1-r[0] for r in x])


def model():return StructureModel(Adapter(),FiniteModel(),LinkModel())


def test_forest_exact_acyclic_optimum_and_no_cross_oracle_boundaries():
    m=model();result=m.infer(['a','b','c'])
    assert result['status']=='optimal' and validate_structure(result)
    assert sum(p is not None for p in result['parents'].values())==2
    constrained=m.infer(['a','b','c'],[1,3])
    assert constrained['parents'][0] is None
    assert sum(p is not None for p in constrained['parents'].values())==1
    assert all(p is None or (c>=1 and p>=1) for c,p in constrained['parents'].items())


def test_unknowns_and_nonfinite_tokens_stay_in_coverage():
    r=model().infer(['noun','unknown'])
    assert r['predicates']==[] and r['token_anchors']==[None,None]
    assert r['known_tokens']==1 and r['tokens']==2
    mixed=model().infer(['a','noun','unknown'])
    assert mixed['predicates']==[0] and len(mixed['token_anchors'])==3


def test_duplicate_readings_do_not_change_features():
    readings=Adapter().analyze('a')
    assert morph_features(readings)==morph_features(readings*10)


def test_parent_candidate_radius_and_bad_boundaries():
    assert candidate_parents(4,list(range(9)))==[None,1,2,3,5,6,7]
    assert candidate_parents(4,list(range(9)),[4,9])==[None,5,6,7]
    with pytest.raises(ValueError):model().infer(['a','b'],[1])


def test_source_logistic_fit_and_serialization():
    x=np.array([[-2],[-1],[1],[2]],dtype=float);y=[0,0,1,1]
    trained=Logistic.fit(x,y);copy=Logistic(**asdict(trained))
    assert trained.probability(x)[0]<.5<trained.probability(x)[-1]
    assert np.allclose(copy.logits(x),trained.logits(x))


def test_unresolved_streams_remain_in_metric_denominators():
    r=model().infer(['a','b']);r['status']='unresolved'
    gold={'finite':[0,1],'parents':{0:None,1:0},'anchors':[0,1],'boundaries':[2]}
    scored=metrics(r,gold);summary=aggregate([scored])
    assert summary['unresolved']==1 and summary['tokens']==2
    assert summary['predicates']['gold']==2 and summary['predicates']['tp']==0
    assert summary['parent_total']==2 and summary['parent_correct']==0


def test_gold_skeleton_skips_nonfinite_ancestors_and_omits_punctuation(tmp_path):
    path=tmp_path/'source.conllu'
    path.write_text("# source = Jerome's Vulgate, test\n# sent_id = example\n"
        "1\tamat\tamo\tVERB\t_\tVerbForm=Fin\t0\troot\t_\t_\n"
        "2\tdicens\tdico\tVERB\t_\tVerbForm=Part\t1\tadvcl\t_\t_\n"
        "3\taudit\taudio\tVERB\t_\tVerbForm=Fin\t2\tccomp\t_\t_\n"
        "4\tpuella\tpuella\tNOUN\t_\tCase=Nom\t3\tnsubj\t_\t_\n"
        "5\t.\t.\tPUNCT\t_\t_\t1\tpunct\t_\t_\n")
    rows,loss=read_conllu(path,'proiel');r=rows[0]
    assert r['tokens']==['amat','dicens','audit','puella']
    assert r['finite']==[0,2] and r['parents']=={0:None,2:0}
    assert r['anchors']==[0,0,2,2]
