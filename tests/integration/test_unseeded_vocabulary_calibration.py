from benchmarks import unseeded_vocabulary_calibration as b
from voynich_smt.models.alphabet import Alphabet
from voynich_smt.models.text import Text
from voynich_smt.language.dictionary import WordDictionary
from voynich_smt.solver.recovery import Recovery
from voynich_smt.data.corpus import digest


def test_prefix_dictionary_disjoint_and_coverage_occurrences():
    records=[{'tokens':list(w),'excluded_reason':None} for w in ('a','b','a','b','c','d','e','f')]
    dictionary,provenance=b.dictionary_from_prefix(records,Alphabet(tuple('abcdef')),set(map(tuple,'abcdef')),2)
    assert dictionary.words==(tuple('a'),tuple('b')) and max(r['record_index'] for r in provenance)<4
    audit=b.coverage(Text.from_string('a c c'),Text.from_string('b'),dictionary)
    assert audit['missing_training_occurrences']==2 and len(audit['missing_training_types'])==1
    assert not audit['generating_explanation_admitted']


def test_no_solver_outcome_selection_resume(tmp_path,monkeypatch):
    monkeypatch.setattr(b,'OUT',tmp_path);calls=[]
    def solve(q,budget):
        calls.append((q,budget));return Recovery('UNKNOWN',.01)
    monkeypatch.setattr(b,'recover_oov',solve)
    r=b.run();p=b.prepare()
    assert len(calls)==8 and all(q.timeout_ms==60000 and budget==1 for q,budget in calls)
    for passage in p['passages'].values():
        assert max(v['record_index'] for v in passage['dictionary_provenance'])<passage['record_start']
        assert len(passage['dictionary']['words'])==256
    assert all(a['evaluation_status']=='NOT_EVALUATED_NO_SAT' for a in r['cases'])
    assert digest(b.run())==digest(r) and len(calls)==8
    b.validate()
