import numpy as np
from voynich_smt.letter_discovery import ALPHABET,SPACE,pattern,encode_text,decode_text,language_model,trie,prepare,gram_positions,search,full_score


def test_permutation_pattern_invariance_and_roundtrip():
    key=np.random.default_rng(7).permutation(SPACE);text='puella puerum amat et rosa dormit'
    encrypted=''.join(' ' if c==' ' else ALPHABET[key[ALPHABET.index(c)]] for c in text)
    assert decode_text(encode_text(encrypted),np.argsort(key))==text
    assert [pattern(w) for w in encrypted.split()]==[pattern(w) for w in text.split()]


def test_incremental_archive_matches_full_objective_and_zero_weight_ablation():
    dictionary=['puella','puerum','amat','rosa','dormit'];nodes,terminal=trie(dictionary)
    words=['puella','puerum','amat','rosa','dormit'];cipher=encode_text(' '.join(words));prepared=prepare(words,dictionary);positions,counts=gram_positions(cipher,4);logs,_=language_model([words])
    init=np.arange(SPACE);scores=np.zeros(len(prepared['candidate_ids']));unknown=np.full(len(words),-8.)
    args=(cipher,init,logs,4,positions,counts,prepared['words'],prepared['lengths'],prepared['frequency'],nodes,terminal,prepared['ptr'],prepared['candidate_ids'])
    tail=(prepared['affected_words'],prepared['affected_word_counts'])
    first=search(*args,scores,unknown,*tail,0.,2000,29)
    second=search(*args,np.full_like(scores,-3.),unknown,*tail,0.,2000,29)
    assert np.array_equal(first[0],second[0]) and first[1]==second[1]
    enhanced=search(*args,scores,unknown,*tail,.1,2000,29)
    assert np.isclose(enhanced[1],full_score(cipher,enhanced[0],logs,4,prepared,nodes,terminal,scores,unknown,.1),atol=1e-8)
    assert sorted(enhanced[0].tolist())==list(range(SPACE))


def test_candidates_exclude_inconsistent_letter_equality_patterns():
    prepared=prepare(['abc','aba'],['est','non','sum','ibi'])
    actual={w:prepared['candidate_ids'][prepared['ptr'][i]:prepared['ptr'][i+1]].tolist() for i,w in enumerate(prepared['unique'])}
    assert actual=={'abc':[0,2],'aba':[1,3]}


def test_shape_pos_features_do_not_reveal_cipher_key():
    from benchmarks.latin_compact_cipher import features
    assert features(['puella','dormit'],0)==features(['axyzzb','cdefgh'],0)
