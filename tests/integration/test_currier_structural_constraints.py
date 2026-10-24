from collections import Counter
from benchmarks.currier_structural_constraints import extract,repeat_stats,summarize

def record(word,folio='f1r',locus='f1r.1,+P0',bad=False):
    return {'folio':folio,'locus':locus,'page_variables':{'L':'A'},'tokens':list(word),'excluded_reason':'bad' if bad else None}

def test_filters_and_windows_preserve_exclusion_and_folio_barriers():
    rs=[record('aa') for _ in range(22)]+[record('x',bad=True)]+[record('bb') for _ in range(22)]
    strict,runs,_=extract(rs,'whole-clean-lines');assert not strict['A'] and not runs['A']
    broad,runs,_=extract(rs,'clean-words');assert list(map(len,runs['A']))==[22,22]
    result=summarize(broad['A'],runs['A']);assert result['contiguous_22_word_windows']==2
    assert result['width_constraints']['fixed-2']['incompatible_word_occurrences']==0
    assert result['width_constraints']['fixed-3']['incompatible_word_occurrences']==44

def test_repetition_spectrum_and_monotone_splitting():
    r=repeat_stats([tuple('a'),tuple('a'),tuple('b'),tuple('b')])
    split=repeat_stats([tuple('x'),tuple('y'),tuple('z'),tuple('z')])
    assert r['frequency_spectrum']=={2:2} and r['repeat_pairs']==2
    assert split['repeat_pairs']<=r['repeat_pairs'] and split['types']>=r['types']
