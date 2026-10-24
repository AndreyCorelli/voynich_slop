import json

import pytest

from voynich_smt.word_mapping.scalable.data import CipherStream
from voynich_smt.word_mapping.scalable.inventory import Inventory
from voynich_smt.word_mapping.scalable.retrieval import RetrievalConfig
from voynich_smt.word_mapping.scalable.search import DictionarySearch, SearchConfig
from voynich_smt.word_mapping.scalable.sparse_lm import SparseBigram


@pytest.fixture
def resources(tmp_path):
    inventory = Inventory.build(tmp_path / 'inventory.sqlite', ['a', 'b', 'c', 'd', 'e'])
    model = SparseBigram.train(inventory, [[0, 1, 2, 0, 1, 2], [3, 1, 0]])
    yield model, CipherStream(((0, 1, 2, 0, 1), (2, 1, 0)), 3)
    inventory.close()


def options():
    return dict(seed=3, config=SearchConfig(proposals=80, refresh_interval=7, validation_interval=11,
                                          checkpoint_interval=13, budget_seconds=30, reserve_seconds=0),
                retrieval_config=RetrievalConfig(active_limit=4, total_entries=12, per_context=3,
                                                  frequency_limit=3, random_candidates=2, pool_limit=10))


def test_checkpoint_continuation_replays_decisions_caches_and_joint_keys(resources, tmp_path):
    model, stream = resources
    uninterrupted = DictionarySearch(model, stream, **options())
    expected = [uninterrupted.advance() for _ in range(80)]
    partial = DictionarySearch(model, stream, **options())
    actual = [partial.advance() for _ in range(31)]
    path = tmp_path / 'checkpoint.json'
    partial.save(path)
    resumed = DictionarySearch.load(path, model, stream)
    actual.extend(resumed.advance() for _ in range(49))
    assert actual == expected
    a, b = uninterrupted.snapshot(), resumed.snapshot()
    for key in ('elapsed_seconds',):
        a.pop(key); b.pop(key)
    assert a == b
    assert len(resumed.joint_archive) <= resumed.config.joint_archive_size
    assert resumed.joint_archive[0][0] >= resumed.initial_score
    resumed.scorer.validate()


def test_budget_stop_saves_consistent_resumable_state(resources, tmp_path):
    model, stream = resources
    class Clock:
        value = 0.
        def __call__(self):
            self.value += 1.
            return self.value
    search = DictionarySearch(model, stream, clock=Clock(), **options())
    path = tmp_path / 'checkpoint.json'
    result = search.run(checkpoint=path)
    assert result['stop_reason'] == 'time_budget'
    assert result['step'] < 80
    resumed = DictionarySearch.load(path, model, stream)
    assert resumed.scorer.state == search.scorer.state
    assert resumed.step == search.step
    resumed.scorer.validate()


def test_partial_run_and_model_bound_tamper_checks(resources, tmp_path):
    model, stream = resources
    search = DictionarySearch(model, stream, **options())
    path = tmp_path / 'checkpoint.json'
    assert search.run(steps=20, checkpoint=path)['stop_reason'] == 'partial'
    resumed = DictionarySearch.load(path, model, stream)
    result = resumed.run()
    assert result['stop_reason'] == 'proposal_limit' and result['step'] == 80
    assert sum(result['source_counts'].values()) == 80
    assert result['accepted'] + result['noops'] <= 80
    envelope = json.loads(path.read_text())
    envelope['payload']['step'] += 1
    path.write_text(json.dumps(envelope))
    with pytest.raises(ValueError, match='identity'):
        DictionarySearch.load(path, model, stream)


@pytest.mark.parametrize('kwargs', [{'greedy_probability': 1}, {'frequency_mix': 1}, {'proposals': 0},
                                   {'budget_seconds': 1, 'reserve_seconds': 1}])
def test_invalid_search_contract(kwargs):
    with pytest.raises(ValueError):
        SearchConfig(**kwargs)


def test_memory_budget_stops_before_next_transaction(resources, monkeypatch):
    from voynich_smt.word_mapping.scalable import search as module
    model, stream = resources
    monkeypatch.setattr(module, 'peak_rss', lambda: 100)
    kwargs = options()
    from dataclasses import replace
    kwargs['config'] = replace(kwargs['config'], memory_limit_bytes=99)
    search = DictionarySearch(model, stream, **kwargs)
    result = search.run()
    assert result['stop_reason'] == 'memory_budget' and result['step'] == 0
    search.scorer.validate()


