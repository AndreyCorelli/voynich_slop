import gzip
import json
from pathlib import Path

import pytest

from benchmarks.scalable_latin_caesar import (TOKENIZATION, anchor_evaluate, build, measure,
                                              prepare, search, sentences, sha, training, words)
from voynich_smt.word_mapping.scalable.config import ModelConfig
from voynich_smt.word_mapping.scalable.data import CipherStream, generate
from voynich_smt.word_mapping.scalable.inventory import Inventory
from voynich_smt.word_mapping.scalable.state import DictionaryState
from voynich_smt.word_mapping.scalable.trigram import load_model


def block(source, text, *, perseus=False):
    metadata=f'# sent_id = {source}.perseus-lat1.tb.xml@1' if perseus else f'# source = {source}'
    return metadata+'\n'+'\n'.join(f'{i}\t{w}\t{w}\tCCONJ\t_\t_\t0\troot\t_\t_' for i,w in enumerate(text.split(),1))+'\n\n'


def test_latin_sources_normalization_and_exclusion(tmp_path):
    assert words('JŪLIUS, VĒNIT; atque') == ('iulius','uenit','atque')
    proiel=tmp_path/'proiel.conllu'; perseus=tmp_path/'perseus.conllu'
    proiel.write_text(block('Commentarii belli Gallici, Caes., Gall. 1.1','gallia est omnis')+
                      block('De officiis, Book 1, section 1','et non sed'))
    perseus.write_text(block('phi0448.phi001','caesar uenit',perseus=True)+
                       block('phi0631.phi001','autem atque',perseus=True))
    docs,pos,audit=training([('proiel',proiel),('perseus',perseus)])
    assert docs == (('et','non','sed'),('autem','atque'))
    assert 'caesar' not in pos and 'gallia' not in pos
    assert sum(r.get('excluded_tokens',0) for r in audit.values())==5
    proiel.write_text(block('Unknown work','et non'))
    with pytest.raises(ValueError,match='Unregistered'): training([('proiel',proiel)])


def test_latin_multiword_surface_and_continuity(tmp_path):
    path=tmp_path/'mwt.conllu'
    path.write_text('# source = De officiis, Book 1\n1-2\tmecum\t_\t_\t_\t_\t_\t_\t_\t_\n'
                    '1\tme\tego\tPRON\t_\t_\t0\troot\t_\t_\n'
                    '2\tcum\tcum\tADP\t_\t_\t1\tcase\t_\t_\n\n'+
                    block('De officiis, Book 1','et non'))
    docs,_,_=training([('proiel',path)])
    assert docs == (('mecum','et','non'),)


def test_latin_independent_pipeline_and_anchor_accounting(tmp_path):
    proiel=tmp_path/'train.conllu'
    proiel.write_text(block('De officiis, Book 1','et non sed et non atque et')+
                      block('Commentarii belli Gallici, Caes., Gall. 1.1','gallia est omnis'))
    lexicon=tmp_path/'forms.gz'
    with gzip.open(lexicon,'wt') as handle: handle.write('et\nnon\nsed\natque\nest\nomnis\na\nb\nc\nd\ne\nf\ng\nh\ni\n')
    resources=tmp_path/'resources'; build(resources,paths=[('proiel',proiel)],lexicon=lexicon)
    # Target is created after resources, so build cannot have consulted it.
    source=tmp_path/'caesar.txt'
    source.write_text('*** START OF THE PROJECT GUTENBERG EBOOK CAESAR ***\nGALLIA est omnis et non sed atque et non.\n*** END OF THE PROJECT GUTENBERG EBOOK CAESAR ***\n')
    source.with_suffix('.txt.manifest.json').write_text(json.dumps({'sha256':sha(source)}))
    fixture=tmp_path/'fixture'; audit=prepare(resources,fixture,source=source,tokens=35000)
    assert audit['tokens']==9 and audit['exact_12_word_overlap_count']==0
    public=CipherStream.load(fixture/'public/cipher.json')
    assert public.tokenization==TOKENIZATION and len(public.documents)==1
    private=fixture/'evaluation-only'; private.rename(fixture/'temporarily-unavailable')
    proiel.rename(tmp_path/'unavailable-train')
    output=tmp_path/'run'
    search(resources,fixture,output,proposals=20,seeds=(3,5,7),budget=30)
    (fixture/'temporarily-unavailable').rename(private)
    result=measure(resources,fixture,output)
    assert result['primary_anchors']['types']==0
    anchors=json.loads((output/'anchors-evaluation.json').read_text())
    assert anchors['primary']['token_precision'] is None
    assert sum(r['count'] for r in anchors['rows'])==9
    assert all('possible_training_pos' in r for r in anchors['rows'])
    assert sum(b['tokens'] for b in anchors['frequency_bands'].values())==9
    assert any('Latin surface' in s for s in json.loads((output/'evaluation.json').read_text())['limitations'])
    inventory=Inventory(resources/'inventory.sqlite')
    try:
        model=load_model(resources/'model.sqlite',inventory)
        english,_=generate((('et','non'),),seed=1)
        with pytest.raises(ValueError,match='tokenization mismatch'): DictionaryState.random(english,model,seed=3)
    finally: inventory.close()
    with pytest.raises(ValueError): ModelConfig(language='la')
    with pytest.raises(ValueError): ModelConfig(tokenization=TOKENIZATION)


def test_unanimous_wrong_anchors_are_counted_as_errors(tmp_path):
    resources=tmp_path/'resources'; resources.mkdir()
    inventory=Inventory.build(resources/'inventory.sqlite',('a','b','c'))
    try:
        stream,truth=generate((('a',)*100+('b',)*101+('c',)*120,),seed=83,tokenization=TOKENIZATION)
        truth_path=tmp_path/'truth.json'; truth.save(truth_path)
        output=tmp_path/'run'; stream.save(output/'public/cipher.json')
        key=[inventory.id({'a':'a','b':'c','c':'b'}[w]) for w in truth.decoding]
        protocol={'cipher_sha256':stream.identity,'inventory_sha256':inventory.identity,
                  'search':{'initialization':'frequency'}}
        inference={'protocol':protocol,'selected_seed':3,
                   'runs':[{'seed':seed,'joint_archive':[{'assignments':key}]} for seed in (3,5,7)]}
        (output/'inference.json').write_text(json.dumps(inference))
        rows=[{'cipher':c,'word_id':word,'votes':3,'strict_majority':True,'changed_in_all_supporters':True}
              for c,word in enumerate(key)]
        (output/'consensus-public.json').write_text(json.dumps({'protocol':protocol,'rows':rows}))
        (resources/'training-pos.json').write_text(json.dumps({'a':{'CCONJ':10},'b':{'ADP':10},'c':{'NOUN':10}}))
        report=anchor_evaluate(resources,output,truth_path)
        assert report['primary']['types']==3 and report['primary']['correct_types']==1
        assert report['primary']['type_precision']==pytest.approx(1/3)
        assert report['primary']['token_precision']==pytest.approx(100/321)
        assert report['primary']['token_coverage']==1
        assert report['primary']['correct_token_coverage']==pytest.approx(100/321)
        assert report['shared_initialization_warning']
    finally: inventory.close()
