import pytest

from voynich_smt.word_mapping.ravi_knight.english import extract, prefix_segments


def test_extraction_removes_frontmatter_footer_and_preserves_contractions():
    text = "Front matter. Alice was beginning to get very tired.\n\nDon't go!\n\n[Illustration: noise.]\nCHAPTER II.\n\nNew prose?\n*** END OF THE PROJECT GUTENBERG EBOOK X *** license"
    segments = extract(text, '11')
    assert segments == (('alice', 'was', 'beginning', 'to', 'get', 'very', 'tired'),
                        ("don't", 'go'), ('new', 'prose'))
    assert prefix_segments(segments, 9) == segments[:2]
    with pytest.raises(ValueError):
        prefix_segments(segments, 1)
    with pytest.raises(ValueError):
        extract('unrecognized edition', '11')


def test_source_loss_counts_unknown_and_endpoints():
    import math
    from voynich_smt.word_mapping.ravi_knight.english import source_loss
    from voynich_smt.word_mapping.ravi_knight.lm import train_bigram
    source = train_bigram([('a', 'b')], max_types=1)
    result = source_loss(source, [('a', 'unseen')])
    score = math.log(source.initial[1]) + math.log(source.transition[1][0]) + math.log(source.final[0])
    assert result['log_probability'] == pytest.approx(score)
    assert result['prediction_events'] == 3
    assert result['unknown_tokens'] == 1
