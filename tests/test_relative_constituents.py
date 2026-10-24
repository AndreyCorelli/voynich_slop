import pytest
from voynich_smt.grammar_diagnostic import LatinAdapter,MorphAnalysis
from voynich_smt.relative_constituents import ConstituentAdapter,infer,noun_phrases
from voynich_smt.word_mapping.morphology import WhitakerAnnotator
from benchmarks.grammar_relative_constituents_iteration15 import PROBES,signature

@pytest.fixture(scope='module')
def adapter():return ConstituentAdapter(WhitakerAnnotator('data/vendor/whitakers-words',mode='upstream-default'))

def probe(adapter,definition,**options):
    _,text,pwords,mword,cword,words=definition;t=text.split()
    expected=sorted([(t.index(h),t.index(v) if v else None,t.index(p)) for h,v,p in words],key=str)
    result=infer(t,[t.index(w) for w in pwords],t.index(mword),t.index(cword),adapter,**options)
    return result,expected

@pytest.mark.parametrize('definition',PROBES,ids=[p[0] for p in PROBES])
def test_construction_probes(adapter,definition):
    assert len(definition[2])>=3
    result,expected=probe(adapter,definition,nonfinite=True,object_frames=True)
    assert signature(result)==expected
    if len(expected)>1:assert result['status']=='ambiguous'


def test_declared_have_frame_is_separate(adapter):
    result,_=probe(adapter,PROBES[2],nonfinite=True,object_frames=False)
    assert not result['chains']
    result,expected=probe(adapter,PROBES[2],nonfinite=True,object_frames=True)
    assert signature(result)==expected


def test_dictionary_frame_needs_no_manual_addition(adapter):
    result,expected=probe(adapter,PROBES[8],nonfinite=True,object_frames=False)
    assert signature(result)==expected
    assert result['chains'][0]['nonfinite_verb']['features']


def test_no_participial_chain_without_shared_subject(adapter):
    text='pueri currunt hodie accedit habens puellam bonam quae cantat';tokens=text.split()
    result=infer(tokens,[1,3,8],7,8,adapter,nonfinite=True,object_frames=True)
    assert not result['chains']


def test_modal_number_does_not_agree_with_antecedent(adapter):
    t='pueri currunt in parte secreta locare debemus quae cantat'.split()
    result=infer(t,[1,6,8],7,8,adapter,nonfinite=True,object_frames=False)
    assert signature(result)==[(3,5,6)]


def reading(pos,**features):return MorphAnalysis(pos,tuple(sorted(features.items())))

class TinyAdapter(LatinAdapter):
    def __init__(self,lattice):self.lattice=lattice
    def analyze(self,word):return self.lattice.get(word,())


def test_unknown_gender_must_bind_once_across_modifiers():
    noun=reading('N',Case='NOM',Gender='X',Number='S')
    a=TinyAdapter({'head':(noun,), 'fem':(reading('ADJ',Case='NOM',Gender='F',Number='S'),),
        'masc':(reading('ADJ',Case='NOM',Gender='M',Number='S'),)})
    assert noun_phrases(['head','fem','masc','quae'],3,0,noun,a)==[]


def test_common_gender_and_relative_share_binding():
    noun=reading('N',Case='NOM',Gender='C',Number='S')
    female=reading('ADJ',Case='NOM',Gender='F',Number='S')
    a=TinyAdapter({'head':(noun,),'modifier':(female,)})
    phrases=noun_phrases(['head','modifier','quae'],2,0,noun,a,
        pronoun=reading('PRON',Case='NOM',Gender='F',Number='S'))
    assert phrases and all(p['agreement']['Gender']=='F' for p in phrases)
    assert not noun_phrases(['head','modifier','qui'],2,0,noun,a,
        pronoun=reading('PRON',Case='NOM',Gender='M',Number='S'))


def test_independent_checker_rejects_mixed_unknown_gender():
    from dataclasses import asdict
    from benchmarks.grammar_relative_constituents_iteration15_validate import check_witness
    noun=reading('N',Case='NOM',Gender='X',Number='S')
    fem=reading('ADJ',Case='NOM',Gender='F',Number='S')
    masc=reading('ADJ',Case='NOM',Gender='M',Number='S')
    pron=reading('PRON',Case='NOM',Gender='X',Number='S')
    verb=reading('V',Mood='IND',Voice='ACTIVE',Number='S',Person='3',VerbKind='INTRANS')
    a=TinyAdapter({'head':(noun,), 'fem':(fem,), 'masc':(masc,), 'quae':(pron,), 'cantat':(verb,), 'ridet':(verb,)})
    witness={'antecedent':0,'via':None,'parent':5,'noun':asdict(noun),'pronoun':asdict(pron),
        'child_verb':asdict(verb),'parent_verb':asdict(verb),'subject':None,
        'phrase':{'start':0,'end':3,'argument_preposition':None,
            'analyses':{'0':asdict(noun),'1':asdict(fem),'2':asdict(masc)}},
        'relative_role':'subject','governing_role':'subject'}
    with pytest.raises(AssertionError):check_witness(['head','fem','masc','quae','cantat','ridet'],[4,5],3,4,witness,a,False)


def test_independent_checker_rejects_wrong_argument_role(adapter):
    from copy import deepcopy
    from benchmarks.grammar_relative_constituents_iteration15_validate import check_witness
    result,_=probe(adapter,PROBES[0],nonfinite=True,object_frames=True)
    witness=deepcopy(result['chains'][0]);witness['governing_role']='object'
    t=PROBES[0][1].split()
    with pytest.raises(AssertionError):check_witness(t,[1,5,7],4,5,witness,adapter,True)


def test_plural_object_and_relative_instrument_with_singular_governors(adapter):
    from benchmarks.grammar_relative_constituents_iteration15_validate import check_witness
    # A dictionary-covered parallel to the natural aluearia case, not a repair
    # of that source token. Neither singular verb agrees with the plural object.
    t='pueri currunt agricola accedit habens noua animalia praeparata quibus excipiatur'.split()
    result=infer(t,[1,3,9],8,9,adapter,nonfinite=True,object_frames=True)
    assert signature(result)==[(6,4,3)]
    for witness in result['chains']:
        assert witness['relative_role']=='passive_instrument'
        assert dict(witness['noun']['features'])['Number']=='P'
        assert dict(witness['nonfinite_verb']['features'])['Number']=='S'
        check_witness(t,[1,3,9],8,9,witness,adapter,True)
