from benchmarks.latin_pattern_natural_long import select_passages
from benchmarks.latin_h2_identifiability import encrypt


def records(words):
    return [{'tokens':list(word),'excluded_reason':None} for word in words]


def test_passage_selection_is_contiguous_and_coverage_independent():
    words=['abc']*48+['ab','bc','ac','ab','bc','ac']
    chosen=select_passages(records(words*7),0,set('abc'),7)
    assert [(x['record_start'],x['record_end_exclusive']) for x in chosen]==[(i*54,(i+1)*54) for i in range(7)]
    assert all(x['train']==words[:48] and x['held']==words[48:] for x in chosen)


def test_cyclic_natural_holdout_can_require_unseen_homophone():
    train,held=encrypt(['ab'],['ab'],{'a':['qq','qr'],'b':['qs','qt']})
    assert {c for w in held for c in w}-{c for w in train for c in w}=={'qr','qt'}


def test_generation_has_no_added_duplicate_words():
    words=['ab','aba','ba']
    train,held=encrypt(words,['ab'],{'a':['qq','qr'],'b':['qs','qt']})
    assert list(map(len,train))==list(map(len,words))
    assert len(train)==3 and held==[['qq','qt']]
