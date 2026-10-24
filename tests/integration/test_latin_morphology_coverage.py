from benchmarks import latin_morphology_coverage as b


def test_independent_recognizer_and_negative():
    engine=b.parser('upstream-default')
    recognized=b.evidence(engine,'regem')
    assert recognized['recognized'] and recognized['analyses']
    assert not b.evidence(engine,'zzzzzzzz')['recognized']
    assert b.canonical('jv')=='iu'


def test_orthography_is_separate_and_occurrences_counted():
    p={'fixed_passage':{'plaintext':{'words':[list('via'),list('x'),list('x')]},'holdout_plaintext':{'words':[list('uia')]}},'query_words':['via','x','uia'],'attested_words':[list('uia')],'grid_windows':[{'words':[list('x'),list('x')]}]}
    rows=b.calculate(p,{'toy':{'via':{'recognized':True},'x':{'recognized':False},'uia':{'recognized':True}}})['rows']
    assert rows[0]['training']['missing_occurrences']==3
    assert rows[1]['training']['missing_occurrences']==2
    assert rows[2]['grid']['at_most_one_missing']==0
