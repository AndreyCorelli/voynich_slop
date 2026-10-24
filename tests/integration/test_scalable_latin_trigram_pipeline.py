import json
from itertools import product

import pytest

from benchmarks.scalable_english_run import run
from benchmarks.scalable_english_evaluate import evaluate
from benchmarks.scalable_latin_trigram import score_variants
from voynich_smt.word_mapping.scalable.inventory import Inventory
from voynich_smt.word_mapping.scalable.trigram import InterpolatedTrigram,load_model
from voynich_smt.word_mapping.scalable.config import ModelConfig
from voynich_smt.word_mapping.scalable.data import generate
from voynich_smt.word_mapping.scalable.search import SearchConfig
from voynich_smt.word_mapping.scalable.retrieval import RetrievalConfig


def test_latin_trigram_contract_controls_and_public_only_pipeline(tmp_path):
    resources=tmp_path/'resources';resources.mkdir()
    inv=Inventory.build(resources/'inventory.sqlite',('et','in','puella','puellam','uenit','amat','nouum'))
    try:
        docs=[tuple(map(inv.id,d)) for d in [('puella','uenit','et','puella','amat'),('puellam','amat','et','uenit')]]
        cfg=ModelConfig(language='la',tokenization='latin-iu-continuous-v1')
        model=InterpolatedTrigram.train(inv,lambda:iter(docs),config=cfg)
        assert model.config==cfg
        for a,b in product(range(-1,inv.size),repeat=2):
            assert sum(model.probability3(a,b,c) for c in range(inv.size+1))==pytest.approx(1.)
        sequence=tuple(inv.id(w) for w in ('puella','uenit','et','nouum','amat'))
        scores=score_variants(model,sequence,(.25,.5,.75))
        assert scores['bigram']==pytest.approx(model.bigram.score(sequence))
        for weight in (.25,.5,.75):
            model.weight=weight
            assert scores[str(weight)]==pytest.approx(model.score(sequence))
        model.weight=.5;model.save(resources/'model.sqlite')
        assert load_model(resources/'model.sqlite',inv).config==cfg
        stream,truth=generate((('puella','uenit','et','puella','amat'),),seed=83,tokenization='latin-iu-continuous-v1')
        public=tmp_path/'public/cipher.json';stream.save(public)
        output=tmp_path/'run'
        inference=run(resources,public,output,seeds=(3,5,7),config=SearchConfig(proposals=20),
                      retrieval=RetrievalConfig(active_limit=5,total_entries=20,per_context=3),trace=True)
        assert all(r['step']==20 for r in inference['runs'])
        private=tmp_path/'evaluation-only/truth.json';truth.save(private)
        metrics=evaluate(resources,output,private)
        assert len(metrics['runs'])==3 and metrics['tokens']==5
        assert not (output/'evaluation-only').exists()
    finally:inv.close()
