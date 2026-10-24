import json
import sqlite3

import pytest

from benchmarks.scalable_english_build import build
from benchmarks.scalable_english_prepare import prepare
from benchmarks.scalable_english_validate import validate
from voynich_smt.word_mapping.scalable.data import CipherStream
from voynich_smt.word_mapping.scalable.inventory import Inventory


def test_prepare_and_public_loading_are_independent_of_truth(tmp_path):
    path = tmp_path / 'private-source.txt'
    path.write_text("The cat walks.\nThe dog walks!")
    root = tmp_path / 'fixture'
    before = prepare([path], root, seed=3)
    public_path = root / 'public/cipher.json'
    snapshot = public_path.read_bytes()
    truth = root / 'evaluation-only/truth.json'
    truth.write_text('{"deliberately": "changed evaluation-only content"}')
    path.unlink()
    assert CipherStream.load(public_path) == before
    assert snapshot == public_path.read_bytes()
    assert json.loads(snapshot)['documents'] == [list(before.documents[0])]
    assert len(before.documents[0]) == 6
    with pytest.raises(FileExistsError):
        # Existing output may not be overwritten; use an existing input too.
        source = tmp_path / 'again.txt'
        source.write_text('another text')
        prepare([source], root)


def test_engineering_build_coverage_and_artifact_validation(tmp_path):
    raw = tmp_path / 'raw'
    raw.mkdir()
    (raw / 'en_ewt-r2.17-train.conllu').write_text(
        '# newdoc id = train\n# text = The cat walks.\n# text = The dog walks.\n')
    (raw / 'en_ewt-r2.17-dev.conllu').write_text(
        '# newdoc id = dev-one\n# text = The dog walks.\n'
        '# newdoc id = dev-two\n# text = The giraffe walks.\n')
    output = tmp_path / 'build'
    report = build(raw, output)
    assert report['inventory_forms'] == 4
    assert report['development']['missing_tokens'] == 1
    assert report['development']['excluded_documents'] == 1
    assert validate(raw, output)['status'] == 'validated'
    with sqlite3.connect(output / 'inventory.sqlite') as db:
        db.execute("UPDATE forms SET word='different' WHERE word='dog'")
    with pytest.raises(ValueError, match='mismatch'):
        Inventory(output / 'inventory.sqlite')


def test_dictionary_move_artifact_replay(tmp_path):
    from benchmarks.scalable_english_moves import run
    from benchmarks.scalable_english_moves_validate import validate as validate_moves
    raw = tmp_path / 'raw'
    raw.mkdir()
    training = raw / 'en_ewt-r2.17-train.conllu'
    training.write_text('# newdoc id = one\n# text = The cat walks.\n# text = The dog walks.\n')
    (raw / 'en_ewt-r2.17-dev.conllu').write_text('# newdoc id = two\n# text = The dog walks.\n')
    resources = tmp_path / 'resources'
    build(raw, resources)
    output = tmp_path / 'moves'
    report = run(resources, training, output, tokens=6, proposals=50)
    assert report['tokens'] == 6
    assert report['full_validation_checks'] == 1
    assert validate_moves(resources, output)['replayed_proposals'] == 50


def test_retrieval_artifact_replay_and_score_checks(tmp_path):
    from benchmarks.scalable_english_retrieval import run
    from benchmarks.scalable_english_retrieval_validate import validate as validate_retrieval
    raw = tmp_path / 'raw'
    raw.mkdir()
    training = raw / 'en_ewt-r2.17-train.conllu'
    training.write_text('# newdoc id = one\n# text = The cat walks.\n# text = The dog walks.\n')
    (raw / 'en_ewt-r2.17-dev.conllu').write_text('# newdoc id = two\n# text = The dog walks.\n')
    resources = tmp_path / 'resources'
    build(raw, resources)
    output = tmp_path / 'retrieval'
    report = run(resources, training, output, tokens=6, sampled_types=3)
    assert report['sampled_types'] == 3
    assert report['active_entries'] <= 300
    assert validate_retrieval(resources, output)['candidate_rows_replayed'] == 3


