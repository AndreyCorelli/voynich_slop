import pytest
from voynich_smt.copular_head_oracle import MASKS,case_allowed,in_adp_phrase,clause_anchor,flags,indices


def token(pos,head,rel,**features):
    return dict(pos=pos,head=head,rel=rel,features=features)


def example():
    return [token('NOUN',4,'nsubj',Case='Nom'),token('ADP',2,'case'),token('NOUN',4,'obl',Case='Abl'),token('ADJ',2,'amod',Case='Abl'),token('ADJ',None,'root',Case='Nom'),token('AUX',4,'cop',VerbForm='Fin'),token('VERB',4,'advcl',VerbForm='Fin'),token('NOUN',6,'nsubj',Case='Nom')]


def test_case_unknown_and_ambiguity_are_permissive():
    assert case_allowed(token('NOUN',None,'root'))
    assert case_allowed(token('NOUN',None,'root',Case='Nom,Acc'))
    assert not case_allowed(token('NOUN',None,'root',Case='Gen'))


def test_adp_membership_extends_to_nominal_modifier():
    ts=example()
    assert in_adp_phrase(ts,2) and in_adp_phrase(ts,3)
    assert not in_adp_phrase(ts,4)
    assert flags(ts,2,5)['phrase'] and not flags(ts,2,5)['adp']
    assert not flags(ts,3,5)['phrase']


def test_clause_locality_follows_carrier_to_its_annotated_head():
    ts=example()
    assert clause_anchor(ts,5)==clause_anchor(ts,4)==4
    assert clause_anchor(ts,7)==6
    assert flags(ts,4,5)['clause'] and not flags(ts,7,5)['clause']
    # This intentionally reads the annotated cop edge: it is an oracle diagnostic.
    ts[5]['head']=6
    assert not flags(ts,4,5)['clause']


def test_cycles_do_not_hang_and_unknown_clause_remains_permissive():
    ts=[token('NOUN',1,'nmod'),token('NOUN',0,'nmod')]
    assert clause_anchor(ts,0) is None
    assert not in_adp_phrase(ts,0)
    assert flags(ts,0,1)['clause']


def test_factorial_masks_preserve_subsets_and_type_is_explicit():
    assert len(MASKS)==16
    options=[(5,'direct'),(2,'cop'),(4,'cop'),(4,'aux')];ts=example();f={h:flags(ts,h,5) for h,_ in options}
    assert indices(options,f,'none','free_type')==[0,1,2,3]
    assert indices(options,f,'none','cop_type')==[1,2]
    assert indices(options,f,'case+adp+phrase+clause','cop_type')==[2]
    with pytest.raises(ValueError):indices(options,f,'unknown','free_type')
