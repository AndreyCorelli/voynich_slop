import json
from benchmarks import latin_layered_timeout as benchmark
from voynich_smt.data.corpus import digest, write_json
from voynich_smt.language.word_automaton import WordAutomaton


def test_worker_persists_phase_timings_and_independent_witness(tmp_path, monkeypatch):
    monkeypatch.setattr(benchmark, 'OUT', tmp_path)
    a = WordAutomaton.from_sorted(['ab', 'ba'])
    monkeypatch.setattr(benchmark.compact, 'load_automaton', lambda _: a)
    p = {'case': {'length': 2, 'automaton': {}, 'alphabet': {'symbols': list('ab')}}, 'solver_ms': 2000}
    write_json(tmp_path / 'prepared.json', p)
    benchmark.worker()
    row = json.loads((tmp_path / 'result.json').read_text())
    phases = json.loads((tmp_path / 'phases.json').read_text())
    assert row['status'] == 'SAT' and row['verified'] and a.accepts(row['word'])
    assert phases['phase'] == 'complete' and phases['prepared_sha256'] == digest(p)
    assert phases['timings'] == row['timings']
    assert set(row['timings']) == {'load_seconds', 'construction_seconds', 'solver_seconds', 'verification_seconds'}
    assert all(value >= 0 for value in row['timings'].values())
