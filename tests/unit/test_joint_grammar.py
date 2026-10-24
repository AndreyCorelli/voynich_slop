import z3
from voynich_smt.joint_grammar import JointGrammar,Reading
from benchmarks.latin_joint_identifiability import corpus,encode,lexicon,audit_example


def test_repeated_contexts_identify_structure_without_gold_solver_inputs():
    rows=corpus()[:6];inputs,truth=encode(rows)
    assert set(inputs)=={'ciphertext'}
    solver=JointGrammar(lexicon('base'),inputs['ciphertext'],max_adjectives=0,allow_pp=False)
    result=solver.enumerate('structure')
    assert result['status']=='complete' and result['count']==1
    assert solver.query_structure(truth['roles'],truth['heads'],different=True)['status']=='unsat'
    assert solver.query_mapping(truth['dictionary'])=='sat'
    dictionaries=solver.enumerate('dictionary',limit=1000)
    assert dictionaries['status']=='complete' and dictionaries['count']>1
    audit_example(result['examples'][0],lexicon('base'))


def test_syncretism_leaves_genuinely_different_structures():
    inputs,truth=encode(corpus()[:6]);solver=JointGrammar(lexicon('syncretic'),inputs['ciphertext'],max_adjectives=0,allow_pp=False)
    result=solver.enumerate('structure')
    assert result['status']=='complete' and result['count']>1
    wrong=solver.query_structure(truth['roles'],truth['heads'],different=True)
    assert wrong['status']=='sat';audit_example(wrong['example'],lexicon('syncretic'))


def test_no_separate_reading_can_rescue_each_adjective():
    n1=Reading('N','NOM','S','M');n2=Reading('N','NOM','P','F')
    a1=Reading('ADJ','NOM','S','M');a2=Reading('ADJ','NOM','P','F')
    # Each adjective independently matches a noun reading; no single reading matches both.
    assert all(any(all(getattr(n,f)==getattr(a,f) for f in ('case','number','gender')) for n in (n1,n2)) for a in (a1,a2))
    lex={'noun':[n1,n2],'first':[a1],'second':[a2],'verb':[Reading('V',number='S',valency='intransitive'),Reading('V',number='P',valency='intransitive')]}
    candidates={w:[w] for w in lex};solver=JointGrammar(lex,[['noun','first','second','verb']],candidates=candidates,max_adjectives=2,allow_pp=False)
    assert solver.solver.check()==z3.unsat


def test_same_decoded_surface_may_have_different_readings_per_occurrence():
    lex={'ambiguous':[Reading('N','NOM','S','M'),Reading('N','ACC','S','M')],
         'subject':[Reading('N','NOM','S','F')],
         'sleeps':[Reading('V',number='S',valency='intransitive')],
         'sees':[Reading('V',number='S',valency='transitive')]}
    sentences=[['ambiguous','sleeps'],['subject','ambiguous','sees']]
    solver=JointGrammar(lex,sentences,candidates={w:[w] for w in lex},max_adjectives=0,allow_pp=False)
    assert solver.solver.check()==z3.sat
    ex=solver.example(solver.solver.model());audit_example(ex,lex)
    assert ex['sentences'][0]['readings'][0]['case']=='NOM'
    assert ex['sentences'][1]['readings'][1]['case']=='ACC'


def test_global_injectivity_differs_from_independent_sentence_injectivity():
    lex={'puella':[Reading('N','NOM','S','F')],'dormit':[Reading('V',number='S',valency='intransitive')]}
    ss=[['a','v'],['b','v']];pools={'a':['puella'],'b':['puella'],'v':['dormit']}
    assert JointGrammar(lex,ss,pools,shared=True,max_adjectives=0,allow_pp=False).solver.check()==z3.unsat
    assert JointGrammar(lex,ss,pools,shared=False,max_adjectives=0,allow_pp=False).solver.check()==z3.sat


def test_attachment_can_remain_ambiguous_even_with_known_dictionary():
    words=['puella','puerum','amat','cum','rosa'];lex=lexicon('rich')
    solver=JointGrammar(lex,[words],candidates={w:[w] for w in words},noun_attachment=True,max_adjectives=0)
    result=solver.enumerate('structure')
    assert result['count']==3 and result['status']=='complete'
    for ex in result['examples']:audit_example(ex,lex)
