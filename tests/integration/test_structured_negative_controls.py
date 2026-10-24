from collections import Counter

from benchmarks import structured_negative_controls as b
from benchmarks.l3_conflict import verify
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.models.text import Text


def test_bigram_control_preserves_edges_endpoints_and_repetitions():
    text=Text.from_string('abacada abacada abacaba')
    changed,audit=b.generate(text,'bigrams')
    assert changed is not None and changed!=text
    assert changed.words[0]==changed.words[1]
    assert audit['exact_repetition_partition_preserved']
    assert audit['overlapping_bigram_counts_per_word_preserved']
    assert audit['endpoints_per_word_preserved']
    assert audit['glyph_counts_per_word_preserved']
    assert b.generate(text,'bigrams')==(changed,audit)


def test_chunk_control_keeps_aligned_pairs_and_records_unavailable():
    text=Text.from_string('aabbcc aabbcc ddee')
    changed,audit=b.generate(text,'pair-chunks')
    assert changed is not None and changed!=text
    assert audit['aligned_pair_counts_per_word_preserved']
    assert audit['exact_repetition_partition_preserved']
    unchanged,metadata=b.generate(Text.from_string('ab ab'),'bigrams')
    assert unchanged is None and metadata['status'].startswith('UNAVAILABLE')


def test_preparation_keeps_positive_and_structural_controls_separate(tmp_path,monkeypatch):
    monkeypatch.setattr(b,'OUT',tmp_path)
    prepared=b.prepare()
    assert len([c for c in prepared['cases'] if c['kind']=='positive'])==4
    assert len(prepared['cases'])+len(prepared['unavailable'])==12
    for case in prepared['cases']:
        if case['kind']=='positive':verify(HiddenRecoveryRequest.from_dict(case['request']),case['truth'])
        else:
            assert case['construction']['changed_word_occurrences']>0
            assert case['construction']['exact_repetition_partition_preserved']
            assert 'truth' not in case
    assert b.digest(prepared)==b.digest(b.prepare())
