import numpy as np
import pytest
from voynich_smt.proxy_combination import fit_linear,threshold,evaluate,grouped_intervals
from voynich_smt.latin_sentence_cases import read_conllu,mutate,PREPOSITIONS

def test_nonnegative_fit_and_calibration_threshold():
    x=np.array([[-2.,1.],[-1.,2.],[1.,1.],[2.,2.]])
    y=np.array([0,0,1,1]);p=fit_linear(x,y,.01,True)
    assert np.all(p[:-1]>=0)
    s=x@p[:-1]+p[-1];t=threshold(s,y)
    assert np.array_equal(s>=t,y.astype(bool))

def test_evaluation_does_not_credit_ties_and_keeps_valid_controls():
    rows=[{'base':'a','family':'original','valid':True},{'base':'a','family':'subject_number','valid':False},
          {'base':'a','family':'lexical_control','valid':True}]
    result=evaluate(rows,np.array([1.,1.,-1.]),0.)
    assert result['paired_accuracy']==0
    assert result['families']['lexical_control']['accuracy']==0
    assert result['balanced_accuracy']==pytest.approx(.25)

def test_cluster_resampling_keeps_sentence_variants_together():
    rows=[];scores=[]
    for base in ('a','b','c'):
        rows.extend([{'base':base,'family':'original','valid':True},{'base':base,'family':'adjective_case','valid':False}]);scores.extend([1,-1])
    intervals=grouped_intervals(rows,np.asarray(scores),0,iterations=20)
    assert intervals=={'balanced_accuracy':[1.,1.],'paired_accuracy':[1.,1.]}

def test_conllu_document_propagation_and_punctuation(tmp_path):
    path=tmp_path/'tiny.conllu'
    path.write_text('# newdoc id = author.work\n# sent_id = one\n1\tPuer\tpuer\tNOUN\t_\tCase=Nom|Number=Sing\t0\troot\t_\t_\n\n# sent_id = two\n1\tVir\tvir\tNOUN\t_\tCase=Nom\t0\troot\t_\t_\n')
    rows=read_conllu(path)
    assert [r['document'] for r in rows]==['author.work','author.work']
    assert rows[0]['tokens'][0]['word']=='puer'
    assert rows[1]['tokens'][0]['word']=='uir'

def test_ambiguous_prepositions_are_not_forced_to_one_case():
    assert 'in' not in PREPOSITIONS and 'sub' not in PREPOSITIONS
    assert PREPOSITIONS['cum']=='ABL' and PREPOSITIONS['ad']=='ACC'
