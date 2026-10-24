import json

from benchmarks.scalable_english_independent import AUSTEN,WELLS,build,prepare
from benchmarks.scalable_english_strategy_resources import build_expanded,build_trigram
from benchmarks.scalable_english_run import run
from benchmarks.scalable_english_evaluate import evaluate
from benchmarks.scalable_english_diagnostics import analyze
from benchmarks.scalable_english_diagnostics_validate import validate
from benchmarks.scalable_english_consensus import collect,evaluate as evaluate_consensus
from voynich_smt.word_mapping.scalable.search import SearchConfig
from voynich_smt.word_mapping.scalable.retrieval import RetrievalConfig


def test_strategy_resources_trigram_search_and_consensus(tmp_path,monkeypatch):
    import benchmarks.scalable_english_strategy_resources as module
    ewt=tmp_path/'ewt'; ewt.write_text('# newdoc id = x\n# text = The cat sleeps and the dog walks.\n')
    austen=tmp_path/'austen'; austen.write_text(AUSTEN+' the dog sleeps.\n*** END OF THE PROJECT GUTENBERG EBOOK TEST ***')
    lexicon=tmp_path/'dict'; lexicon.write_text('no N\none W\nwould W\nhave H\nbelieved B\n')
    base=tmp_path/'base'; build(ewt,austen,lexicon,base)
    raw=tmp_path/'raw'; raw.mkdir()
    (raw/'1.txt').write_text('Training extra context and the hiddenword.\n*** END OF THE PROJECT GUTENBERG EBOOK TEST ***')
    monkeypatch.setattr(module,'BOOKS',[('1','Training extra','Example','Author')])
    expanded=tmp_path/'expanded'
    reports=build_expanded(base,raw,expanded)
    assert reports['corpus_control']['inventory_sha256']==reports['corpus_expanded']['inventory_sha256']
    assert reports['corpus_expanded']['training_tokens']>reports['corpus_control']['training_tokens']
    trigram=tmp_path/'trigram'; build_trigram(base,trigram)
    target=tmp_path/'target'
    target.write_text(WELLS+' the cat.\n*** END OF THE PROJECT GUTENBERG EBOOK TEST ***')
    fixture=tmp_path/'fixture'; prepare(base,target,fixture,tokens=7)
    truth=fixture/'evaluation-only/truth.json'
    hidden=truth.read_bytes(); truth.unlink(); target.unlink()
    root=tmp_path/'run'
    run(trigram,fixture/'public/cipher.json',root,seeds=(3,5),
        config=SearchConfig(proposals=30,initialization='frequency',joint_probability=.2),
        retrieval=RetrievalConfig(context_strategy='pooled',active_limit=4,total_entries=20),trace=True)
    # Consensus collection needs only opaque keys and initial trace events.
    public=collect(root,root/'consensus-public.json')
    assert 'decoding' not in public and len(public['rows'])==7
    truth.write_bytes(hidden)
    measured=evaluate(trigram,root,truth)
    analyzed=analyze(trigram,root,truth,root/'traces',root/'analysis')
    assert validate(trigram,root,truth,root/'traces',root/'analysis')['status']=='validated'
    consensus=evaluate_consensus(trigram,root,truth,root/'consensus-evaluation.json')
    assert consensus['groups']['majority']['types']<=7
    for group in consensus['groups'].values():
        if group['type_precision'] is not None:
            assert 0<=group['type_precision']<=1
    assert measured['inventory_coverage']['missing_types']==0
    assert analyzed['attribution']['3']['offered_evaluations']>0
