from benchmarks.grammar_anchor_transfer_iteration86 import cached_sentences,transfer_rows

def fixture():return {'a':[dict(word='in',pos='ADP',head=1,rel='case'),dict(word='urbe',pos='NOUN',head=None,rel='root')]}

def test_cached_conversion_preserves_all_words_heads():
    ss=cached_sentences(fixture(),['a'])
    assert len(ss)==1 and len(ss[0]['tokens'])==2
    assert ss[0]['tokens'][0]['head']==1

def test_no_source_pos_class_required_for_target_labels():
    ss=cached_sentences(fixture(),['a']);ss[0]['tokens'][1]['pos']='UNSEEN'
    pub,rows=transfer_rows(ss,{'in':'ADP'},'s',['ADP','NOUN'])
    assert len(rows)==2 and rows[1]['labels']['pp']
    assert pub[0]['tokens'][1]['tag']=='X'

def test_private_target_annotation_changes_do_not_change_public_features():
    ss=cached_sentences(fixture(),['a']);_,a=transfer_rows(ss,{'in':'ADP'},'s',[])
    for t in ss[0]['tokens']:t.update(pos='X',head=None,rel='root')
    _,b=transfer_rows(ss,{'in':'ADP'},'s',[])
    assert [r['features'] for r in a]==[r['features'] for r in b]
    assert not b[1]['labels']['pp']
