import pytest

pytest.importorskip('torch')

from benchmarks.word_mapping_cloze_finetune import scaffold


def test_scaffold_keeps_target_hidden_and_is_nested():
    decoding={f'c{i}':f'w{i}' for i in range(100)}
    anchors={'c0':'w0','c1':'w1'}
    previous=set()
    for fraction in (0,.1,.25,.5,1):
        visible=scaffold(decoding,anchors,'c2',fraction)
        assert 'c2' not in visible
        assert previous<=set(visible)
        assert all(decoding[c]==w for c,w in visible.items())
        assert len(visible)==2+int(fraction*97)
        previous=set(visible)


def test_scaffold_removes_target_even_if_supplied_as_anchor():
    assert scaffold({'a':'one','b':'two'},{'a':'one'},'a',1)=={'b':'two'}


def test_loss_weights_examples_equally_despite_piece_count():
    from types import SimpleNamespace
    import torch
    from benchmarks.word_mapping_cloze_finetune import loss
    class Model:
        def roberta(self,input_ids,attention_mask):
            return SimpleNamespace(last_hidden_state=torch.nn.functional.one_hot(input_ids,num_classes=3).float())
        def lm_head(self,hidden):return hidden*2
    examples=[{'ids':[0,1],'positions':[0],'labels':[0]},
              {'ids':[0,1],'positions':[0,1],'labels':[1,0]}]
    actual=loss(Model(),SimpleNamespace(pad_token_id=2),examples)
    first=torch.nn.functional.cross_entropy(torch.tensor([[2.,0.,0.]]),torch.tensor([0]))
    second=torch.nn.functional.cross_entropy(torch.tensor([[2.,0.,0.],[0.,2.,0.]]),torch.tensor([1,0]))
    assert torch.allclose(actual,(first+second)/2)
