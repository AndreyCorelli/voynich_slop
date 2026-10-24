from benchmarks.joint_predictor_calibration import blend, score
from benchmarks.joint_order_constraints import optimize
from benchmarks.adjacent_order_validation import inventory


def test_blend_preserves_block_constraints_and_endpoints():
    blocks=[{'words':[list(w) for w in ('ab','ab','ba','ba')],'positions':[4]*4,'line_ids':['x']*4}]
    reordered=optimize(blocks,{'b':'b','a':'a'},7,True)
    assert blend(blocks,reordered,0,11)==blocks
    assert blend(blocks,reordered,1,11)==reordered
    assert inventory(blend(blocks,reordered,.5,11)[0])==inventory(blocks[0])


def test_score_uses_refitted_null_difference():
    b={'words':[list(w) for w in ('ab','ba','ab','ba')],'positions':[4]*4,'line_ids':['x']*4,'folio':'f','start':0}
    r=score([b],[b],{'order':2,'strength':10,'position':4,'gate':'all'},(17,))
    assert r['excess']==r['active']['gain_position']-r['nulls'][0]['gain_position']
