from collections import Counter
from benchmarks.shared_inventory_mechanisms import local_order
from benchmarks.boundary_mechanisms import encoder, decode


def blocks():
    return [{'folio':'a','start':start,'words':[list(w) for w in ('ay','qa','an','ca')]*8,'positions':[4]*32,'line_ids':['line']*32} for start in (0,32)]


def test_exact_inventory_is_preserved_per_block_not_only_folio():
    original=blocks(); local,_=local_order(original,{'y':'q','n':'c','a':'a'},42)
    for a,b in zip(original,local):
        assert Counter(map(''.join,a['words']))==Counter(map(''.join,b['words']))
        assert list(map(len,a['words']))==list(map(len,b['words'])) and a['positions']==b['positions']
        assert a['folio']==b['folio'] and a['start']==b['start']


def test_both_sources_share_encoding_keys_lengths_and_decode():
    plain=blocks(); local,_=local_order(plain,{'y':'q','n':'c'},42)
    a,ka=encoder(plain,33001,.0625); b,kb=encoder(local,33001,.0625)
    assert ka==kb and decode(a,ka)==plain and decode(b,kb)==local
    for x,y in zip(a,b): assert list(map(len,x['words']))==list(map(len,y['words']))
