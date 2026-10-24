import hashlib
import json
import pytest
from benchmarks import latin_pattern_natural_ambiguity as benchmark
from voynich_smt.data.corpus import write_json
from voynich_smt.language.word_automaton import WordAutomaton


@pytest.mark.parametrize('alternate', [False, True])
def test_used_key_exclusion_detects_unique_or_alternate_key(tmp_path, monkeypatch, alternate):
    monkeypatch.setattr(benchmark, 'OUT', tmp_path / 'run')
    monkeypatch.setattr(benchmark.compact, 'OUT', tmp_path / 'source')
    words = ['ab','aba','ba'] + (['xy','xyx','yx'] if alternate else [])
    words.sort(); a = WordAutomaton.from_sorted(words)
    monkeypatch.setattr(benchmark.compact, 'load_automaton', lambda _: a)
    monkeypatch.setattr(benchmark.compact, 'inventory_lines', lambda _: iter(words))
    inventory = tmp_path / 'inventory'; inventory.write_bytes(b'fixture')
    write_json(benchmark.compact.OUT / 'prepared.json', {'inventories': {'through-medieval-rare': {'inventory':
        {'path': str(inventory), 'sha256': hashlib.sha256(b'fixture').hexdigest()}}}})
    p = {'case': {'mode': 'through-medieval-rare', 'automaton': {}, 'alphabet': {'symbols': list('abxy' if alternate else 'ab')}},
         'solver_ms': 2000, 'arms': {'positive': [['uu','uv'], ['uu','uv','uu']]},
         'held_cipher': [['uv','uu']], 'truth': {'train': ['ab','aba'], 'held': ['ba']},
         'excluded_key': {'uu': 'a', 'uv': 'b'}}
    write_json(benchmark.OUT / 'prepared.json', p); benchmark.fit('positive')
    row = json.loads((benchmark.OUT / 'positive-result.json').read_text())
    assert row['status'] == ('SAT' if alternate else 'UNSAT')
    if alternate: assert row['verified'] and row['recovered_key'] != p['excluded_key']
