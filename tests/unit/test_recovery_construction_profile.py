import pstats
import pytest
import z3
from benchmarks import recovery_construction_profile as b
from voynich_smt.solver.recovery import Recovery


def test_profile_stops_before_solver_check_and_restores_method():
    sentinel=object();method=z3.Solver.check
    def solve(q):
        assert q is sentinel
        solver=z3.Solver();x=z3.Int('profile_test_x');solver.add(x==1)
        assert solver.check()==z3.sat
        return Recovery('UNKNOWN',0.01,reason_unknown='test')
    result,profile,wall=b.profile_construction(sentinel,solve)
    assert z3.Solver.check is method and result.status=='UNKNOWN' and wall>0
    functions=pstats.Stats(profile).stats
    assert any(name=='add' for file,line,name in functions)
    assert not any(name=='Z3_solver_check' or (name=='check' and file.endswith('/z3/z3.py')) for file,line,name in functions)
    assert b.summarize(profile)['total_calls']>0


def test_instrumentation_restored_on_construction_failure():
    method=z3.Solver.check
    def fail(q):raise ValueError('construction failed')
    with pytest.raises(ValueError,match='construction failed'):b.profile_construction(object(),fail)
    assert z3.Solver.check is method


def test_unexpected_check_count_rejected():
    with pytest.raises(RuntimeError,match='exactly one'):b.profile_construction(object(),lambda q:Recovery('UNKNOWN',0))
