import pytest
from benchmarks.word_mapping_pool_size import restrict_catalog
from voynich_smt.word_mapping.candidates import CandidateCatalog
from voynich_smt.word_mapping.morphology import MorphologyCatalog


def test_restriction_uses_training_frequency_and_recomputes_lemma_counts():
    morphology = MorphologyCatalog({'a': [{'lemma_id': 'shared'}],
        'b': [{'lemma_id': 'shared'}, {'lemma_id': 'other'}],
        'c': [{'lemma_id': 'other'}]}, {}, 'train')
    full = CandidateCatalog.build([('a',) * 5 + ('b',) * 4 + ('c',) * 3], morphology, training_sha256='train')
    small = restrict_catalog(full, morphology, 2)
    assert small.forms == ('a', 'b')
    assert small.form_counts == {'a': 5, 'b': 4}
    assert small.lemma_counts == {'other': 2, 'shared': 7}
    assert small.lemma_forms == {'other': ('b',), 'shared': ('a', 'b')}
    assert small.training_sha256 == full.training_sha256
    assert restrict_catalog(full, morphology, None) is full
    for size in (0, True, 4):
        with pytest.raises(ValueError):
            restrict_catalog(full, morphology, size)
