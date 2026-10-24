from benchmarks.text_generation_comparison import one_edit, metrics, generate


def test_one_edit_insertion_deletion_substitution_and_exact():
    assert one_edit(tuple('abc'),tuple('ab')) and one_edit(tuple('ab'),tuple('abc'))
    assert one_edit(tuple('abc'),tuple('adc'))
    assert not one_edit(tuple('abc'),tuple('abc'))
    assert not one_edit(tuple('abc'),tuple('xyz'))


def test_global_metrics_survive_injective_relabeling():
    words=[tuple(w) for w in ('ab','ac','ab','dd')]
    a=metrics(words); b=metrics([tuple({'a':'X','b':'Y','c':'Z','d':'W'}[c] for c in w) for w in words])
    assert a==b


def test_local_copying_differs_from_global_frequency():
    a=metrics([('a',)]*16+[('b',)]*16)
    b=metrics([('a',),('b',)]*16)
    assert a['unique_ratio']==b['unique_ratio']
    assert a['adjacent_repeat']>b['adjacent_repeat']
    assert a['repeat_local_excess']>b['repeat_local_excess']


def test_homophones_do_not_leak_original_letter_equality():
    words=[tuple('aaaa')]*64
    h2=generate('natural-h2',{'words':[]},words,1)
    assert len(set(h2))>1 and all(len(w)==4 for w in h2)


def test_one_edit_against_independent_dynamic_program():
    from itertools import product
    words=[tuple(w) for n in range(1,4) for w in product('ab',repeat=n)]
    for a in words:
        for b in words:
            previous=list(range(len(b)+1))
            for i,x in enumerate(a,1):
                current=[i]
                for j,y in enumerate(b,1):
                    current.append(min(current[-1]+1,previous[j]+1,previous[j-1]+(x!=y)))
                previous=current
            assert one_edit(a,b)==(previous[-1]==1)
