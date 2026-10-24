from voynich_smt.decoder_confusions import matched_pairs,same_child_contrasts


def record(stream,child,parent,distance,gap=1,author='a'):
    return {'stream':stream,'child':child,'parent':parent,'left':min(child,parent),'right':max(child,parent),
        'token_distance':distance,'predicate_gap':gap,'distance_bucket':distance.bit_length()-1,'author':author}


def test_matching_controls_author_gap_and_distance_without_reusing_positives():
    p=[record(0,1,2,8),record(1,1,2,14),record(2,1,2,8,author='b')]
    n=[record(3,1,2,9),record(4,1,2,10),record(5,1,2,11),record(6,1,2,8,gap=2)]
    result=matched_pairs(p,n)
    assert [r['positive_index'] for r in result['matches']]==[0,1]
    assert result['unmatched_negative_indices']==[2,3]
    assert result['unused_positive_indices']==[2]


def test_same_child_controls_are_separate_from_pool_matching():
    p=[record(0,1,2,8),record(1,1,2,8)]
    n=[record(0,1,3,12),record(1,4,3,8)]
    result=same_child_contrasts(p,n)
    assert len(result)==1 and result[0]['distance_matched']
    assert result[0]['positive']['child']==result[0]['negative']['child']
