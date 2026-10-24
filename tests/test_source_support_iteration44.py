from pathlib import Path
from benchmarks.grammar_source_support_iteration44 import OUT,RESERVE,load,fold
from benchmarks.grammar_source_support_iteration44_validate import strings_with_keys


def test_fresh_source_ids_exclude_prior_keys_values_and_reserve():
    used=set()
    for path in load(OUT/'selection-manifest.json')['prior_declarations']:used.update(strings_with_keys(load(Path(path))))
    reserve={r['sent_id'] for rows in load(RESERVE)['authors'].values() for r in rows};data=load(OUT/'annotations-truth.json')
    assert len(data)==4070 and not set(data)&(used|reserve)
    assert {s['author'] for s in data.values()}=={'Cicero','Palladius'}


def test_sentence_holdout_keeps_every_construction_of_sentence_together():
    records=load(OUT/'records-truth.json')
    for model in load(OUT/'models.json'):
        if model['scheme']=='sentence':
            assert not set(model['train_ids'])&set(model['test_ids'])
            assert all(fold(sid)==model['group'] for sid in model['test_ids'])
    assert len(records)==879


def test_purged_predicate_holdout_has_neither_sentence_nor_predicate_overlap():
    rows=load(OUT/'records-truth.json')
    for model in load(OUT/'purged-models.json'):
        train=[rows[i] for i in model['train_ix']];test=[rows[i] for i in model['test_ix']]
        assert not {r['sent_id'] for r in train}&{r['sent_id'] for r in test}
        assert not {r['predicate'] for r in train}&{r['predicate'] for r in test}
        assert all(fold(r['predicate'])==model['group'] for r in test)


def test_support_gate_and_held_author_evaluation_match_frozen_definition():
    audit=load(OUT/'audit.json');rows=load(OUT/'records-truth.json')
    assert audit['fit_gate_passed'] and audit['mixed_examples']==261 and audit['mixed_lemmas']==38
    for model in load(OUT/'models.json'):
        if model['scheme']=='author':
            train=set(model['train_ids']);test=set(model['test_ids'])
            assert all((r['author']==model['group'])==(r['sent_id'] in test) for r in rows)
            assert not train&test
