from voynich_smt.initial_abbreviation_context import extract_initials
from voynich_smt.unlabeled_caesar_context import extract


def test_uniform_initial_preservation_keeps_other_words_and_segment_positions():
    raw=b'<p>[1] C. Caesar ad L. Titum venit. A. c. C sine puncto?</p>'
    old,_=extract('test',raw);new,changes=extract_initials('test',raw)
    assert [(s['sent_id'],len(s['tokens'])) for s in old]==[(s['sent_id'],len(s['tokens'])) for s in new]
    assert [c['after'] for c in changes]==['c.','l.','a.']
    assert [s['tokens'][-1]['word'] for s in new][-2:]==['c','puncto']
    assert old[0]['tokens'][0]['word']=='c' and new[0]['tokens'][0]['word']=='c.'


def test_multiletter_and_nonperiod_endings_are_not_initials():
    raw=b'<p>[1] CC. C! D? C. </p>'
    ss,changes=extract_initials('test',raw)
    assert [t['word'] for s in ss for t in s['tokens']]==['cc','c','d','c.']
    assert len(changes)==1
