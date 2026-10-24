from types import SimpleNamespace
from benchmarks import latin_form_inventory as b


def test_generation_independent_matching_and_enclitic_rules():
    # Bootstrap the pinned matcher without passing a target query to generation.
    b.morphology.parser('upstream-default')
    stem={'orth':'ros','pos':'N','stem_number':1,'n':[1,1],'form':['F'],'wid':1}
    inflection={'ending':'a','pos':'N','stem':1,'n':[1,1],'form':['NOM','S','F']}
    wrong=dict(inflection,ending='us',form=['NOM','S','M'])
    data=SimpleNamespace(stems={'ros':[stem]},inflects={'1':{'a':[inflection]},'2':{'us':[wrong]}},wordkeys=set(),empty={},uniques={},
                         addons={'tackons':[{'orth':'que','pos':'X'},{'orth':'est','pos':'PRON'}],'packons':[],'not_packons':[]},lookup_stem=lambda _: {'parts':['rosa']})
    words,stats=b.enumerate_forms(SimpleNamespace(data=data))
    assert words=={'rosa','rosaque'} and stats['base_forms']==1


def test_coverage_counts_occurrences_in_canonical_spelling():
    source={'fixed_passage':{'plaintext':{'words':[list('via'),list('x'),list('x')]},'holdout_plaintext':{'words':[list('via')]}},'grid_windows':[{'words':[list('via')]}]}
    audit=b.audit({'uia'},source)
    assert audit['training']['missing_occurrences']==2 and audit['holdout']['missing_occurrences']==0
    assert audit['grid']['at_most_one_missing']==1
