import string
from benchmarks.character_prediction import fit, probability, score, letter_shuffle, BASE_SPECS, BOS, EOS


def block(words):
    return {'folio':'f','start':0,'words':[list(w) for w in words],'positions':list(range(len(words))),'line_ids':['a']*len(words)}


def test_nonempty_word_and_termination_probabilities_normalize():
    model=fit([block(['ab','ab','ac'])],BASE_SPECS['char-2-10'])
    for history in ([BOS,BOS],[BOS,'a'],['a','b']):
        symbols=list(string.ascii_lowercase)+([] if history[-1]==BOS else [EOS])
        assert abs(sum(probability(c,history,model) for c in symbols)-1)<1e-12
    assert probability(EOS,[BOS,BOS],model)==0 and probability(EOS,['a','b'],model)>0


def test_novel_words_and_unseen_glyphs_receive_distinct_full_scores():
    model=fit([block(['ab','ab'])],BASE_SPECS['char-2-10'])
    scores=score(block(['az','azz']),model)
    assert all(r['novel'] for r in scores)
    assert scores[0]['loss']!=scores[1]['loss'] and all(r['loss']>0 for r in scores)


def test_iid_invariant_to_internal_character_permutation():
    b=block(['abcd','abca','ddca']); model=fit([b],BASE_SPECS['char-iid'])
    shuffled=letter_shuffle(b,3)
    assert abs(sum(r['loss'] for r in score(b,model))-sum(r['loss'] for r in score(shuffled,model)))<1e-12


def test_position_and_suffix_probability_normalize_at_first_glyph():
    b=block(['ab','ac','ab','ac']); spec={**BASE_SPECS['char-1-10'],'position':4,'gate':'within'}; model=fit([b],spec)
    assert abs(sum(probability(c,[BOS,BOS],model,b,1) for c in string.ascii_lowercase)-1)<1e-12
