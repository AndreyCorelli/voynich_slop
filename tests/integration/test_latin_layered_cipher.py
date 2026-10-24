import json
from benchmarks import latin_layered_cipher as benchmark
from voynich_smt.data.corpus import write_json
from voynich_smt.language.word_automaton import WordAutomaton


def test_shared_key_repeats_and_frozen_holdout(tmp_path, monkeypatch):
    monkeypatch.setattr(benchmark, 'OUT', tmp_path)
    a = WordAutomaton.from_sorted(['ab', 'aba', 'ba'])
    monkeypatch.setattr(benchmark.compact, 'load_automaton', lambda _: a)
    p = {'case': {'automaton': {}, 'alphabet': {'symbols': list('ab')}}, 'solver_ms': 2000,
         'train_cipher': [['uu','uv'], ['uu','uv','uu']], 'held_cipher': ['uv','uu'],
         'truth': {'train': ['ab','aba'], 'held': 'ba'}}
    write_json(tmp_path / 'prepared.json', p); benchmark.worker()
    row = json.loads((tmp_path / 'result.json').read_text())
    assert row['status'] == 'SAT' and row['verified']
    assert row['training_exact'] == 2 and row['held_exact'] and row['held_word'] == 'ba'
    assert row['recovered_key'] == {'uu': 'a', 'uv': 'b'}
