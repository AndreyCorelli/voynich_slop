import json

import pytest

from benchmarks.scalable_english_independent import AUSTEN, WELLS, build, cmu_forms, prepare


def test_independent_resources_and_missing_form_evaluation(tmp_path):
    from benchmarks.scalable_english_run import run
    from benchmarks.scalable_english_evaluate import evaluate
    from benchmarks.scalable_english_diagnostics import analyze
    from benchmarks.scalable_english_diagnostics_validate import validate
    from voynich_smt.word_mapping.scalable.search import SearchConfig
    from voynich_smt.word_mapping.scalable.retrieval import RetrievalConfig
    ewt = tmp_path/'train.conllu'
    ewt.write_text('# newdoc id = x\n# text = The dog sees the cat.\n')
    austen = tmp_path/'austen.txt'
    austen.write_text('Front matter\n'+AUSTEN+' the cat.\n*** END OF THE PROJECT GUTENBERG EBOOK TEST ***')
    lexicon = tmp_path/'cmu.dict'
    lexicon.write_text('cat K AE1 T\ncat(2) K AE1 T\nno N OW1\none W AH1 N\nwould W UH1 D\nhave HH AE1 V\nbelieved B IH0 L IY1 V D\n')
    resources = tmp_path/'resources'
    built = build(ewt, austen, lexicon, resources)
    before = (resources/'inventory.sqlite').read_bytes()
    target = tmp_path/'wells.txt'
    target.write_text('Editorial matter\n'+WELLS+' unseenmonster sleeps with the dog.\n*** END OF THE PROJECT GUTENBERG EBOOK TEST ***')
    fixture = tmp_path/'fixture'
    with pytest.raises(ValueError, match='shorter'):
        prepare(resources,target,tmp_path/'too-short',tokens=100)
    assert not (tmp_path/'too-short').exists()
    audit = prepare(resources,target,fixture,tokens=10)
    assert audit['coverage']['missing_types'] == 3  # unseenmonster, sleeps, with
    assert audit['coverage']['missing_tokens'] == 3
    assert audit['overlap_audit']['matching_distinct_windows'] == 0
    assert (resources/'inventory.sqlite').read_bytes() == before
    public_text = (fixture/'public/cipher.json').read_text()
    assert 'unseenmonster' not in public_text and 'wells' not in public_text
    # Inference must work with source and truth files physically unavailable.
    truth = fixture/'evaluation-only/truth.json'
    hidden = truth.read_bytes()
    truth.unlink()
    target.unlink()
    retrieval = RetrievalConfig(active_limit=4,total_entries=40)
    for initialization in ('random','frequency'):
        root = tmp_path/initialization
        run(resources,fixture/'public/cipher.json',root,seeds=(3,),
            config=SearchConfig(initialization=initialization,proposals=30),
            retrieval=retrieval,trace=True)
        truth.write_bytes(hidden)
        evaluation = evaluate(resources,root,truth)
        assert evaluation['inventory_coverage']['missing_tokens'] == 3
        assert evaluation['inventory_coverage']['token_ceiling'] == 7/10
        report = analyze(resources,root,truth,root/'traces',root/'analysis')
        assert report['attribution']['3']['categories']['inventory_absent'] == 3
        assert validate(resources,root,truth,root/'traces',root/'analysis')['status'] == 'validated'
        if initialization == 'frequency':
            assert evaluation['runs'][0]['initial'] == evaluation['frequency_baseline']
        truth.unlink()
    from benchmarks.scalable_english_compare_initialization import compare
    compared = compare(tmp_path/'random',tmp_path/'frequency',tmp_path/'comparison.json')
    assert compared['methods']['frequency']['inventory_coverage']['missing_types'] == 3
    assert compared['methods']['frequency']['mean_initial_token_accuracy'] == evaluation['frequency_baseline']['token_accuracy']
    confounded_path = tmp_path/'frequency/inference.json'
    confounded = json.loads(confounded_path.read_text())
    confounded['protocol']['search']['frequency_mix'] = .25
    confounded_path.write_text(json.dumps(confounded))
    with pytest.raises(AssertionError, match='more than'):
        compare(tmp_path/'random',tmp_path/'frequency',tmp_path/'confounded.json')
    assert built['inventory_forms'] >= audit['types']
    # Frozen training inputs cannot silently change after resource construction.
    ewt.write_text(ewt.read_text()+'\n# changed\n')
    target.write_text(WELLS+' changed.\n*** END OF THE PROJECT GUTENBERG EBOOK TEST ***')
    with pytest.raises(ValueError, match='changed'):
        prepare(resources,target,tmp_path/'changed',tokens=3)


def test_lexicon_variants(tmp_path):
    lexicon = tmp_path/'dict'
    lexicon.write_text(";;; comment\nCAT(2) K AE1 T\nwell-known W EH1 L\ncan't K AE1 N T\n")
    assert list(cmu_forms(lexicon)) == ['cat','well','known',"can't"]


def test_pinned_prose_anchor_can_cross_a_wrapped_line(tmp_path):
    from benchmarks.scalable_english_independent import prose
    source=tmp_path/'source'
    source.write_text('Front matter\nMr. Sherlock Holmes, who was usually\nvery late in the mornings, continued.\n'
                      '*** END OF THE PROJECT GUTENBERG EBOOK TEST ***')
    body,start=prose(source,'Mr. Sherlock Holmes, who was usually very late in the mornings')
    assert start==len('Front matter\n')
    assert body.startswith('Mr. Sherlock Holmes')
    assert 'Front matter' not in body
    with pytest.raises(ValueError,match='anchors'):
        prose(source,'A nonexistent incipit')
