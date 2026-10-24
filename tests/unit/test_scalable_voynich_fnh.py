from collections import Counter
import pytest
from benchmarks.scalable_voynich_fruehneuhochdeutsch import segments,split_at,shuffled
from voynich_smt.word_mapping.scalable.data import CipherStream


def record(raw,*,folio='f1r',index=0,excluded=False):
    return {'raw':raw,'tokens':list(raw) if not excluded else [],'folio':folio,'locus':folio+'.1',
            'word_in_locus':index,'excluded_reason':'unclear' if excluded else None}


def test_no_adjacency_across_ambiguous_words_or_folio_boundaries():
    docs,positions=segments([record('daiin'),record('?',index=1,excluded=True),record('ol',index=2),record('chedy',folio='f1v')])
    assert docs==(('daiin',),('ol',),('chedy',))
    assert positions[1][0]['word_in_locus']==2
    with pytest.raises(ValueError,match='Multiple transcription'):
        segments([record('daiin'),record('ol')])


def test_half_split_keeps_every_word_without_joining_real_gaps():
    left,right=split_at(((0,1),(2,3,4),(5,)),3)
    assert left==((0,1),(2,)) and right==((3,4),(5,))
    assert [w for doc in left+right for w in doc]==list(range(6))


def test_shuffle_cancels_count_and_endpoint_hints_but_changes_order():
    stream=CipherStream((tuple(range(20)),(0,1),(2,)),20,tokenization='ref-historical-continuous-v1')
    control=shuffled(stream,2701)
    assert control==shuffled(stream,2701)
    assert control.documents!=stream.documents
    assert Counter(c for d in control.documents for c in d)==Counter(c for d in stream.documents for c in d)
    assert all((a[0],a[-1],len(a))==(b[0],b[-1],len(b)) for a,b in zip(stream.documents,control.documents))
