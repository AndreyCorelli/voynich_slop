from copy import deepcopy
from voynich_smt.predicate_projection import project_sentence,projection_changes


def sentence(tokens,upos,heads,finite,relative=()):
    return {'sent_id':'synthetic','tokens':tokens,'upos':upos,'heads':heads,'finite':finite,
        'features':[{'PronType':'Rel'} if i in relative else {} for i in range(len(tokens))],
        'parents':{},'relations':{},'markers':{},'anchors':[None]*len(tokens)}


def test_nested_passives_route_relative_and_si_to_local_auxiliary():
    # si factae fuissent virtutes quae factae sunt mansissent
    s=sentence('si factae fuissent virtutes quae factae sunt mansissent'.split(),
        ['SCONJ','VERB','AUX','NOUN','PRON','VERB','AUX','VERB'],[1,7,1,1,5,3,5,None],[2,6,7],relative=[4])
    before=deepcopy(s);r=project_sentence(s,['mark','advcl','aux:pass','nsubj:pass','nsubj:pass','acl','aux:pass','root'])
    assert r['parents']=={2:7,6:2,7:None}
    assert r['markers']=={0:{'target':2,'kind':'subordination'},4:{'target':6,'kind':'relative'}}
    assert r['anchors'][1]==2 and r['anchors'][5]==6
    assert s==before and r['finite']==s['finite'] and r['tokens']==s['tokens']


def test_coordination_uses_complex_outward_relation():
    s=sentence(['dicit','et','facta','est'],['VERB','CCONJ','VERB','AUX'],[None,2,0,2],[0,3])
    r=project_sentence(s,['root','cc','conj','aux:pass'])
    assert r['parents']=={0:None,3:0} and r['relations'][3]=='coordination'
    assert r['markers'][1]=={'target':3,'kind':'coordination'}


def test_unique_nonverbal_copula_is_a_clause_representative():
    s=sentence(['qui','bonus','est','dicit'],['PRON','ADJ','AUX','VERB'],[1,3,1,None],[2,3],relative=[0])
    r=project_sentence(s,['nsubj','ccomp','cop','root'])
    assert r['parents']=={2:3,3:None} and r['markers'][0]['target']==2


def test_ambiguous_finite_auxiliaries_are_not_arbitrarily_collapsed():
    s=sentence(['facta','est','sit','dicit'],['VERB','AUX','AUX','VERB'],[3,0,0,None],[1,2,3])
    r=project_sentence(s,['ccomp','aux:pass','aux:pass','root'])
    assert not r['predicate_complexes']
    assert r['projection_issues'][0]['kind']=='multiple_finite_auxiliaries'
    assert r['parents']=={1:3,2:3,3:None}


def test_finite_head_with_finite_auxiliary_is_explicitly_unsupported():
    s=sentence(['dicit','est'],['VERB','AUX'],[None,0],[0,1])
    r=project_sentence(s,['root','aux'])
    assert not r['predicate_complexes'] and r['projection_issues'][0]['kind']=='finite_head_with_finite_auxiliary'
    assert r['parents']=={0:None,1:0}


def test_saved_13305_regression_preserves_tokens_and_finite_positions():
    from benchmarks.grammar_markers_iteration5 import marker_sentences,TREEBANKS
    path=TREEBANKS/'proiel-r2.17/la_proiel-ud-train.conllu'
    records,_=marker_sentences(path,'proiel');s=next(s for s in records if s['sent_id']=='13305')
    block=next(b for b in path.read_text().split('\n\n') if '# sent_id = 13305\n' in b+'\n')
    deps=[l.split('\t')[7] for l in block.splitlines() if l and not l.startswith('#') and l.split('\t')[0].isdigit() and l.split('\t')[3]!='PUNCT']
    r=project_sentence(s,deps)
    assert s['tokens'][13]=='sunt' and s['tokens'][9]=='fuissent' and s['tokens'][17]=='mansissent'
    assert s['parents'][13]==17 and r['parents'][13]==9
    assert s['markers'][11]['target']==17 and r['markers'][11]['target']==13
    assert 5 not in s['markers'] and r['markers'][5]=={'target':9,'kind':'subordination'}
    assert s['tokens']==r['tokens'] and s['finite']==r['finite']
