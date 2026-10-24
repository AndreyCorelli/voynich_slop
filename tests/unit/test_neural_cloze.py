from types import SimpleNamespace
import numpy as np
import pytest
from voynich_smt.neural_cloze import ClozeCandidateBank,RepeatedCloze


class Tokenizer:
    bos_token_id=0;eos_token_id=2;mask_token_id=4
    all_special_ids=[0,1,2,3,4]
    def __call__(self,words,add_special_tokens=False):
        lookup={'in':[5],'et':[6],'a':[7],'ab':[7,8],'unknown':[3]}
        return {'input_ids':[lookup[w] for w in words] if isinstance(words,list) else lookup[words]}


def test_length_hypothesis_masks_all_same_type_occurrences_without_spelling():
    tok=Tokenizer();bank=ClozeCandidateBank(tok,('a','ab'))
    scorer=SimpleNamespace(tokenizer=tok,max_length=30)
    cloze=RepeatedCloze(scorer,bank,radius=10)
    ids,positions=cloze.job(('x','f','x','y'),'x',2,{'f':'in'},2)
    assert ids==[0,4,4,5,4,4,4,2]
    assert positions==(4,5)
    # Different hidden type identifiers change nothing in the model input.
    assert cloze.job(('x','f','x','other'),'x',2,{'f':'in'},2)==(ids,positions)
    with pytest.raises(ValueError):cloze.job(('x',),'x',0,{'x':'a'},1)
    with pytest.raises(ValueError):cloze.job(('x',),'x',0,{},0)


def test_piece_scoring_is_normalized_and_special_candidates_excluded():
    bank=ClozeCandidateBank(Tokenizer(),('a','ab','unknown'))
    assert bank.excluded==[2]
    one=np.full((1,9),-10.);two=np.full((2,9),-10.)
    one[0,7]=-3.;two[0,7]=-1.;two[1,8]=-2.
    scores=bank.scores({1:one,2:two})
    assert scores[:2]==pytest.approx([-3.,-1.5])
    assert scores[2]==-np.inf
    with pytest.raises(ValueError):bank.scores({1:one,2:one})


def test_every_occurrence_is_scored_and_pooled_without_gold():
    bank=ClozeCandidateBank(Tokenizer(),('a','ab'))
    cloze=RepeatedCloze(SimpleNamespace(tokenizer=Tokenizer(),max_length=30),bank,radius=1)
    seen=[]
    def distributions(jobs):
        seen.append(jobs)
        return [np.full((len(p),9),-float(i+1)) for i,(_,p) in enumerate(jobs)]
    cloze.distributions=distributions
    result=cloze.rank_scores((('x','f','x'),('x',)),'x',{'f':'in'})
    assert result['occurrences']==3
    assert result['pooled']==pytest.approx([-2.,-2.])
    assert result['first_occurrence']==pytest.approx([-1.,-1.])
    assert len(seen)==2 and all(len(jobs)==3 for jobs in seen)
