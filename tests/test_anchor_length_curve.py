from voynich_smt.anchor_length_curve import supported_words,length_blocks,curve_metrics,aggregate


def test_support_needs_occurrences_and_distinct_sentences_without_pos():
    sentences=[dict(sent_id=str(i),tokens=[dict(word='a') for _ in range(3)]+[dict(word='b')]) for i in range(3)]
    assert supported_words(sentences,['a','b'])=={'a'}
    assert supported_words(sentences[:2],['a','b'])==set()


def test_length_levels_keep_same_ids_and_merge_disjoint_blocks():
    hundred={f'sparse{i}':[str(100*i+j) for j in range(100)] for i in range(8)}
    blocks=length_blocks(dict(scored=dict(hundred,full=[str(j) for j in range(829)])))
    assert len(blocks)==16
    for n in (100,200,400,800):
        level=[ids for key,ids in blocks.items() if key.startswith(str(n)+'-')]
        assert all(len(ids)==n for ids in level)
        assert sorted(s for ids in level for s in ids)==sorted(str(j) for j in range(800))


def test_raw_ranking_is_separate_from_gain_threshold_recommendation():
    pairs=[dict(pair=['a','b'],gain=.2,supported=True),dict(pair=['c','d'],gain=.1,supported=True)]
    r=curve_metrics(pairs,dict(pair=['a','b'],error=True),.6)
    assert r['abstain'] and r['rank1_correct']==1 and r['hit']==0
    a=aggregate([r]);assert a['reference_supported']==1 and a['recall']==0 and a['precision'] is None