def test_search_public_only_run_resume_and_separate_evaluation(tmp_path):
    from benchmarks.scalable_english_run import run as search_run
    from benchmarks.scalable_english_evaluate import evaluate
    from voynich_smt.word_mapping.scalable.search import SearchConfig
    from voynich_smt.word_mapping.scalable.retrieval import RetrievalConfig
    raw = tmp_path / 'raw'
    raw.mkdir()
    (raw / 'en_ewt-r2.17-train.conllu').write_text('# newdoc id = one\n# text = The cat walks.\n# text = The dog walks.\n')
    (raw / 'en_ewt-r2.17-dev.conllu').write_text('# newdoc id = two\n# text = The dog walks.\n')
    resources = tmp_path / 'resources'
    build(raw, resources)
    source = tmp_path / 'source.txt'
    source.write_text('The cat walks. The dog walks.')
    fixture = tmp_path / 'fixture'
    prepare([source], fixture)
    truth = fixture / 'evaluation-only/truth.json'
    hidden = truth.read_bytes()
    truth.unlink()
    source.unlink()
    config = SearchConfig(proposals=60, checkpoint_interval=10, validation_interval=10,
                          budget_seconds=30, reserve_seconds=0)
    retrieval = RetrievalConfig(active_limit=4, total_entries=16, per_context=3)
    output = tmp_path / 'search'
    options = dict(seeds=(3,), config=config, retrieval=retrieval)
    partial = search_run(resources, fixture / 'public/cipher.json', output, steps=17, **options)
    assert partial['runs'][0]['stop_reason'] == 'partial'
    with pytest.raises(ValueError, match='fresh run'):
        search_run(resources, fixture / 'public/cipher.json', output, resume=True, trace=True, **options)
    legacy = json.loads((output / 'protocol.json').read_text())
    del legacy['search']['scheduler']
    del legacy['search']['initialization']
    del legacy['search']['joint_probability']
    del legacy['retrieval']['context_strategy']
    del legacy['retrieval']['attested_mix']
    (output / 'protocol.json').write_text(json.dumps(legacy))
    complete = search_run(resources, fixture / 'public/cipher.json', output, resume=True, **options)
    assert complete['runs'][0]['step'] == 60
    truth.write_bytes(hidden)
    report = evaluate(resources, output, truth)
    assert report['grammar'] == report['semantics'] == 'not_evaluated'
    assert 0 <= report['selected_token_accuracy'] <= 1
    assert complete['runs'][0]['best_score'] >= complete['runs'][0]['initial_score']


@pytest.mark.parametrize("scheduler", ["mixed", "coverage_first"])
def test_search_trace_and_failure_analysis_reproduce_saved_keys(tmp_path, scheduler):
    from benchmarks.scalable_english_run import run as search_run
    from benchmarks.scalable_english_trace import run as trace_run
    from benchmarks.scalable_english_diagnostics import analyze
    from voynich_smt.word_mapping.scalable.search import SearchConfig
    from voynich_smt.word_mapping.scalable.retrieval import RetrievalConfig
    raw=tmp_path/'raw'; raw.mkdir()
    (raw/'en_ewt-r2.17-train.conllu').write_text('# newdoc id = one\n# text = The cat walks.\n# text = The dog walks.\n')
    (raw/'en_ewt-r2.17-dev.conllu').write_text('# newdoc id = two\n# text = The dog walks.\n')
    resources=tmp_path/'resources'; build(raw,resources)
    source=tmp_path/'source.txt'; source.write_text('The cat walks. The dog walks.')
    fixture=tmp_path/'fixture'; prepare([source],fixture)
    root=tmp_path/'run'
    search_run(resources,fixture/'public/cipher.json',root,seeds=(3,),
               config=SearchConfig(proposals=30, scheduler=scheduler),
               retrieval=RetrievalConfig(active_limit=4,total_entries=16), trace=True)
    traces=tmp_path/'traces'; replay_report=trace_run(resources,root,traces)
    assert replay_report['runs'][0]['exact_joint_archive_match']
    import gzip
    assert gzip.open(root/'traces/seed-3.jsonl.gz', 'rt').read() == gzip.open(traces/'seed-3.jsonl.gz', 'rt').read()
    report=analyze(resources,root,fixture/'evaluation-only/truth.json',traces,tmp_path/'analysis')
    assert sum(report['attribution']['3']['categories'].values())==4
    assert report['attribution']['3']['moves']==30
    assert len(report['fixed_samples'])==5
    for method in report['methods'].values():
        assert sum(b['types'] for b in method['frequency_bands'].values())==4
        assert abs(method['base_frequency_component']+method['context_component']-method['source_score'])<1e-12
    from benchmarks.scalable_english_diagnostics_validate import validate as validate_diagnostics
    assert validate_diagnostics(resources,root,fixture/'evaluation-only/truth.json',traces,tmp_path/'analysis')['status']=='validated'
    if scheduler == 'coverage_first':
        from benchmarks.scalable_english_evaluate import evaluate
        from benchmarks.scalable_english_compare_schedules import compare
        mixed = tmp_path/'mixed'
        search_run(resources,fixture/'public/cipher.json',mixed,seeds=(3,),
                   config=SearchConfig(proposals=30, scheduler='mixed'),
                   retrieval=RetrievalConfig(active_limit=4,total_entries=16), trace=True)
        for run_root in (root, mixed):
            evaluate(resources,run_root,fixture/'evaluation-only/truth.json')
            analyze(resources,run_root,fixture/'evaluation-only/truth.json',run_root/'traces',run_root/'analysis')
            validate_diagnostics(resources,run_root,fixture/'evaluation-only/truth.json',run_root/'traces',run_root/'analysis')
        comparison = compare(mixed,root,tmp_path/'comparison.json')
        assert comparison['methods']['coverage_first']['mean_visited_types'] == 4
        assert len(comparison['paired_changes']) == 1
        saved = json.loads((mixed/'inference.json').read_text())
        saved['runs'][0]['step'] = 29
        (mixed/'inference.json').write_text(json.dumps(saved))
        with pytest.raises(AssertionError, match='Incomplete'):
            compare(mixed,root,tmp_path/'incomplete.json')
        saved['runs'][0]['step'] = 30
        saved['protocol']['search']['initial_temperature'] = 2
        (mixed/'inference.json').write_text(json.dumps(saved))
        with pytest.raises(AssertionError, match='more than'):
            compare(mixed,root,tmp_path/'confounded.json')
