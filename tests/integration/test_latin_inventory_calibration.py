from collections import Counter
from benchmarks import latin_inventory_calibration as b


def test_deterministic_controls_unavailable_and_invariants():
    c=b.controls(['a','aaaa','abc'],7)
    assert c==b.controls(['abc','aaaa','a'],7)
    assert c['unavailable_anagrams']==['a','aaaa']
    assert Counter(c['typewise_anagram']['abc']['word'])==Counter('abc')
    assert c['typewise_anagram']['abc']['word']!='abc'
    assert all(len(w)==len(v) for w,v in c['uniform_letters'].items())


def test_public_length_counts_not_true_lengths():
    scale=b.candidate_scale({1:5,2:7,3:11,4:13},[3,6])
    assert [r['candidate_words'] for r in scale['word_rows']]==[23,31]
    assert scale['total_membership_candidates']==54


def test_token_weights_separate_from_type_acceptance():
    c={'typewise_anagram':{'ab':{'word':'ba'},'cd':{'word':'dc'}},'uniform_letters':{'ab':'aa','cd':'cc'}}
    scored=b.acceptance({'ba','cc'},c,Counter({'ab':3,'cd':1}))
    assert scored['typewise_anagram']['accepted_types']==1 and scored['typewise_anagram']['accepted_grid_tokens']==3
    assert scored['uniform_letters']['accepted_grid_tokens']==1
