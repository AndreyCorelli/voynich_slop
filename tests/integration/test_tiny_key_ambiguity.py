from benchmarks import tiny_key_ambiguity as benchmark
from benchmarks.l3_conflict import verify
from voynich_smt.experiments.hidden import HiddenRecoveryRequest


def test_used_mapping_signature_ignores_unused_codes_and_slot_order():
    first={'plaintext':{'words':[['a']]},'choices':[0],
           'encoder':{'codebook':{'a':[['x'],['y']],'b':[['z']]}}}
    second={'plaintext':{'words':[['a']]},'choices':[1],
            'encoder':{'codebook':{'a':[['w'],['x']],'b':[['q']]}}}
    assert benchmark.used_mappings(first)==benchmark.used_mappings(second)==[{'symbol':'a','code':('x',)}]


def test_capped_explanations_are_distinct_verified_and_coverage_is_complete(tmp_path,monkeypatch):
    monkeypatch.setattr(benchmark,'OUT',tmp_path)
    report=benchmark.run();q=HiddenRecoveryRequest.from_dict(report['request'])
    verify(q,report['generating_truth'])
    assert report['all_six_generating_homophones_seen_in_training']
    assert len(benchmark.used_mappings(report['generating_truth']))==6
    assert report['generating_score']['dictionary_words']==4
    signatures=set()
    for row in report['solutions']:
        verify(q,row['result']);signatures.add(row['used_mappings_sha256'])
    assert len(signatures)==len(report['solutions'])
    assert len(report['solutions'])<=6 and report['complete']
    # Predictions differ despite identical fitted observations and complete true-code coverage.
    assert len({row['prediction']['dictionary_words'] for row in report['solutions']})>1
