from benchmarks.line_context_prediction import fit, probability, evaluate, permutation, position_bin, stratum


def block():
    words=['a','b','a','b']*16
    return {'folio':'f','start':0,'words':[list(w) for w in words],'line_ids':[str(i//4) for i in range(64)],'positions':[i%4 for i in range(64)]}


def test_line_gate_distinguishes_boundary_and_no_context():
    b=block()
    assert stratum(b,0)=='block-start' and stratum(b,1)=='within' and stratum(b,4)=='cross'
    m=fit([b],{'position':4,'gate':'within'})
    assert sum(sum(row.values()) for row in m['transitions'].values())==48


def test_position_probability_normalizes():
    b=block(); model=fit([b],{'position':4,'gate':'within'})
    for i in range(8):
        total=0
        for word in model['vocabulary']:
            target={**b,'words':list(b['words'])}; target['words'][i]=list(word)
            total+=probability(target,i,model)
        assert abs(total-1)<1e-12


def test_position_preserving_shuffle_leaves_baseline_log_loss_fixed():
    b=block(); shuffled=permutation(b,3)
    from collections import Counter
    for pos in ('0','1','2-3','4+'):
        assert Counter(tuple(w) for i,w in enumerate(b['words']) if position_bin(b['positions'][i],4)==pos)==Counter(tuple(w) for i,w in enumerate(shuffled['words']) if position_bin(b['positions'][i],4)==pos)
    spec={'position':4,'gate':'none'}
    a=evaluate([b],[b],spec)[0]; c=evaluate([b],[shuffled],spec)[0]
    assert abs(sum(t['loss'] for t in a['tokens'])-sum(t['loss'] for t in c['tokens']))<1e-10
