from dataclasses import asdict, replace

import pytest

from voynich_smt.data.corpus import digest
from voynich_smt.word_mapping.candidates import CandidateCatalog
from voynich_smt.word_mapping.diagnostics import truth_diagnostic
from voynich_smt.word_mapping.fixtures import generate
from voynich_smt.word_mapping.morphology import MorphologyCatalog
from voynich_smt.word_mapping.ngram import NgramConfig, NgramModel


def setup(training, plaintext, *, unigram=False, kind='one-to-one'):
    config = NgramConfig(unigram_weight=1, bigram_weight=0, trigram_weight=0) if unigram else NgramConfig()
    model = NgramModel.train(training, config)
    morphology = MorphologyCatalog({w: [] for w in model.vocabulary}, {}, model.training_sha256)
    candidates = CandidateCatalog.build(training, morphology, training_sha256=model.training_sha256)
    public, truth = generate(plaintext, source={}, seed=9, kind=kind)
    return model, candidates, public, truth


def archive(candidates, truth, *, replace_forms=None):
    replace_forms = replace_forms or {}
    return [{'assignments': {cipher: candidates.forms.index(replace_forms.get(form, form))
                            for cipher, form in truth.decoding.items()}, 'score': -9999}]


def test_wrong_mapping_can_outrank_true_dictionary_without_search_failure():
    model, candidates, public, truth = setup([['a'] * 100 + ['b']], [['a', 'b']], unigram=True)
    before = digest(asdict(candidates))
    result = truth_diagnostic(model, candidates, public, truth, archive(candidates, truth, replace_forms={'b': 'a'}))
    assert result['active_truth_feasible']
    assert result['comparison_scope'] == 'complete_active_dictionary'
    assert result['diagnosis'] == 'incorrect_mapping_outranks_truth'
    assert result['best_minus_truth'] > 0
    assert digest(asdict(candidates)) == before


def test_search_below_truth_is_distinct_from_an_objective_counterexample():
    model, candidates, public, truth = setup([['a', 'b'] * 100], [['a', 'b'] * 10])
    result = truth_diagnostic(model, candidates, public, truth,
                             archive(candidates, truth, replace_forms={'a': 'b'}))
    assert result['diagnosis'] == 'search_below_truth'
    assert result['best_minus_truth'] < 0


def test_unigram_tie_is_reported_as_nonidentifiability():
    model, candidates, public, truth = setup([['a', 'b']], [['a', 'b']], unigram=True)
    result = truth_diagnostic(model, candidates, public, truth,
                             archive(candidates, truth, replace_forms={'a': 'b', 'b': 'a'}))
    assert result['diagnosis'] == 'incorrect_mapping_ties_truth'
    assert result['best_minus_truth'] == pytest.approx(0)


def test_missing_candidates_use_identical_masks_and_never_expand_vocabulary():
    model, candidates, public, truth = setup([['a']], [['a', 'missing', 'a']])
    searched = [{'assignments': {w: 0 for s in public.segments for w in s}, 'score': 0}]
    result = truth_diagnostic(model, candidates, public, truth, searched)
    assert not result['active_truth_feasible']
    assert result['comparison_scope'] == 'candidate-covered_unambiguous_subset'
    assert result['comparable_types'] == 1 and result['comparable_tokens'] == 2
    assert result['truth_score']['prediction_events'] == 4
    assert result['best_comparable_score']['prediction_events'] == 4
    assert result['full_plaintext_score_noncomparable']['prediction_events'] == 4
    assert result['full_plaintext_score_noncomparable']['oov_tokens'] == 1
    assert result['candidate_constrained_token_accuracy_ceiling'] == 2 / 3
    assert candidates.forms == ('a',)


def test_lost_plaintext_conflicts_are_not_treated_as_a_true_dictionary():
    model, candidates, public, truth = setup([['a', 'b']], [['a', 'b', 'a']], kind='lossy')
    searched = [{'assignments': {public.segments[0][0]: 0}, 'score': 0}]
    result = truth_diagnostic(model, candidates, public, truth, searched)
    assert result['conflicting_plaintext_types']
    assert result['diagnosis'] == 'no_comparable_truth'
    assert result['truth_score'] is None
    assert result['candidate_constrained_token_accuracy_ceiling'] == 2 / 3


def test_truth_recovered_and_collapse_penalty_calibrated_on_same_types():
    model, candidates, public, truth = setup([['a', 'b']] * 30, [['a', 'b']] * 10, kind='homophonic')
    result = truth_diagnostic(model, candidates, public, truth, archive(candidates, truth), collapse_weight=3)
    assert result['diagnosis'] == 'truth_recovered_in_comparison'
    assert result['truth_score']['collapse_penalty'] == 2
    assert result['truth_score']['objective'] == result['truth_score']['log_likelihood'] - 6


def test_mismatched_truth_and_changing_active_domains_rejected():
    model, candidates, public, truth = setup([['a', 'b']], [['a', 'b']])
    rows = archive(candidates, truth)
    with pytest.raises(ValueError, match='another fixture'):
        truth_diagnostic(model, candidates, public, replace(truth, public_sha256='bad'), rows)
    rows.append({'assignments': {}, 'score': 0})
    with pytest.raises(ValueError, match='active vocabulary'):
        truth_diagnostic(model, candidates, public, truth, rows)


def test_unigram_profile_scores_and_round_trip_and_old_identity(tmp_path):
    model = NgramModel.train([['a', 'b', 'b']], NgramConfig(
        unigram_weight=1, bigram_weight=0, trigram_weight=0))
    assert model.score([['a', 'b']]) == model.score([['b', 'a']])
    path = tmp_path / 'unigram.json'
    model.save(path)
    assert NgramModel.load(path).identity == model.identity
    legacy = NgramModel.train([['a', 'b']])
    assert 'unigram_weight' not in legacy.artifact()['config']
    legacy.save(tmp_path / 'legacy.json')
    assert NgramModel.load(tmp_path / 'legacy.json').identity == legacy.identity
