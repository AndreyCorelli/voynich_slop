from dataclasses import replace
import math
import pytest
from tests.unit.test_bootstrap_mapping import resources
from benchmarks.word_mapping_widening import held_event_comparison, jobs_for
from voynich_smt.widening_mapping import WideningSearch, expanded_model, nested_prefixes, repetition_statistics
from voynich_smt.word_mapping.annealing import SearchConfig
from voynich_smt.word_mapping.fixtures import CipherInput, CipherTruth
from voynich_smt.word_mapping.mapping import WordMapping


def test_nested_prefixes_whole_segments_fixed_holdout_and_repetition():
    segments = [('a', 'b'), ('a', 'c', 'd'), ('e', 'f'), ('a', 'z')]
    cases, held = nested_prefixes(segments, (2, 4, 7), holdout_tokens=2)
    assert cases[2] == segments[:1] or cases[2] == tuple(segments[:1])
    assert cases[4] == tuple(segments[:2])
    assert cases[7] == tuple(segments[:3])
    assert held == (('a', 'z'),)
    stats = repetition_statistics(cases[7], held)
    assert stats['tokens'] == 7 and stats['types'] == 6
    assert stats['holdout_recurring_tokens'] == 1 and stats['holdout_unseen_types'] == 1
    with pytest.raises(ValueError, match='Insufficient'):
        nested_prefixes(segments, (8,), holdout_tokens=2)
    with pytest.raises(ValueError):
        nested_prefixes(segments, (4, 2), holdout_tokens=2)


def test_expansion_keeps_counts_ids_and_distinguishes_zero_count_surfaces():
    original, _, _ = resources()
    wide = expanded_model(original, ('unknown1', 'unknown2', 'a'))
    assert wide.form_ids['a'] == original.form_ids['a']
    assert wide.form_ids['unknown1'] != wide.form_ids['unknown2']
    assert wide.unigram == original.unigram and wide.bigram == original.bigram
    assert wide.trigram == original.trigram and wide.total == original.total
    assert wide.training_sha256 == original.training_sha256
    assert wide.unigram[wide.form_ids['unknown1']] == 0
    assert wide.probability(0, 0, wide.form_ids['unknown1']) == wide.probability(0, 0, wide.form_ids['unknown2'])


def test_cached_owners_full_scores_checkpoint_and_shared_initialization(tmp_path):
    model, morphology, candidates = resources()
    segments = [('x', 'y', 'z', 'x'), ('z', 'y')]
    config = SearchConfig(seed=71, restarts=3, steps_per_restart=100, active_types=3,
                          injective=True, archive_size=1)
    complete = WideningSearch(model, candidates, morphology, segments, config)
    complete.advance()
    for row in complete.archive:
        assert row['score'] == pytest.approx(model.score(WordMapping(candidates.forms, row['assignments']).render(segments)).log_likelihood)
    partial = WideningSearch(model, candidates, morphology, segments, config)
    partial.advance(137)
    path = tmp_path / 'checkpoint.json'
    partial.checkpoint(path)
    resumed = WideningSearch(model, candidates, morphology, segments, config).resume(path)
    resumed.advance()
    assert resumed.archive == complete.archive and resumed.statistics == complete.statistics
    assert resumed.owners == {v: w for w, v in resumed.scorer.assignments.items()}
    assert sum(s['proposed'] for s in resumed.statistics.values()) == 300
    short = WideningSearch(model, candidates, morphology, segments, config)
    long = WideningSearch(model, candidates, morphology, segments, replace(config, steps_per_restart=200))
    for _ in range(3):
        assert short.scorer.assignments == long.scorer.assignments
        short.advance(100)
        long.advance(200)


def test_heldout_comparison_does_not_create_boundaries_around_unknowns():
    model, _, catalog = resources()
    public = CipherInput((('x', 'unknown', 'z'),), {}, {})
    truth = CipherTruth(public.identity, (('a', 'c', 'b'),), {'x': 'a', 'unknown': 'c', 'z': 'b'}, 1)
    mapping = WordMapping(catalog.forms, {'x': catalog.forms.index('a'), 'z': catalog.forms.index('b')})
    result = held_event_comparison(model, public, truth, mapping)
    assert result['events'] == 1
    assert result['prediction_log_score'] == pytest.approx(math.log(model.probability(0, 0, model.form_ids['a'])))
    assert result['score_gap_per_event'] == 0


def test_scaled_budgets_and_duplicate_smallest_jobs():
    publics = {2: CipherInput((('x', 'y'),), {}, {}), 5: CipherInput((('x', 'y', 'z', 'u', 'v'),), {}, {})}
    jobs = jobs_for(publics, 11, (101,), 3)
    assert len(jobs) == 6
    assert all(j['budget_modes'] == ['equal', 'scaled'] for j in jobs if j['target'] == 2)
    assert all(j['config']['steps_per_restart'] == 28 for j in jobs if j['target'] == 5 and 'scaled' in j['budget_modes'])
