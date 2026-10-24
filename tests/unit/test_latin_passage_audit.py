from benchmarks.latin_passage_proxy_audit import chunks


def test_blocks_preserve_sentences_and_discard_incomplete_tail():
    sentences=[{'words':['a']*n} for n in (90,100,80,50)]
    assert chunks(sentences,250)==[[0,1,2]]


def test_whole_work_retains_tail():
    sentences=[{'words':['a']*n} for n in (90,100,80,50)]
    assert chunks(sentences,'whole_work')==[[0,1,2,3]]


def test_large_sentence_is_not_dropped_or_counted_twice():
    sentences=[{'words':['a']*n} for n in (300,260,20)]
    assert chunks(sentences,250)==[[0],[1]]
