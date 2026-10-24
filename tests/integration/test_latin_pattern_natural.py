import hashlib
import json
from benchmarks import latin_pattern_natural as benchmark
from voynich_smt.data.corpus import write_json
from voynich_smt.language.word_automaton import WordAutomaton


def test_worker_filters_selected_inventory_and_scores_novel_holdout(tmp_path, monkeypatch):
    monkeypatch.setattr(benchmark, 'OUT', tmp_path / 'run')
    monkeypatch.setattr(benchmark.compact, 'OUT', tmp_path / 'source')
    words = ['ab','aba','ba']; a = WordAutomaton.from_sorted(words)
    monkeypatch.setattr(benchmark.compact, 'load_automaton', lambda _: a)
    inventory = tmp_path / 'inventory'; inventory.write_bytes(b'fixture')
    def lines(path):
        assert path == str(inventory)
        return iter(words)
    monkeypatch.setattr(benchmark.compact, 'inventory_lines', lines)
    write_json(benchmark.compact.OUT / 'prepared.json', {'inventories': {'through-medieval-rare': {'inventory':
        {'path': str(inventory), 'sha256': hashlib.sha256(b'fixture').hexdigest()}}}})
    p = {'case': {'mode': 'through-medieval-rare', 'automaton': {}, 'alphabet': {'symbols': list('ab')}},
         'solver_ms': 2000, 'arms': {'positive': [['uu','uv'], ['uu','uv','uu']]},
         'held_cipher': [['uv','uu']], 'truth': {'train': ['ab','aba'], 'held': ['ba']}}
    write_json(benchmark.OUT / 'prepared.json', p); benchmark.fit('positive')
    row = json.loads((benchmark.OUT / 'positive-result.json').read_text())
    assert row['status'] == 'SAT' and row['verified'] and row['held_exact'] == 1
