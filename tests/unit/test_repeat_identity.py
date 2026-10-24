from types import SimpleNamespace
import pytest
import numpy as np

torch=pytest.importorskip('torch')
from voynich_smt.neural_cloze import RepeatedCloze
from voynich_smt.repeat_identity import IdentityCloze,pack,adapter_for

class Tokenizer:
    bos_token_id=0;eos_token_id=2;mask_token_id=4;pad_token_id=1
    all_special_ids=[0,1,2,3,4]
    def __call__(self,word,add_special_tokens=False):return {'input_ids':[5]}

def cloze(mode='repeat',seed=941):
    scorer=SimpleNamespace(tokenizer=Tokenizer(),max_length=100)
    return IdentityCloze(scorer,None,None,mode=mode,seed=seed)

def test_repeat_slots_preserve_equality_and_do_not_change_mask_inputs():
    c=cloze();s=('x','y','x','y','f');visible={'f':'in'}
    ids,positions,slots=c.job(s,'x',2,visible,2)
    assert (ids,positions)==RepeatedCloze(c.scorer,None).job(s,'x',2,visible,2)
    assert slots[1]==slots[2]==slots[4]==slots[5]!=0
    assert slots[3]==slots[6]!=slots[1]
    assert slots[0]==slots[7]==slots[8]==0
    assert slots[positions[0]]==slots[positions[1]]
    with pytest.raises(ValueError):c.job(s,'x',2,{'x':'answer'},2)

def test_anonymous_relation_survives_renaming_and_randomization():
    c=cloze();s=('x','y','x','y');a=c.job(s,'x',2,{},1)[2]
    renamed=c.job(('z','a','z','a'),'z',2,{},1)[2]
    assert np.array_equal(np.equal.outer(a,a),np.equal.outer(renamed,renamed))
    b=cloze(seed=942).job(s,'x',2,{},1)[2]
    assert a!=b
    assert np.array_equal(np.equal.outer(a,a),np.equal.outer(b,b))

def test_collapsed_and_broken_controls():
    s=('x','y','x','y')
    assert not any(cloze('collapsed').job(s,'x',2,{},2)[2])
    slots=cloze('broken').job(s,'x',2,{},2)[2]
    assert slots[1]==slots[2] and slots[4]==slots[5]
    assert slots[1]!=slots[4]

def test_batch_padding_and_zero_adapter_row():
    c=cloze();jobs=[c.job(('x','y','x'),'x',2,{},2),c.job(('x',),'x',0,{},1)]
    ids,attention,identity,rows,places=pack(jobs,1)
    assert ids.shape==attention.shape==identity.shape
    assert torch.all(identity[attention==0]==0)
    assert len(rows)==len(places)==3
    adapter=adapter_for(SimpleNamespace(config=SimpleNamespace(hidden_size=4)))
    assert torch.equal(adapter(torch.tensor([0])),torch.zeros(1,4))

def test_enriched_sampler_is_matched_and_keeps_repetition_visible():
    from collections import Counter
    from benchmarks.word_mapping_repeat_identity_enriched import examples_for
    def entry(pos):return [{'enclitic':None,'inflections':[{'part_of_speech':pos,'features':{}}]}]
    segments=[('x','f','y','x','z','y','f','z')]
    entries={w:entry('PREP' if w=='f' else 'N') for w in ('x','y','z','f')}
    repeat=examples_for(segments,entries,cloze(),30,941)
    collapsed=examples_for(segments,entries,cloze('collapsed'),30,941)
    assert [{k:v for k,v in e.items() if k!='identity'} for e in repeat]==[{k:v for k,v in e.items() if k!='identity'} for e in collapsed]
    assert repeat==examples_for(segments,entries,cloze(),30,941)
    for e in repeat:
        counts=Counter(e['identity']);target=e['identity'][e['positions'][0]]
        if e['category']=='repeated_target':assert counts[target]>len(e['labels'])
        if e['category']=='repeated_other':assert any(v>=2 for k,v in counts.items() if k not in (0,target))
