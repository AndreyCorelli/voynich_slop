from types import SimpleNamespace
import pytest
from benchmarks.word_mapping_context_rank import ranking, target_jobs


def test_ties_have_fractional_credit_and_expected_reciprocal_rank():
    result = ranking([10, 10, 9], 0)
    assert result['midrank'] == 1.5
    assert result['top1_credit'] == .5
    assert result['top5_credit'] == 1
    assert result['reciprocal_rank'] == .75
    assert ranking([9, 8, 7, 6, 5, 4], 5)['top5_credit'] == 0
    with pytest.raises(ValueError):
        ranking([float('nan')], 0)


class Masker:
    tokenizer = SimpleNamespace(mask_token_id=99)
    def _job(self, words, target):
        ids = [0]
        groups = []
        for word in words:
            start = len(ids)
            ids.extend([7, 8] if word == 'multi' else [5])
            groups.append(tuple(range(start, len(ids))))
        ids.append(2)
        places = groups[target]
        labels = tuple(ids[i] for i in places)
        for i in places:
            ids[i] = 99
        return ids, places, labels


def test_every_repeated_target_is_masked_but_neighbors_remain_visible():
    jobs = target_jobs(Masker(), ['multi', 'neighbor', 'multi'], [0, 2])
    assert all(ids == [0, 99, 99, 5, 99, 99, 2] for ids, _, _ in jobs)
    assert jobs[0][1:] == ((1, 2), (7, 8))
    assert jobs[1][1:] == ((4, 5), (7, 8))
    with pytest.raises(ValueError):
        target_jobs(Masker(), ['multi'], [0, 0])
