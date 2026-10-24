from collections import Counter
from benchmarks.latin_h2_identifiability import encrypt
from benchmarks.latin_h2_layout import two_pass


def test_layout_changes_code_associations_but_keeps_matching_targets():
    types=['ab','ac','bb']; train=[w for w in types for _ in range(2)]
    held=['ca']; key={'a':['aa','ab'],'b':['ba','bb'],'c':['ca','cb']}
    cipher,held_cipher=encrypt(train,held,key)
    fixture={'truth':{'train':train,'held':held,'key':key},'arms':{'positive':cipher,'shuffle':[]},'held_cipher':held_cipher,'shuffle_seed':8301,
             'case':{'alphabet':{'symbols':list('abc')}},'inventory':{'word_count':9}}
    changed=two_pass(fixture)
    assert changed['truth']['train']==types*2
    assert changed['arms']['positive']!=cipher
    assert changed['held_cipher']==held_cipher
    assert Counter(changed['truth']['train'])==Counter(train)
    assert changed['case']==fixture['case'] and changed['inventory']==fixture['inventory']
    assert changed['truth']['key']==key
    assert fixture['truth']['train']==train
