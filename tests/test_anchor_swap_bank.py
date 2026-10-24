from voynich_smt.anchor_swap_bank import remaining_bank
from benchmarks.grammar_anchor_swap_bank_iteration97 import compact,expand,delta_public,apply_delta,signature


def test_bank_is_exhaustive_and_excludes_previous_cross_pairs():
    anchors={'a':'ADP','b':'ADP','x':'CCONJ','y':'CCONJ'}
    previous={'known':{'a':'x','x':'a'},'same_adp':{'a':'b','b':'a'},'same_conjunction':{'x':'y','y':'x'}}
    bank=remaining_bank(anchors,previous)
    swaps=[m for k,m in bank.items() if k.startswith('swap_')]
    assert {frozenset(m) for m in swaps}=={frozenset(('a','y')),frozenset(('b','x')),frozenset(('b','y'))}
    assert bank['same_adp']==previous['same_adp'] and bank['correct']=={}


def test_compact_roundtrip_and_public_delta_preserve_opaque_groups():
    row=dict(sid='s',index=0,word='opaque',visible=True,labels={'pp':True},scores={'pooled_pos':{'pp':.75},'left':{'pp':.5},'prior':{'pp':.1}})
    ref=[{k:row[k] for k in ('sid','index','word','visible','labels')}]
    assert expand(ref,compact([row]))==[row]
    base=[dict(sent_id='s',tokens=[dict(id='opaque',anchor='a',tag='ADP'),dict(id='opaque',anchor='a',tag='ADP')])]
    other=apply_delta(base,{'opaque':['x','CCONJ']})
    assert apply_delta(base,delta_public(base,other))==other
    assert signature(base)!=signature(other)
    assert [t['id'] for t in other[0]['tokens']]==['opaque','opaque']
