from collections import Counter
from benchmarks.currier_mechanism_transfer import outsiders

def test_outside_generators_conservation_and_reversible_marker_rules():
    payload=[[tuple('abc'),tuple('ca')],[tuple('bac')]]
    arms=outsiders(payload,tuple('abc'),7)
    assert [[w[::2] for w in l] for l in arms['fixed-two']]==payload
    assert [[w[:-1] for w in l] for l in arms['word-final-marker']]==payload
    flat=lambda lines:[g for l in lines for w in l for g in w]
    assert Counter(flat(arms['glyph-shuffle']))==Counter(flat(payload))
    assert [len(w) for l in arms['glyph-shuffle'] for w in l]==[len(w) for l in payload for w in l]
    for name in ('renewal-4','renewal-8'):
        assert [[g for w in l for g in w] for l in arms[name]]==[[g for w in l for g in w] for l in payload]
