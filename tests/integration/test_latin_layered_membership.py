import json
import pytest
from benchmarks import latin_layered_membership as benchmark
from voynich_smt.data.corpus import write_json
from voynich_smt.language.word_automaton import WordAutomaton


@pytest.mark.parametrize('kind', ['concrete', 'one-hidden-letter', 'all-hidden-letters'])
def test_worker_checks_actual_membership_and_fixed_letters(tmp_path, monkeypatch, kind):
    monkeypatch.setattr(benchmark, 'OUT', tmp_path)
    automaton = WordAutomaton.from_sorted(['amare', 'amere'])
    monkeypatch.setattr(benchmark.compact, 'load_automaton', lambda _: automaton)
    case = {'kind': kind, 'anchor': 'amare', 'automaton': {},
            'alphabet': {'symbols': list('aemr')}}
    write_json(tmp_path / 'prepared.json', {'cases': [case], 'solver_ms': 2000})
    benchmark.worker(0)
    row = json.loads((tmp_path / 'case-0.json').read_text())
    assert row['status'] == 'SAT' and row['verified'] and automaton.accepts(row['word'])
    if kind != 'all-hidden-letters':
        assert all(row['word'][i] == 'amare'[i] for i in (0, 1, 3, 4))
    if kind == 'concrete': assert row['word'] == 'amare'