def test_cli_budget_is_divided_across_restarts():
    from benchmarks.scalable_english_run import allocate_budget
    result = allocate_budget(SearchConfig(budget_seconds=3600., reserve_seconds=12.), 3)
    assert result.budget_seconds == 1200.
    assert result.reserve_seconds == 4.
    assert result.proposals == 20000


@pytest.mark.parametrize('split', [1, 3, 5])
def test_coverage_pass_and_resume(resources, tmp_path, split):
    from dataclasses import replace
    model, stream = resources
    kwargs = options()
    kwargs['config'] = replace(kwargs['config'], scheduler='coverage_first')
    search = DictionarySearch(model, stream, **kwargs)
    expected = [search.advance() for _ in range(80)]
    assert sorted(event['cipher'] for event in expected[:stream.type_count]) == list(range(stream.type_count))
    partial = DictionarySearch(model, stream, **kwargs)
    actual = [partial.advance() for _ in range(split)]
    path = tmp_path / 'coverage.json'
    partial.save(path)
    resumed = DictionarySearch.load(path, model, stream)
    actual.extend(resumed.advance() for _ in range(80 - split))
    assert actual == expected
    assert resumed.scorer.state == search.scorer.state


def test_unknown_scheduler_is_rejected():
    with pytest.raises(ValueError, match='scheduler'):
        SearchConfig(scheduler='unknown')


def test_legacy_checkpoint_defaults_to_mixed(resources, tmp_path):
    from voynich_smt.data.corpus import digest
    model, stream = resources
    search = DictionarySearch(model, stream, **options())
    search.advance()
    path = tmp_path / 'legacy.json'
    search.save(path)
    envelope = json.loads(path.read_text())
    del envelope['payload']['config']['scheduler']
    del envelope['payload']['config']['initialization']
    del envelope['payload']['config']['joint_probability']
    del envelope['payload']['retrieval_config']['context_strategy']
    del envelope['payload']['retrieval_config']['attested_mix']
    envelope['sha256'] = digest(envelope['payload'])
    path.write_text(json.dumps(envelope))
    resumed = DictionarySearch.load(path, model, stream)
    assert resumed.config.scheduler == 'mixed'
    assert resumed.advance() == search.advance()


def test_short_coverage_schedule_does_not_override_budget_or_horizon(resources):
    from dataclasses import replace
    model, stream = resources
    kwargs = options()
    kwargs['config'] = replace(kwargs['config'], scheduler='coverage_first', proposals=2)
    search = DictionarySearch(model, stream, **kwargs)
    assert search.run()['step'] == 2
    assert search.step < stream.type_count
    assert search.stop_reason == 'proposal_limit'


def test_frequency_initialization_checkpoint_resume(resources, tmp_path):
    from dataclasses import replace
    model, stream = resources
    kwargs = options()
    kwargs['config'] = replace(kwargs['config'], initialization='frequency')
    full = DictionarySearch(model, stream, **kwargs)
    expected = [full.advance() for _ in range(80)]
    partial = DictionarySearch(model, stream, **kwargs)
    actual = [partial.advance() for _ in range(17)]
    path = tmp_path/'frequency.json'
    partial.save(path)
    resumed = DictionarySearch.load(path, model, stream)
    actual.extend(resumed.advance() for _ in range(63))
    assert expected == actual
    assert resumed.scorer.state == full.scorer.state
    assert resumed.config.initialization == 'frequency'
    with pytest.raises(ValueError, match='initialization'):
        SearchConfig(initialization='unknown')


def test_attested_mixture_exact_checkpoint_continuation(resources, tmp_path):
    from dataclasses import replace
    model,stream=resources
    kwargs=options()
    kwargs['retrieval_config']=replace(kwargs['retrieval_config'],attested_mix=.5)
    search=DictionarySearch(model,stream,**kwargs)
    for _ in range(31): search.advance()
    path=tmp_path/'attested.json';search.save(path)
    resumed=DictionarySearch.load(path,model,stream)
    for _ in range(49): assert search.advance()==resumed.advance()
    assert search.joint_archive==resumed.joint_archive
    search.scorer.validate();resumed.scorer.validate()
