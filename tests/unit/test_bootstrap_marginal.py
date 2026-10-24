import math
from dataclasses import replace
import pytest
from voynich_smt.bootstrap_mapping import BootstrapOptions
from voynich_smt.bootstrap_marginal import MarginalAgreementModel, MarginalBootstrapSearch
from voynich_smt.word_mapping.annealing import SearchConfig
from test_bootstrap_mapping import entries, resources


def test_marginalization_matches_log_mean_exp_and_retains_ambiguity():
    _, morphology, _ = resources()
    ambiguous = replace(morphology, entries={**morphology.entries,
        'b': morphology.entries['b'] + entries('ADJ', 'ACC', 'P', 'M')})
    model = MarginalAgreementModel(ambiguous)
    assert model.pair('a', 'b') == pytest.approx(math.log((math.exp(2) + math.exp(-2)) / 2) / 2)
    assert model.pair('a', 'd') == -1
    assert model.pair('a', 'f') == 0
    assert model.pair('e', 'b') == 0
    assert MarginalAgreementModel(ambiguous, strength=1000).pair('a', 'b') == pytest.approx(1 - math.log(2) / 1000)
    with pytest.raises(ValueError):
        MarginalAgreementModel(ambiguous, strength=0)


def test_marginal_search_checkpoint_replays_exactly(tmp_path):
    model, morphology, candidates = resources()
    config = SearchConfig(seed=71, restarts=3, steps_per_restart=80,
        initialization='mixed', injective=True, active_types=3)
    options = BootstrapOptions(shortlist_probability=.6, agreement_weight=2, joint_probability=.25)
    segments = [('x', 'y', 'z', 'x')]
    direct = MarginalBootstrapSearch(model, candidates, morphology, segments, config, options)
    direct.advance()
    partial = MarginalBootstrapSearch(model, candidates, morphology, segments, config, options)
    partial.advance(107)
    path = tmp_path / 'checkpoint.json'
    partial.checkpoint(path)
    resumed = MarginalBootstrapSearch(model, candidates, morphology, segments, config, options).resume(path)
    resumed.advance()
    assert resumed.archive == direct.archive
    assert resumed.statistics == direct.statistics
    assert resumed.scorer.objective == direct.scorer.objective
