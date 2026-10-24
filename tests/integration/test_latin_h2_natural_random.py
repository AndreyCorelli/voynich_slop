from benchmarks.latin_h2_natural_random import random_encrypt
from benchmarks.latin_h2_natural_context import evaluate_holdouts

KEY = {'a': ['qq', 'qr'], 'b': ['qs', 'qt']}


def test_random_choices_are_reproducible_valid_and_not_forced_balanced():
    cipher = random_encrypt(['a'*12, 'abba'], KEY, 11401)
    assert cipher == random_encrypt(['a'*12, 'abba'], KEY, 11401)
    assert all(code in KEY[letter] for word, encoded in zip(['a'*12, 'abba'], cipher) for letter, code in zip(word, encoded))
    # A predeclared seed demonstrates that this is not balanced or cyclic.
    assert cipher[0].count('qq') != 6
    assert any(a == b for a, b in zip(cipher[0], cipher[0][1:]))


def test_holdout_rng_is_independent_of_training_length():
    held = random_encrypt(['ab', 'ba'], KEY, 11501)
    random_encrypt(['ab']*100, KEY, 11401)
    assert random_encrypt(['ab', 'ba'], KEY, 11501) == held


def test_random_selection_can_leave_single_letter_code_unseen():
    train = random_encrypt(['a'], KEY, 1)
    held = random_encrypt(['a'], KEY, 0)
    key = {train[0][0]: 'a'}
    score = evaluate_holdouts(key, held, ['a'])
    assert score['covered'] == 0 and score['unseen'] == 1
