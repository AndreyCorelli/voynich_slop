import json
import pytest
from benchmarks import latin_pattern_natural_context as benchmark
from voynich_smt.data.corpus import digest, write_json
from voynich_smt.language.word_automaton import WordAutomaton


@pytest.mark.parametrize('missing_prefix', [False, True])
def test_context_freezes_holdout_and_blocks_missing_prefix(tmp_path, monkeypatch, missing_prefix):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(benchmark, 'OUT', tmp_path / 'context')
    monkeypatch.setattr(benchmark.baseline, 'OUT', tmp_path / 'baseline')
    monkeypatch.setattr(benchmark.ambiguity, 'OUT', tmp_path / 'ambiguity')
    old = {'id': 'fixture', 'passage_index': 0, 'case': {'automaton': {}, 'alphabet': {'symbols': list('ab')}},
           'truth': {'train': ['ab','aba'], 'held': ['ba'], 'key': {'a':'uu','b':'uv'}},
           'held_cipher': [['uv','uu']]}
    source = {'fixtures': [old], 'passages': [{'record_start': 24}]}
    audit = {'fixture': 'frozen'}
    monkeypatch.setattr(benchmark.baseline, 'prepare', lambda: source)
    monkeypatch.setattr(benchmark.ambiguity, 'prepare', lambda: audit)
    monkeypatch.setattr(benchmark.compact, 'load_automaton', lambda _: WordAutomaton.from_sorted(['ab','aba','ba']))
    write_json(benchmark.baseline.OUT / 'report.json', {'complete': True, 'prepared_sha256': digest(source),
        'fixtures': {'fixture': {'positive': {'status': 'SAT', 'held_exact': 0}}}})
    write_json(benchmark.ambiguity.OUT / 'report.json', {'complete': True, 'prepared_sha256': digest(audit),
        'fixtures': {'fixture': {'positive': {'status': 'SAT'}}}})
    records = [{'tokens': list('aa' if missing_prefix else 'ab')} for _ in range(24)]
    write_json(tmp_path / 'data/processed/caesar-latin-v2.json', {'records': records})
    p = benchmark.prepare()
    assert p['contexts'][0]['prefix_start'] == 0 and len(p['contexts'][0]['prefix_records']) == 24
    if missing_prefix:
        assert not p['fixtures'] and not p['coverage_audits']['fixture']['admitted']
    else:
        f = p['fixtures'][0]
        assert f['held_cipher'] == old['held_cipher'] and f['truth']['held'] == old['truth']['held']
        assert len(f['truth']['train']) == 26 and f['truth']['train'][-2:] == old['truth']['train']
