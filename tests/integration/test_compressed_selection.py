from benchmarks.latin_h2_compressed_replication import choose_mode


def test_selection_prefers_resolved_large_fit_then_runtime():
    trials = {'a': {'small': {'status': 'SAT'}, 'large': {'status': 'UNKNOWN', 'construction': .01}},
              'b': {'small': {'status': 'SAT'}, 'large': {'status': 'SAT', 'elapsed': 5}},
              'c': {'small': {'status': 'SAT'}, 'large': {'status': 'SAT', 'elapsed': 3}}}
    assert choose_mode(trials) == 'c'


def test_selection_excludes_unresolved_regression_and_uses_construction():
    trials = {'a': {'small': {'status': 'UNKNOWN'}, 'large': {'status': 'UNKNOWN', 'construction': .01}},
              'b': {'small': {'status': 'SAT'}, 'large': {'status': 'UNKNOWN', 'construction': 2}},
              'c': {'small': {'status': 'SAT'}, 'large': {'status': 'UNKNOWN', 'construction': 3}}}
    assert choose_mode(trials) == 'b'
