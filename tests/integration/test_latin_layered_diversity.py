import json
import pytest
from benchmarks import latin_layered_diversity as benchmark
from voynich_smt.data.corpus import write_json
from voynich_smt.language.word_automaton import WordAutomaton


@pytest.mark.parametrize('arm', ['positive', 'shuffle'])
def test_worker_shared_key_and_positive_only_scores(tmp_path, monkeypatch, arm):
    monkeypatch.setattr(benchmark, 'OUT', tmp_path)
    a = WordAutomaton.from_sorted(['ab', 'aba', 'ba'])
    monkeypatch.setattr(benchmark.compact, 'load_automaton', lambda _: a)
    words = [['uu','uv'], ['uu','uv','uu']]
    p = {'case': {'automaton': {}, 'alphabet': {'symbols': list('ab')}}, 'solver_ms': 2000,
         'arms': {'positive': words, 'shuffle': words}, 'held_cipher': [['uv','uu']],
         'truth': {'train': ['ab','aba'], 'held': ['ba']}}
    write_json(tmp_path / 'prepared.json', p); benchmark.worker(arm)
    row = json.loads((tmp_path / f'{arm}-result.json').read_text())
    assert row['status'] == 'SAT' and row['verified']
    if arm == 'positive': assert row['training_exact'] == 2 and row['held_exact'] == 1
    else: assert 'training_exact' not in row and 'held_exact' not in row
