import z3
from benchmarks.latin_joint_coverage import datasets,vocabulary,query_truth,audit_example
from benchmarks.latin_joint_identifiability import encode
from voynich_smt.joint_grammar_coverage import CoverageGrammar,coverage_syntax


def fixture(name,broad=False,level='lean'):
    rows=next(rows for n,_,rows in datasets() if n==name);inputs,truth=encode(rows,3219);lex=vocabulary(level)
    return CoverageGrammar(lex,inputs['ciphertext'],broad=broad),truth,lex


def test_missing_rule_can_produce_unique_wrong_structure():
    solver,truth,lex=fixture('genitive-coherent-six')
    result=solver.enumerate('structure');q=query_truth(solver,truth)
    assert result['count']==1 and result['status']=='complete'
    assert q['original_structure']['status']=='unsat' and q['wrong_structure']['status']=='sat'
    assert q['true_dictionary_status']=='unsat'
    audit_example(result['examples'][0],lex,False)


def test_broader_grammar_admits_original_and_exposes_ambiguity():
    solver,truth,lex=fixture('genitive-coherent-six',True)
    q=query_truth(solver,truth);assert q['true_dictionary_and_structure']['status']=='sat'
    result=solver.enumerate('structure');assert result['status']=='complete' and result['count']>1
    audit_example(q['true_dictionary_and_structure']['example'],lex,True)


def test_missing_subject_can_be_reinterpreted_then_rejected_with_context():
    alone,truth,_=fixture('omitted-subject-alone');assert alone.solver.check()==z3.sat
    assert query_truth(alone,truth)['true_dictionary_status']=='unsat'
    contextual,truth,_=fixture('omitted-subject-with-context');assert contextual.solver.check()==z3.unsat
    covered,truth,_=fixture('omitted-subject-with-context',True)
    assert query_truth(covered,truth)['true_dictionary_and_structure']['status']=='sat'


def test_known_context_and_supported_genitive_can_identify_structure():
    solver,truth,lex=fixture('genitive-with-context',True)
    result=solver.enumerate('structure');assert result['status']=='complete' and result['count']==1
    assert solver.query_structure(truth['roles'],truth['heads'],different=True)['status']=='unsat'
    audit_example(result['examples'][0],lex,True)


def test_coordinated_subject_agrees_as_plural_not_first_noun_number():
    lex=vocabulary('lean')
    for verb,expected in [('dormit',z3.unsat),('dormiunt',z3.sat)]:
        words=['puella','et','puer',verb];solver=CoverageGrammar(lex,[words],broad=True)
        solver.solver.add(*[v==solver.word_index[t] for t,v in solver.mapping.items()])
        assert solver.solver.check()==expected
        if expected==z3.sat:audit_example(solver.example(solver.solver.model()),lex,True)


def test_coordinated_copular_predicate_requires_unimplemented_group_gender():
    assert not any('cc' in c.parse.roles and 'xcomp' in c.parse.roles for c in coverage_syntax(5,broad=True))
