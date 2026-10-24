from collections import Counter
import pytest
from benchmarks.latin_h2_choice import balanced_random, random_choice
from benchmarks.latin_h2_identifiability import encrypt


def test_balanced_choice_preserves_key_counts_and_fixed_holdouts():
    train=['abb','aca','abb','aca']; held=['cab']
    key={'a':['aa','ab'],'b':['ba','bb'],'c':['ca','cb']}
    cipher,held_cipher=encrypt(train,held,key)
    random=balanced_random(train,key,19101)
    assert random==balanced_random(train,key,19101) and random!=cipher
    assert Counter(c for w in random for c in w)==Counter(c for w in cipher for c in w)
    inverse={code:letter for letter,codes in key.items() for code in codes}
    assert [''.join(inverse[c] for c in w) for w in random]==train
    fixture={'truth':{'train':train,'held':held,'key':key},'arms':{'positive':cipher,'shuffle':[]},'held_cipher':held_cipher,'shuffle_seed':9301}
    changed=random_choice(fixture,19101)
    assert changed['truth']==fixture['truth'] and changed['held_cipher']==held_cipher
    assert fixture['arms']['positive']==cipher


def test_odd_letter_totals_rejected():
    with pytest.raises(ValueError): balanced_random(['a'],{'a':['aa','ab']},1)
