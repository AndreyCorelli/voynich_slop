import numpy as np
import pytest
from voynich_smt.marker_structure import (MarkerModel,marker_choices,attachment_features,
    infer_attached_links,validate_markers)
from voynich_smt.predicate_structure import morph_features,validate_structure
from tests.unit.test_predicate_structure import Adapter


class Nearest:
    def logits(self,rows):
        start=1+3+3*len(morph_features(()))
        return np.array([-100*r[start]+10*r[start+5]-r[start+3] for r in rows])


class Constant:
    def logits(self,rows):return np.zeros(len(rows))


def test_marker_has_one_target_and_normalized_alternatives():
    model=MarkerModel({'et':['coordination']},Nearest())
    rows=model.predict(['a','et','b','c'],[0,3],Adapter())
    assert len(rows)==1 and rows[0]['position']==1 and rows[0]['target']==0
    assert set(r['target'] for r in rows[0]['alternatives'])=={None,0,3}
    assert np.isclose(sum(r['probability'] for r in rows[0]['alternatives']),1)


def test_chosen_predicate_cannot_simultaneously_supply_marker_evidence():
    model=MarkerModel({'a':['subordination']},Nearest())
    rows=model.predict(['a','b'],[0,1],Adapter())
    assert rows[0]['target'] is None and len(rows[0]['alternatives'])==1


def test_marker_scope_respects_supplied_boundary():
    model=MarkerModel({'et':['coordination']},Nearest())
    rows=model.predict(['a','et','b','c'],[0,3],Adapter(),[2,4])
    assert set(r['target'] for r in rows[0]['alternatives'])=={None,0}


def test_duplicate_marker_evidence_has_no_count_bonus():
    adapter=Adapter();tokens=['a','et','b'];pred=[0,2]
    morph=[morph_features(adapter.analyze(w)) for w in tokens]
    marker={'position':1,'target':2,'kinds':['coordination']}
    first=attachment_features(tokens,2,0,pred,morph,'coordination',[marker],True)
    duplicate=attachment_features(tokens,2,0,pred,morph,'coordination',[marker,dict(marker)],True)
    assert first==duplicate


def test_end_to_end_hard_marker_witness_and_forest_coverage():
    marker=MarkerModel({'et':['coordination']},Nearest())
    result=infer_attached_links(['a','et','b'],[0,2],Adapter(),Constant(),marker,interactions=True)
    assert result['status']=='optimal' and validate_structure(result) and validate_markers(result)
    assert result['tokens']==len(result['token_anchors'])==3
    assert result['forest_score_integer']==0
    assert len(result['marker_attachments'])==1
    assert sum(m['target'] is not None for m in result['marker_attachments'])==1


def test_marker_validator_rejects_duplicate_positions_and_bad_inputs():
    marker=MarkerModel({'et':['coordination']},Nearest())
    result=infer_attached_links(['a','et','b'],[0,2],Adapter(),Constant(),marker)
    result['marker_attachments']*=2
    with pytest.raises(AssertionError):validate_markers(result)
    with pytest.raises(ValueError):infer_attached_links(['a','b'],[1,0],Adapter(),Constant(),marker)
    with pytest.raises(ValueError):infer_attached_links(['a','b'],[0],Adapter(),Constant(),marker,boundaries=[1])
