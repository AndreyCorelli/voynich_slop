from benchmarks.broader_contraction_capacity import minimum,applies


def rule(id,text,cost=1,position='any',**kwargs):
    return dict(id=id,expansion=text,units=cost,position=position,**kwargs)


def test_retained_letters_count_and_one_unit_ceiling_is_separate():
    rules=[rule('dominus','dominus',3,'whole')]
    assert minimum('dominus',rules)[0]==3
    assert minimum('dominus',rules,True)[0]==1
    assert minimum('dominusque',rules)[0]==10


def test_nonoverlapping_and_scoped_rules():
    rules=[rule('per','per'),rule('rum','rum',position='final')]
    assert minimum('perum',rules)[0]==3
    assert minimum('rumor',[rules[1]])[0]==5
    bus=rule('us','us',position='final',left='b')
    assert minimum('hominibus',[bus])[0]==8
    assert minimum('dominus',[bus])[0]==7


def test_nasal_boundary_approximation_is_explicit():
    r=rule('am','am',right='consonant-or-end')
    assert applies('campus',1,r)
    assert applies('quam',2,r)
    assert not applies('amare',0,r)
