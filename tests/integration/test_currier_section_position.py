from benchmarks.currier_section_position import collect,line_role,position

def test_roles_require_explicit_markers():
    assert line_role('<%>abc<$>')=='single'
    assert line_role('<%>abc')=='initial'
    assert line_role('abc<$>')=='final'
    assert line_role('abc')=='unmarked'
    assert [position(i,3) for i in range(3)]==['first','interior','last']

def test_exclusion_never_moves_word_to_line_boundary():
    def record(w,i,bad=False):return {'folio':'f1r','locus':'f1r.1,+P0','page_variables':{'L':'A'},'section':'H','tokens':list(w),'excluded_reason':'bad' if bad else None,'word_in_locus':i,'raw_locus_text':'<%>x.abc.y'}
    rs=[record('x',0,True),record('abc',1),record('y',2,True)]
    out=collect(rs,'clean-words','atomic')
    assert len(out)==1 and out[0]['word_position']=='interior' and out[0]['line_role']=='initial'
    assert not collect(rs,'whole-clean-lines','atomic')

def test_standardization_removes_composition_only_difference():
    from benchmarks.currier_section_position import standardize
    rows=[]
    for label in ('A','B'):
        for i in range(5):
            for role,length,count in [('initial',8,10 if label=='A' else 2),('unmarked',4,2 if label=='A' else 10)]:
                rows.extend({'folio':label+str(i),'currier':label,'section':'H','line_role':role,'length':length} for _ in range(count))
    result=standardize(rows,['section','line_role'],['H'])
    assert result['B_minus_A']==0
    assert result['standardized_means']=={'A':6,'B':6}
    assert result['contrast_percentile_95_interval']==[0,0]
