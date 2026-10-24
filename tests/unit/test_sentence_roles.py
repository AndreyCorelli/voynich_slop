import torch
from voynich_smt.sentence_roles import SentenceRoles,Encoder,head_bin,reading_features


def test_expected_roles_exclude_target_including_morphology():
    torch.manual_seed(3)
    entries={'terra':[{'inflections':[{'part_of_speech':'N','features':{'Case':'NOM'}}]}],
             'terram':[{'inflections':[{'part_of_speech':'N','features':{'Case':'ACC'}}]}]}
    encoder=Encoder(entries,['UNKNOWN','POS:N','Case:NOM','Case:ACC'])
    model=SentenceRoles([('N',),('V',)],['root'],encoder.morphology).eval()
    with torch.no_grad():
        a=model(*encoder.batch([['in','terra','sumus'],['a','b']]))[0]
        b=model(*encoder.batch([['in','terram','sumus'],['a','b']]))[0]
    assert torch.equal(a[0,1],b[0,1])
    assert not torch.equal(a[0,0],b[0,0])
    assert torch.equal(a[1],b[1])


def test_sentence_wide_context_reaches_beyond_three_words():
    torch.manual_seed(4);encoder=Encoder({},['UNKNOWN'])
    model=SentenceRoles([('N',),('V',)],['root'],encoder.morphology).eval()
    words=['a']*10;changed=words.copy();changed[9]='different'
    with torch.no_grad():a=model(*encoder.batch([words]))[0];b=model(*encoder.batch([changed]))[0]
    assert not torch.equal(a[0,0],b[0,0])


def test_head_targets_remap_removed_punctuation_and_missing_heads():
    ts=[{'id':1,'head':0},{'id':3,'head':1},{'id':5,'head':2}]
    assert head_bin(ts,0)==0
    assert head_bin(ts,1)==1
    assert head_bin(ts,2)==-100


def test_morphological_context_keeps_both_ambiguous_readings():
    entries={'x':[{'inflections':[{'part_of_speech':'N','features':{'Case':'NOM'}},{'part_of_speech':'N','features':{'Case':'ACC'}}]}]}
    assert reading_features(entries,'x')=={'POS:N','Case:NOM','Case:ACC'}
