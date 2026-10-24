import hashlib
import json
import pytest
from benchmarks import latin_h2_public as benchmark
from voynich_smt.data.corpus import write_json
from voynich_smt.language.word_automaton import WordAutomaton


@pytest.mark.parametrize('too_many', [False, True])
def test_shared_inverse_allows_two_codes_but_rejects_three(tmp_path, monkeypatch, too_many):
    monkeypatch.setattr(benchmark, 'OUT', tmp_path / 'run')
    monkeypatch.setattr(benchmark.compact, 'OUT', tmp_path / 'source')
    words = ['aaa','ba'] if too_many else ['aba','ba']
    a = WordAutomaton.from_sorted(words)
    monkeypatch.setattr(benchmark.compact, 'load_automaton', lambda _: a)
    monkeypatch.setattr(benchmark.compact, 'inventory_lines', lambda _: iter(words))
    path = tmp_path / 'inventory'; path.write_bytes(b'fixture')
    write_json(benchmark.compact.OUT / 'prepared.json', {'inventories': {'upstream-default': {'inventory':
        {'path': str(path), 'sha256': hashlib.sha256(b'fixture').hexdigest()}}}})
    p = {'case': {'mode': 'upstream-default', 'automaton': {}, 'alphabet': {'symbols': list('ab')}},
         'solver_ms': 2000, 'max_homophones': 2, 'arms': {'positive': [['uu','uv','uw']]},
         'held_cipher': [['uv','uu']], 'truth': {'train': ['aba'], 'held': ['ba']}}
    write_json(benchmark.OUT / 'prepared.json', p); benchmark.fit('positive')
    row = json.loads((benchmark.OUT / 'positive-result.json').read_text())
    assert row['status'] == ('UNSAT' if too_many else 'SAT')
    if not too_many:
        assert row['verified'] and row['held_exact'] == 1
        assert row['recovered_key']['uu'] == row['recovered_key']['uw'] == 'a'


def test_global_capacity_across_separate_words(tmp_path, monkeypatch):
    monkeypatch.setattr(benchmark, 'OUT', tmp_path / 'run')
    monkeypatch.setattr(benchmark.compact, 'OUT', tmp_path / 'source')
    words = ['a']; a = WordAutomaton.from_sorted(words)
    monkeypatch.setattr(benchmark.compact, 'load_automaton', lambda _: a)
    monkeypatch.setattr(benchmark.compact, 'inventory_lines', lambda _: iter(words))
    path = tmp_path / 'inventory'; path.write_bytes(b'fixture')
    write_json(benchmark.compact.OUT / 'prepared.json', {'inventories': {'upstream-default': {'inventory':
        {'path': str(path), 'sha256': hashlib.sha256(b'fixture').hexdigest()}}}})
    p = {'case': {'mode': 'upstream-default', 'automaton': {}, 'alphabet': {'symbols': list('ab')}},
         'solver_ms': 2000, 'max_homophones': 2,
         'arms': {'positive': [['uu'], ['uv'], ['uw']]}, 'held_cipher': [['uu']],
         'truth': {'train': ['a','a','a'], 'held': ['a']}}
    write_json(benchmark.OUT / 'prepared.json', p); benchmark.fit('positive')
    row = json.loads((benchmark.OUT / 'positive-result.json').read_text())
    assert row['candidate_counts'] == [1,1,1] and row['status'] == 'UNSAT'
