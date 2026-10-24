import json
import pytest
from benchmarks import latin_layered_lengths as benchmark
from voynich_smt.data.corpus import write_json
from voynich_smt.language.word_automaton import WordAutomaton


@pytest.mark.parametrize('length,prefix,expected', [(2, '', 'SAT'), (3, '', 'SAT'), (2, 'aa', 'UNSAT'), (3, 'bb', 'UNSAT')])
def test_worker_variable_lengths_and_impossible_prefix(tmp_path, monkeypatch, length, prefix, expected):
    monkeypatch.setattr(benchmark, 'OUT', tmp_path)
    automaton = WordAutomaton.from_sorted(['ab', 'aba', 'ba'])
    monkeypatch.setattr(benchmark.compact, 'load_automaton', lambda _: automaton)
    case = {'length': length, 'prefix': prefix, 'automaton': {}, 'alphabet': {'symbols': list('ab')}}
    write_json(tmp_path / 'prepared.json', {'cases': [case], 'solver_ms': 2000})
    benchmark.worker(0)
    row = json.loads((tmp_path / 'case-0.json').read_text())
    assert row['status'] == expected
    if expected == 'SAT':
        assert row['verified'] and len(row['word']) == length and automaton.accepts(row['word'])
