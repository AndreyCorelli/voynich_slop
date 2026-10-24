from benchmarks.latin_h2_natural_context import prepend_cipher, evaluate_holdouts
from benchmarks.latin_h2_identifiability import encrypt

KEY = {'a': ['qq', 'qr'], 'b': ['qs', 'qt']}


def test_prefix_alignment_preserves_old_cipher_even_with_odd_counts():
    train, held = ['ab', 'aba'], ['ba', 'ab']
    original, original_held = encrypt(train, held, KEY)
    extended, extended_held = prepend_cipher(['a', 'bb', 'ab'], train, held, KEY)
    assert extended[3:] == original and extended_held == original_held
    assert all(c in KEY[l] for word, cipher in zip(['a', 'bb', 'ab']+train, extended) for l, c in zip(word, cipher))
    # Prefix phases may begin on code 1; they finish at code 0 for every letter.
    assert extended[0] == ['qq']  # two preceding a occurrences in total


def test_unseen_holdout_is_not_scored_as_incorrect():
    result = evaluate_holdouts({'qq': 'a', 'qs': 'b'}, [['qq', 'qs'], ['qr', 'qs']], ['ab', 'ab'])
    assert result['covered'] == 1 and result['unseen'] == 1 and result['exact_covered'] == 1
    assert result['words'][1] == {'status': 'UNSEEN_CODE', 'missing_codes': ['qr']}


def test_seen_wrong_key_is_scored_without_truth_rescue():
    result = evaluate_holdouts({'qq': 'b', 'qs': 'a'}, [['qq', 'qs']], ['ab'])
    assert result['covered'] == 1 and result['exact_covered'] == 0
    assert result['words'][0]['word'] == 'ba'
