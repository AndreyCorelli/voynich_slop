from dataclasses import replace
import pytest
from tests.unit.test_bootstrap_mapping import resources
from voynich_smt.oracle_mapping import OracleStartSearch
from voynich_smt.word_mapping.annealing import SearchConfig
from voynich_smt.word_mapping.fixtures import generate
from voynich_smt.word_mapping.evaluation import recovery


@pytest.mark.parametrize('policy', ['greedy', 'annealing'])
def test_zero_corruption_every_proposal_full_counters_and_deterministic_replay(policy):
    model, morphology, candidates = resources()
    public, truth = generate([('e', 'f', 'a', 'e'), ('f', 'a')], source={}, seed=17)
    config = SearchConfig(seed=71, restarts=1, steps_per_restart=400, active_types=3,
                          injective=True, archive_size=1)
    search = OracleStartSearch(model, candidates, morphology, public, truth, config, policy=policy)
    assert search.scorer.mapping.render(public.segments) == truth.plaintext
    assert search.correct_tokens == 6 and search.correct_types == 3
    for _ in range(400):
        search.advance(1)
        search.validate_oracle()
        search.scorer.validate()
        metrics = recovery(public, truth, search.scorer.mapping)
        assert metrics['exact_token_accuracy'] == search.correct_tokens/6
        assert metrics['exact_type_accuracy'] == search.correct_types/3
    repeated = OracleStartSearch(model, candidates, morphology, public, truth, config, policy=policy)
    repeated.advance()
    assert repeated.archive == search.archive and repeated.quality == search.quality
    assert repeated.first_departure == search.first_departure
    assert sum(v['proposed'] for v in search.quality.values()) == 400
    if policy == 'greedy':
        assert search.quality['down/down']['accepted'] == 0
        assert sum(search.quality[f'flat/{r}']['accepted'] for r in ('up', 'down', 'flat')) == 0
        assert search.first_departure['score_delta'] > 1e-9
        assert search.first_departure['token_delta'] < 0
        assert search.perfect_score_witness is not None
        assert search.archive[0]['score'] > search.initial_objective


def test_zero_corruption_rejects_wrong_identity_incomplete_truth_and_restarts():
    model, morphology, candidates = resources()
    public, truth = generate([('a', 'b')], source={}, seed=11)
    config = SearchConfig(restarts=1, steps_per_restart=10, active_types=2, injective=True)
    with pytest.raises(ValueError, match='identity'):
        OracleStartSearch(model, candidates, morphology, public, replace(truth, public_sha256='wrong'), config)
    with pytest.raises(ValueError, match='exactly'):
        OracleStartSearch(model, candidates, morphology, public, replace(truth, decoding={}), config)
    with pytest.raises(ValueError, match='One injective'):
        OracleStartSearch(model, candidates, morphology, public, truth, replace(config, restarts=2))
    with pytest.raises(ValueError, match='exact injective'):
        OracleStartSearch(model, candidates, morphology, public, replace(truth, plaintext=(('b','a'),)), config)


def test_greedy_preserves_a_perfect_dictionary_when_it_is_the_score_optimum():
    from voynich_smt.word_mapping.ngram import NgramModel
    from voynich_smt.word_mapping.candidates import CandidateCatalog
    _, old_morphology, _ = resources()
    train = [('a', 'b')]*100
    model = NgramModel.train(train)
    morphology = replace(old_morphology, entries={w: old_morphology.entries[w] for w in ('a','b')},
                         training_sha256=model.training_sha256)
    candidates = CandidateCatalog.build(train, morphology, training_sha256=model.training_sha256)
    public, truth = generate([('a','b')], source={}, seed=17)
    config = SearchConfig(seed=71, restarts=1, steps_per_restart=400, active_types=2, injective=True, archive_size=1)
    search = OracleStartSearch(model, candidates, morphology, public, truth, config, policy='greedy')
    search.advance()
    assert search.correct_tokens == 2 and search.correct_types == 2
    assert search.best_mapping.render(public.segments) == truth.plaintext
    assert search.first_departure is None
    assert search.archive[0]['score'] == search.initial_objective
