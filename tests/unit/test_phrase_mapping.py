import itertools
import math
import pytest
from tests.unit.test_bootstrap_mapping import resources
from voynich_smt.bootstrap_mapping import BootstrapOptions
from voynich_smt.phrase_mapping import PhraseSearch, exact_mapping_audit
from voynich_smt.word_mapping.annealing import SearchConfig
from voynich_smt.word_mapping.mapping import WordMapping


def test_phrases_attested_global_injective_and_checkpoint_replay(tmp_path):
    model, morphology, catalog = resources()
    segments = [('x', 'y', 'z', 'x'), ('z', 'y')]
    config = SearchConfig(seed=71, restarts=3, steps_per_restart=100, active_types=3, injective=True)
    options = BootstrapOptions(joint_probability=.5)
    search = PhraseSearch(model, catalog, morphology, segments, config, options)
    attested = {(model.vocabulary[a-3], model.vocabulary[b-3]) for a, b in model.bigram if a >= 3 and b >= 3 and a != b}
    assert {(catalog.forms[a], catalog.forms[b]) for a, b in search.phrase_pairs} == attested
    for _ in range(50):
        _, changes = search._joint()
        assignments = {**search.scorer.assignments, **changes}
        assert len(set(assignments.values())) == len(assignments)
        before = search.scorer.objective
        proposal = search.scorer.propose(changes)
        expected = model.score(WordMapping(catalog.forms, assignments).render(segments)).log_likelihood
        assert before + search.scorer.delta(proposal) == pytest.approx(expected)
    complete = PhraseSearch(model, catalog, morphology, segments, config, options)
    complete.advance()
    partial = PhraseSearch(model, catalog, morphology, segments, config, options)
    partial.advance(137)
    path = tmp_path / 'checkpoint.json'
    partial.checkpoint(path)
    resumed = PhraseSearch(model, catalog, morphology, segments, config, options).resume(path)
    resumed.advance()
    assert resumed.archive == complete.archive
    assert resumed.statistics == complete.statistics
    assert complete.statistics['joint']['proposed'] > 0
    complete.scorer.validate()


def test_exact_audit_matches_independent_enumeration_and_budget():
    model, _, catalog = resources()
    segments = [('x', 'y', 'x'), ('y', 'z')]
    forms = catalog.forms[:4]
    report = exact_mapping_audit(model, segments, forms)
    independent = [model.score(WordMapping(forms, dict(zip(('x', 'y', 'z'), p))).render(segments)).log_likelihood
                   for p in itertools.permutations(range(4), 3)]
    assert report['states'] == math.perm(4, 3)
    assert report['best_score'] == pytest.approx(max(independent))
    assert report['optimal_ties'] == sum(abs(s-max(independent)) < 1e-9 for s in independent)
    with pytest.raises(ValueError, match='budget'):
        exact_mapping_audit(model, segments, forms, max_states=23)
    with pytest.raises(ValueError):
        exact_mapping_audit(model, segments, ['a', 'a', 'b'])
