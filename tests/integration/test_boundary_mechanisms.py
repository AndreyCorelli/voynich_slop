import pytest
from benchmarks.boundary_mechanisms import encoder, decode, generate


def block(words):
    return [{'folio':'a','start':0,'words':[list(w) for w in words],'positions':[i%8 for i in range(len(words))],'line_ids':[str(i//8) for i in range(len(words))]}]


def test_encoding_roundtrip_and_public_marker_schedule():
    plain=block(['abc','de','fg','hi','jk','lm','no','pq','rs','tu'])
    for dose in (.25,.5):
        cipher,key=encoder(plain,42,dose)
        assert decode(cipher,key)==plain
        for i,(p,c) in enumerate(zip(plain[0]['words'],cipher[0]['words'])):
            marked=i>0 and i%8!=0 and i%int(1/dose)==0
            assert len(c)==len(p)+int(marked)
    assert plain[0]['words'][0]==list('abc')


def test_wrong_context_marker_is_rejected():
    cipher,key=encoder(block(['ab']*8),42,.5); cipher[0]['words'][2][0]='a' if cipher[0]['words'][2][0]!='a' else 'b'
    with pytest.raises(AssertionError): decode(cipher,key)


def test_generator_uses_training_pool_not_evaluation_spellings():
    train=block(['ay','qa']*8); template=block(['zzzz']*32)
    generated=generate(train,template,{'y':'q','a':'a'},.5,43)
    assert all(''.join(w) in ('ay','qa') for w in generated[0]['words'])
    assert template[0]['words'][0]==list('zzzz')
