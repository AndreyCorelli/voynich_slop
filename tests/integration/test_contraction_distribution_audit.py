from fractions import Fraction
from benchmarks.contraction_distribution_audit import envelope,window_hist


def test_optimistic_removal_matches_independent_quantile_integral():
    a={1:2,4:1,7:2}; b={2:2,5:1}; result=envelope(a,b)
    boundaries=sorted({Fraction(0),Fraction(1),Fraction(2,5),Fraction(3,5),Fraction(2,3)})
    def value(hist,q):
        total=sum(hist.values()); acc=0
        for length,count in sorted(hist.items()):
            acc+=count
            if q<Fraction(acc,total): return length
    expected=sum((z-x)*max(value(a,(x+z)/2)-value(b,(x+z)/2),0) for x,z in zip(boundaries,boundaries[1:]))
    assert abs(result['minimum_extra_unit_removal_per_item']-float(expected))<1e-12


def test_shorttail_deficit_exists_even_with_lower_mean():
    result=envelope({3:10},{1:5,6:5})
    assert result['maximum_short_item_fraction_deficit']==.5
    assert result['minimum_extra_unit_removal_per_item']==1


def test_windows_do_not_bridge_barriers_or_segments():
    segments=[['a']*21+[None]+['a']*22,['a']*21]
    assert window_hist(segments,{'a':1})=={22:1}
