from collections import Counter
import json

from benchmarks.scalable_english_run import run
from benchmarks.scalable_latin_caesar import measure, TOKENIZATION
from voynich_smt.word_mapping.scalable.association import AssociationModel, pair_counts
from voynich_smt.word_mapping.scalable.config import ModelConfig
from voynich_smt.word_mapping.scalable.data import generate
from voynich_smt.word_mapping.scalable.inventory import Inventory
from voynich_smt.word_mapping.scalable.sparse_lm import SparseBigram
from voynich_smt.word_mapping.scalable.search import SearchConfig


def test_profile_association_public_only_full_pipeline(tmp_path):
    resources=tmp_path/'resources';resources.mkdir()
    inventory=Inventory.build(resources/'inventory.sqlite',('a','et','in','non','sed'))
    docs=((0,1,0,2,1,0),(3,1,2,0,3),(1,3,0,2))
    try:
        bigram=SparseBigram.train(inventory,docs,config=ModelConfig(language='la',tokenization=TOKENIZATION))
        pairs=Counter()
        for doc in docs:pairs.update(pair_counts(doc,(1,2,4)))
        model=AssociationModel(bigram,pairs);model.save(resources/'model.sqlite')
    finally:inventory.close()
    (resources/'report.json').write_text(json.dumps({'limitations':['Tiny independent test source.']}))
    (resources/'training-pos.json').write_text('{}')
    public,truth=generate((('et','a','non','et','in','a','et'),),seed=83,tokenization=TOKENIZATION)
    fixture=tmp_path/'fixture';public.save(fixture/'public/cipher.json');truth.save(fixture/'evaluation-only/truth.json')
    (fixture/'evaluation-only').rename(tmp_path/'private-unavailable')
    output=tmp_path/'run'
    run(resources,fixture/'public/cipher.json',output,seeds=(3,5,7),
        config=SearchConfig(initialization='profile',proposals=30),trace=True)
    (tmp_path/'private-unavailable').rename(fixture/'evaluation-only')
    measured=measure(resources,fixture,output)
    inference=json.loads((output/'inference.json').read_text())
    assert all(r['step']==30 for r in inference['runs'])
    assert 'not likelihood' in inference['protocol']['scope']
    assert measured['primary_anchors']['types']==0
    evaluation=json.loads((output/'evaluation.json').read_text())
    assert all(r['score_selected_best']['score']<=0 for r in evaluation['runs'])
