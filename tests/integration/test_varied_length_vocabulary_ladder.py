from dataclasses import asdict
import pytest
from benchmarks import varied_length_vocabulary_ladder as b
from voynich_smt.data.corpus import digest
from voynich_smt.language.dictionary import WordDictionary
from voynich_smt.models.alphabet import Alphabet
from voynich_smt.solver.recovery import Recovery


def test_corpus_order_nested_alphabet_and_exclusion_filtering():
    base=WordDictionary.from_strings(('a',));alphabet=Alphabet(('a','b'))
    records=[{'tokens':list(word),'excluded_reason':reason} for word,reason in
             [('c',None),('a',None),('b',None),('aa','excluded'),('ab',None),('b',None)]]
    dictionaries,provenance=b.vocabularies(base,alphabet,records,(2,3))
    assert dictionaries[2].words==tuple(map(tuple,('a','b')))
    assert dictionaries[3].words==tuple(map(tuple,('a','b','ab')))
    assert [row['record_index'] for row in provenance]==[2,4]
    with pytest.raises(ValueError,match='Insufficient'):b.vocabularies(base,alphabet,records,(4,))
    with pytest.raises(ValueError,match='Invalid'):b.vocabularies(base,alphabet,records,(3,2))


def test_only_dictionary_changes_baselines_reused_unknown_and_resume(tmp_path,monkeypatch):
    monkeypatch.setattr(b,'OUT',tmp_path);received=[]
    def spy(q):
        received.append(q);return Recovery('UNKNOWN',0.01,reason_unknown='forced')
    monkeypatch.setattr(b,'recover_observed_codes',spy)
    r=b.run();source,p=b.prepare()
    assert len(received)==12 and len(p['reused_baselines'])==6
    for q,case in zip(received,p['cases']):
        original=next(c for c in source['cases'] if c['id']==case['source_case'])
        before=dict(original['request']);after=asdict(q)
        before.pop('dictionary');after.pop('dictionary')
        assert digest(before)==digest(after)
        assert len(q.dictionary.words)==case['vocabulary_size'] and q.timeout_ms==5000
    assert all(row['evaluation_status']=='NOT_EVALUATED_NO_SAT' and 'prediction' not in row for row in r['cases'])
    assert digest(b.run())==digest(r) and len(received)==12
    b.validate()
