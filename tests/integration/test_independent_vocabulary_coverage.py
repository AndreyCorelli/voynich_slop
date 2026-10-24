from benchmarks import independent_vocabulary_coverage as b


def test_frequency_ranking_prefix_only_and_nested():
    records=[{'tokens':list(w),'excluded_reason':None} for w in ('b','a','b','c','z','z','z','z')]
    rankings,counts,first=b.inventories(records,set(map(tuple,'abcz')),set('abcz'))
    assert rankings['corpus-order']==list(map(tuple,'bac'))
    assert rankings['frequency']==list(map(tuple,'bac'))
    assert tuple('z') not in counts and first[tuple('b')]==0
    assert set(rankings['frequency'][:1])<set(rankings['frequency'][:2])


def test_occurrence_coverage_and_public_lengths():
    assert not b.audit([tuple('x'),tuple('x')],{tuple('a')})['admitted_one_oov']
    a=b.audit([tuple('xx')],{tuple('a')})
    assert a['missing_occurrences']==1 and a['outside_public_length_positions']==[0] and not a['admitted_one_oov']
    assert b.audit([tuple('b')],{tuple('a')})['admitted_one_oov']


def test_grid_does_not_skip_inside_barriers():
    records=[{'tokens':['a'],'excluded_reason':None} for _ in range(96)]
    records[50]['excluded_reason']='barrier'
    selected,rejected=b.windows(records,{('a',)},{'a'})
    assert rejected==[48] and [w['start'] for w in selected]==[72]


def test_report_survives_json_roundtrip(monkeypatch):
    import json
    from voynich_smt.data.corpus import digest
    monkeypatch.setattr(b,'SIZES',(1,))
    p={'languages':{'toy':{'rankings':{'corpus-order':[['a'],['b']]},'fixed_passage':{'plaintext':{'words':[['x'],['x']]},'holdout_plaintext':{'words':[['a']]}},'grid_windows':[{'words':[['x'],['x']]}],'rejected_grid_starts':[]}}}
    r=b.calculate(p)
    assert digest(r)==digest(json.loads(json.dumps(r)))
