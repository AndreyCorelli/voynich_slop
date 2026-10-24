import json

from benchmarks.ravi_knight_english import run
from benchmarks.ravi_knight_english_validate import validate
from benchmarks.ravi_knight_length_compare import compare


def test_nested_fixture_preserves_cipher_identities_and_active_vocabularies(tmp_path):
    raw = tmp_path / 'raw'
    raw.mkdir()
    end = '\n*** END OF THE PROJECT GUTENBERG EBOOK X ***'
    (raw / '1342.txt').write_text('It is a truth universally acknowledged, the cat runs.\n' + 'The cat runs. A dog walks.\n' * 20 + end)
    (raw / '11.txt').write_text('Alice was beginning to get very tired.\n' +
                               'The cat runs.\n' * 5 + 'A new dog walks.\n' * 1500 + end)
    short_dir, long_dir = tmp_path / 'short', tmp_path / 'long'
    options = dict(sizes=(1, 2), iterations=1)
    short = run(raw, short_dir, tokens=20, **options)
    long = run(raw, long_dir, tokens=60, reference_run=short_dir, **options)
    assert long['prefix_tokens'] == short['cipher_tokens']
    assert long['cipher_tokens'] > short['cipher_tokens']
    assert long['frequency']['prefix_token_accuracy'] == short['frequency']['token_accuracy']
    assert validate(short_dir) == validate(long_dir) == 6
    report = compare(short_dir, long_dir)
    assert len(report['runs']) == 3
    a = json.loads((short_dir / 'evaluation-only/truth.json').read_text())['key']
    b = json.loads((long_dir / 'evaluation-only/truth.json').read_text())['key']
    assert all(b[w] == code for w, code in a.items())
