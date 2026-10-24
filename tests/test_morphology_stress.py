from voynich_smt.morphology_stress import schedule,perturb,support,encode,decode,link_summary


def lexicon():
    return {'puella\tNOUN':[['Nom','Sing','3','']], 'uenit\tVERB':[['','Sing','3','Fin']]}


def test_extra_preserves_support_while_substitution_removes_same_original_reading():
    lex=lexicon();plan=schedule(lex,lex,7);extra,_=perturb(lex,plan,1,'extra');sub,_=perturb(lex,plan,1,'substituted');deleted,_=perturb(lex,plan,1,'deleted')
    for key in lex:
        edit=plan['plans'][key]
        assert edit['original'] in extra[key] and edit['original'] not in sub[key]
        assert edit['extra'] in extra[key] and edit['extra'] in sub[key]
        assert deleted[key]==[]
        assert extra[key]!=lex[key]
    assert lex==lexicon()


def test_mask_preserves_nominal_third_person_and_roles():
    lex=lexicon();plan=schedule(lex,lex,7);masked,_=perturb(lex,plan,1,'masked')
    assert masked['puella\tNOUN']==[['Nom','','3','']]
    assert masked['uenit\tVERB']==[['','','','Fin']]
    assert support(masked['uenit\tVERB'],'VERB')>=support(lex['uenit\tVERB'],'VERB')


def test_nested_selection_and_edit_are_fixed_across_rates_and_modes():
    lex={f'n{i}\tNOUN':[['Nom','Sing','3','']] for i in range(10)};plan=schedule(lex,lex,9)
    _,small=perturb(lex,plan,.2,'extra');_,large=perturb(lex,plan,.5,'substituted')
    assert small==large[:2] and len(large)==5
    assert plan==schedule(lex,lex,9)


def test_schedule_skips_types_whose_relevant_support_is_already_unconstrained():
    lex={'v\tVERB':[['','','','Fin']],'n\tNOUN':[['Nom','','3','']]}
    assert schedule(lex,lex,1)['order']==[]


def test_compact_support_round_trip_and_exact_vs_link_survival():
    candidates=[[0,1,'Sing','3','Sing','3'],[0,1,'Plur','3','Plur','3']];blocks=encode(candidates)
    assert set(map(tuple,decode(blocks)))==set(map(tuple,candidates))
    assert blocks[0][2]<2**36
    ref=[0,1,'Sing','3','Plur','3'];s=link_summary(blocks,ref)
    assert s['reference_link'] and not s['reference_exact'] and s['unique_correct']


def test_wrong_unique_is_distinguished_from_empty_and_correct():
    ref=[0,1,'Sing','3','Sing','3'];wrong=encode([[2,1,'Sing','3','Sing','3']])
    assert link_summary(wrong,ref)['false_unique']
    assert not link_summary([],ref)['false_unique']
    assert link_summary(encode([ref]),ref)['unique_correct']
