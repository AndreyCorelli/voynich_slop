import math
from types import SimpleNamespace

import pytest

torch = pytest.importorskip('torch')
transformers = pytest.importorskip('transformers')

from voynich_smt.neural_scoring import WholeWordScorer


class Encoding(dict):
    def __init__(self, ids, owners):
        super().__init__(input_ids=ids)
        self.owners = owners

    def word_ids(self):
        return self.owners


class Tokenizer:
    is_fast = True
    mask_token_id, pad_token_id, unk_token_id = 4, 1, 3
    model_max_length = 30
    vocabulary = {'a': [5], 'b': [6], 'multi': [7, 8], 'c': [9]}

    def __call__(self, words, **kwargs):
        assert kwargs == {'is_split_into_words': True, 'truncation': False}
        ids, owners = [0], [None]
        for i, word in enumerate(words):
            pieces = self.vocabulary.get(word, [3])
            ids.extend(pieces)
            owners.extend([i] * len(pieces))
        return Encoding(ids + [2], owners + [None])


def scorer(batch_size=8):
    torch.manual_seed(71)
    config = transformers.RobertaConfig(vocab_size=12, hidden_size=16,
        num_hidden_layers=1, num_attention_heads=2, intermediate_size=32,
        max_position_embeddings=32, pad_token_id=1, bos_token_id=0, eos_token_id=2,
        hidden_dropout_prob=0, attention_probs_dropout_prob=0)
    return WholeWordScorer(transformers.RobertaForMaskedLM(config), Tokenizer(),
                           batch_size=batch_size, threads=1)


def test_masks_whole_word_without_spelling_leakage_or_special_targets():
    s = scorer()
    ids, positions, targets = s._job(('a', 'multi', 'b'), 1)
    assert ids == [0, 5, 4, 4, 6, 2]
    assert positions == (2, 3)
    assert targets == (7, 8)


def test_batched_optimized_head_matches_independent_full_forward():
    s = scorer()
    words = ('a', 'multi', 'b', 'c')
    actual = s.segment(words)
    expected = []
    for target in range(len(words)):
        ids, positions, labels = s._job(words, target)
        with torch.inference_mode():
            logits = s.model(input_ids=torch.tensor([ids]), attention_mask=torch.ones(1, len(ids))).logits
            log_probs = torch.log_softmax(logits[0, list(positions)], dim=-1)
            values = log_probs.gather(1, torch.tensor(labels)[:, None]).squeeze(1).tolist()
        expected.append(math.fsum(values))
    assert actual.word_log_sums == pytest.approx(expected, abs=1e-6)
    assert actual.word_subwords == (1, 2, 1, 1)
    totals = actual.totals()
    assert totals['word_masked_log_sum'] == pytest.approx(sum(expected))
    assert totals['word_normalized_log_sum'] == pytest.approx(expected[0] + expected[1] / 2 + expected[2] + expected[3])
    rows = s.inference_rows
    assert s.segment(words) == actual
    assert s.inference_rows == rows
    one = scorer(batch_size=1).segment(words)
    assert one.word_log_sums == pytest.approx(actual.word_log_sums, abs=1e-6)


def test_context_window_boundaries_empty_inputs_and_no_silent_truncation():
    s = scorer()
    assert s.score([])['words'] == 0
    assert s.segment(()).totals()['word_masked_log_sum'] == 0
    local = s.segment(('a', 'multi', 'b', 'c'), context_radius=1)
    expected = []
    for i in range(4):
        first, last = max(0, i - 1), min(4, i + 2)
        words = ('a', 'multi', 'b', 'c')[first:last]
        expected.append(s.segment(words).word_log_sums[i - first])
    assert local.word_log_sums == pytest.approx(expected, abs=1e-6)
    with pytest.raises(ValueError, match='silent truncation'):
        s.segment(('a',) * 40)
    with pytest.raises(ValueError, match='Unknown tokenizer'):
        s.segment(('unrecognized',))
    with pytest.raises(ValueError, match='nonempty surface'):
        s.segment(('a b',))
    with pytest.raises(ValueError, match='Context radius'):
        s.segment(('a',), context_radius=-1)
