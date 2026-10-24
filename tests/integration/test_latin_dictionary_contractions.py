from benchmarks.latin_dictionary_contractions import candidates
from benchmarks.latin_contractions import expand


def test_contractions_add_long_words_without_forcing_maximal_compression():
    rules = [{'id':'est','expansion':'est','position':'whole'},
             {'id':'per','expansion':'per','position':'any'}]
    assert candidates(['per'], 1, []) == []
    contracted = candidates(['per'], 1, rules)
    assert contracted[0]['compatible_counts'] == [1]
    assert expand(contracted[0]['witness_units'], rules) == 'per'
    # One contracted unit cannot emit four glyphs; spelling out letters can.
    optional = candidates(['est'], 4, rules)
    assert optional[0]['compatible_counts'] == [3]
    assert expand(optional[0]['witness_units'], rules) == 'est'


def test_scope_and_overlapping_units_do_not_create_invalid_capacity():
    rules = [{'id':'con','expansion':'con','position':'initial'},
             {'id':'on','expansion':'on','position':'any'}]
    assert candidates(['acon'], 2, rules) == []
    result = candidates(['con'], 1, rules)
    assert result[0]['compatible_counts'] == [1]
    assert expand(result[0]['witness_units'], rules) == 'con'
