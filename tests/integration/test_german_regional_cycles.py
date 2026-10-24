from dataclasses import dataclass
import json
from pathlib import Path

import pytest

from benchmarks import german_regional_cycles as regional
from benchmarks.german_selection import build_vocabulary
from voynich_smt.data.corpus import digest


def test_generalized_builder_preserves_recorded_kottanerin_vocabulary():
    recorded = json.loads(Path('data/generated/german-selection/vocabulary.json').read_text())
    assert digest(build_vocabulary()) == digest(recorded)


def test_default_sources_are_only_the_other_eight_dated_witnesses():
    assert regional.SOURCES == (123, 133, 143, 153, 223, 233, 243, 253)


@pytest.mark.parametrize('numbers,budget', [((), 30000), ((123, 123), 30000),
    ((113,), 30000), ((213,), 30000), ((123,), 0)])
def test_invalid_sources_and_budgets_are_rejected(numbers, budget):
    with pytest.raises(ValueError):
        regional.run(numbers, budget, prepare_only=True)


def install_small_sources(monkeypatch, tmp_path):
    monkeypatch.setattr(regional, 'ARTIFACTS', tmp_path/'inputs')
    def vocabulary(number):
        letter = 'a' if number == 123 else 'b'
        return {'words': [letter, letter*2], 'alphabet': [letter],
                'vocabulary_size': 2, 'token_count': 3,
                'source': {'xml_member': f'XML/{number}.xml'}, 'audit': {}}
    monkeypatch.setattr(regional, 'build_vocabulary', vocabulary)


def test_sources_are_kept_separate_and_long_budgets_have_separate_inputs(monkeypatch, tmp_path):
    install_small_sources(monkeypatch, tmp_path)
    short = regional.run((123, 133), output=tmp_path/'short.json', prepare_only=True)
    long = regional.run((123, 133), timeout_ms=1800000, output=tmp_path/'long.json', prepare_only=True)
    for row, other in zip(short['prepared_inputs'], long['prepared_inputs']):
        assert row['request']['selection'] == {'mode': 'cycle', 'reset': 'text'}
        assert row['public_input'] != other['public_input']
        words = row['request']['dictionary']['words']
        assert set(''.join(''.join(w) for w in words)) == ({'a'} if row['source_id'] == 123 else {'b'})


def test_checkpoint_resume_skips_finished_sources_and_rejects_tampering(monkeypatch, tmp_path):
    install_small_sources(monkeypatch, tmp_path)
    calls = []
    @dataclass
    class Unknown:
        status: str = 'UNKNOWN'
        verified: bool = False
        runtime_seconds: float = 0.01
    def solve(request):
        calls.append(request)
        return Unknown()
    monkeypatch.setattr(regional, 'recover_observed_codes', solve)
    output = tmp_path/'report.json'
    report = regional.run((123, 133), output=output)
    assert len(calls) == 2 and report['complete']
    regional.run((123, 133), output=output, resume=True)
    assert len(calls) == 2
    cached = json.loads(output.read_text())
    cached['experiments'][0]['request']['timeout_ms'] += 1
    output.write_text(json.dumps(cached))
    with pytest.raises(ValueError, match='hash mismatch'):
        regional.run((123, 133), output=output, resume=True)
    assert len(calls) == 2
