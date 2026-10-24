from dataclasses import asdict
from itertools import product
import pytest
from benchmarks import small_varied_length_controls as b
from voynich_smt.data.corpus import digest
from voynich_smt.solver.recovery import Recovery


@pytest.mark.parametrize('profile',b.PROFILES)
@pytest.mark.parametrize('seed',b.SEEDS)
def test_keys_are_reproducible_prefix_free_and_genuinely_varied(profile,seed):
    symbols=tuple('abcdefghijklmn');glyphs=tuple('uvwxyz')
    encoder=b.key(symbols,glyphs,profile,seed)
    assert encoder==b.key(symbols,glyphs,profile,seed)
    codes=[cs[0] for cs in encoder.codebook.values()]
    assert len(set(codes))==len(symbols)
    assert not any(a!=c and c[:len(a)]==a for a,c in product(codes,codes))
    assert set(map(len,codes))=={'fixed-two':{2},'mixed-one-two':{1,2},'mixed-one-two-three':{1,2,3}}[profile]


def test_arm_inputs_holdout_isolation_resume_and_unknown(tmp_path,monkeypatch):
    monkeypatch.setattr(b,'OUT',tmp_path);known=[];hidden=[]
    def known_spy(plain,q):
        known.append((plain,q));return Recovery('UNKNOWN',0.01,reason_unknown='forced')
    def hidden_spy(q):
        hidden.append(q);return Recovery('UNKNOWN',0.01,reason_unknown='forced')
    monkeypatch.setattr(b,'known_solve',known_spy);monkeypatch.setattr(b,'recover_observed_codes',hidden_spy)
    r=b.run();p=b.prepare()
    assert len(known)==len(hidden)==6
    for (plain,q),hidden_q,case in zip(known,hidden,p['cases']):
        assert q==hidden_q and q.timeout_ms==5000
        assert digest(asdict(q))==digest(case['request'])
        assert digest(asdict(plain))==digest(case['truth']['plaintext'])
    assert all(a['evaluation_status']=='NOT_EVALUATED_NO_SAT' and 'prediction' not in a for a in r['arms'])
    assert digest(b.run())==digest(r) and len(hidden)==6
    b.validate()
