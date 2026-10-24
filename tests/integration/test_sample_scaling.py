import importlib.util
import json
from pathlib import Path

import pytest

from voynich_smt.data.corpus import Corpus
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.solver.recovery import Recovery


def module():
    spec=importlib.util.spec_from_file_location('sample_scaling',Path(__file__).parents[2]/'benchmarks/sample_scaling.py')
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result)
    return result


def record(tokens,folio='f1r',locus='f1r.1,@P0',uncertain=False):
    return {'tokens':list(tokens),'folio':folio,'locus':locus,'physical_line':1,
            'word_in_locus':0,'section':'H','uncertain_space_in_locus':uncertain}


def test_run_never_bridges_exclusions_folios_labels_or_uncertain_spaces():
    runner=module()
    rows=(record('x'),record(''),record('x'),record('x',folio='f1v'),
          record('x',folio='f1v',locus='f1v.1,@L0'),record('x',uncertain=True),
          record('x'),record('y'),record('xy'))
    corpus=Corpus('voynich-eva',{}, {},rows)
    assert runner.clean_run(corpus,3)==6
    with pytest.raises(ValueError,match='uninterrupted'):
        runner.clean_run(corpus,4)
    assert runner.clean_run(corpus,4,False)==5
    text,metadata=runner.sample_at(corpus,6,3)
    assert text.words==(tuple('x'),tuple('y'),tuple('xy'))
    assert metadata['record_indices']==[6,7,8]


def config(tmp_path):
    latin=Corpus('latin',{'sha256':'latin'},{'alphabet':'ab'},
                 tuple({'tokens':list(w)} for w in ['a','b','ab','ba','aa','bb']))
    eva=Corpus('voynich-eva',{'sha256':'eva'}, {},
               tuple(record(w) for w in ['xy','yx','xy','yx']))
    latin.save(tmp_path/'latin.json');eva.save(tmp_path/'eva.json')
    return {'latin':str(tmp_path/'latin.json'),'voynich':str(tmp_path/'eva.json'),'sizes':[1,2,4],
            'sample':{'strategy':'first-clean-paragraph-run','exclude_uncertain_spaces':True},
            'single_letter_words':['a','b'],'bounds':{'family':'verbose','max_homophones':2,'min_code_length':1,'max_code_length':2},
            'selection':{'mode':'cycle','reset':'text'},'timeout_ms':1000}


def test_scaling_varies_only_ciphertext_and_preserves_nested_span(tmp_path,monkeypatch):
    runner=module();cfg=config(tmp_path)
    output,artifacts=tmp_path/'results.json',tmp_path/'artifacts'
    report=runner.run(cfg,output,artifacts)
    assert report['complete']
    requests=[json.loads(Path(e['public_input']).read_text()) for e in report['experiments']]
    for a,b in zip(requests,requests[1:]):
        aw=a.pop('ciphertext');bw=b['ciphertext']
        assert aw['words']==bw['words'][:len(aw['words'])]
        assert a=={k:v for k,v in b.items() if k!='ciphertext'}
    assert all(e['result']['status']=='SAT' and e['result']['verified'] for e in report['experiments'])
    assert len({e['fixed_model_sha256'] for e in report['experiments']})==1
    assert [e['sample_metadata']['record_indices'] for e in report['experiments']]==[[0],[0,1],[0,1,2,3]]
    monkeypatch.setattr(HiddenRecoveryRequest,'solve',lambda request:pytest.fail('Resume solved an existing checkpoint'))
    assert len(runner.run(cfg,output,artifacts,True)['experiments'])==3
    cfg['timeout_ms']=2000
    with pytest.raises(ValueError,match='same configuration'):
        runner.run(cfg,output,artifacts,True)


def test_unknown_keeps_all_sizes_and_no_explanations(tmp_path,monkeypatch):
    runner=module();cfg=config(tmp_path)
    monkeypatch.setattr(HiddenRecoveryRequest,'solve',lambda request:Recovery('UNKNOWN',0.01,reason_unknown='timeout',
                        capacity={'construction_seconds':0.0}))
    report=runner.run(cfg,tmp_path/'unknown.json',tmp_path/'artifacts')
    assert report['complete'] and len(report['experiments'])==3
    assert all(e['result']['status']=='UNKNOWN' and e['result']['plaintext'] is None for e in report['experiments'])


@pytest.mark.parametrize('sizes', [[5,5],[10,5],[0,5],[],[True,5]])
def test_invalid_size_progressions_rejected(tmp_path,sizes):
    runner=module();cfg=config(tmp_path);cfg['sizes']=sizes
    with pytest.raises(ValueError,match='sizes'):
        runner.validate(cfg)
