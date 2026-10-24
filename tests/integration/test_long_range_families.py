from benchmarks.long_range_families import generate,rows


def test_mapped_copy_trace_respects_key_and_line_boundaries():
    blocks,key=generate(7,'mapped-lag8','train')
    assert len(set(key.values()))==26 and any(a!=b for a,b in key.items())
    copies=0
    for b in blocks:
        for i,operation in enumerate(b['operations']):
            if operation=='mapped8':
                assert b['positions'][i]>=8 and b['lines'][i]==b['lines'][i-8]
                assert b['words'][i][0]==key[b['words'][i-8][-1]]; copies+=1
    assert copies>100


def test_template_oracle_only_adds_current_phase_to_baseline():
    blocks,_=generate(7,'template','train'); base=rows(blocks); oracle=rows(blocks,'phase')
    phases=[b['phases'][i] for b in blocks for i in range(32) if b['positions'][i]>=8]
    for a,b,phase in zip(base,oracle,phases):
        assert b=={**a,'pos':a['pos']+f':phase{phase}'}
    assert all(op=='template' for b in blocks for op in b['operations'])
