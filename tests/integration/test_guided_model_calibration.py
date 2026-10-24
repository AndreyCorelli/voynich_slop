import json

from benchmarks import guided_model_calibration as b
from benchmarks.l3_conflict import verify
from voynich_smt.models.text import Text


def test_prepared_coverage_matching_and_contraction_roundtrips():
    p=b.prepare()
    assert len(p['cases'])==8
    for language in p['config']['languages']:
        cases=[c for c in p['cases'] if c['language']==language]
        assert len({tuple(c['training_record_indices']) for c in cases})==1
        for case in cases:
            assert max(case['training_record_indices'])<min(case['holdout_record_indices'])
            assert min(case['training_record_indices'])>=p['splits'][language]
            if case['kind']=='synthetic':
                q,rules=b.request_for(case,case['generation_profile'],p);verify(q,case['truth'])
                seen={tuple(m['code']) for m in b.used_mappings(case['truth'])}
                assert all(tuple(w[i:i+2]) in seen for w in case['holdout']['words'] for i in range(0,len(w),2))
                assert all(w in p['vocabularies'][language] for w in b.expanded(case['truth']['plaintext']['words'],rules))
                if case['generation_profile']=='mixed':
                    assert any(len(s)>1 for w in case['truth']['plaintext']['words'] for s in w)


def test_training_only_proposals_obey_all_public_relations():
    p=b.prepare();case=p['cases'][0];q,rules=b.request_for(case,'letters',p)
    proposed=b.proposals(q,p['models'][case['language']],rules,16,3)
    graph=q.dictionary.candidate_graph(q.ciphertext,q.bounds,1,max(map(len,q.dictionary.words)))
    assert len(proposed)<=3
    for plain in proposed:
        assert all(w in graph.candidates[i] for i,w in enumerate(plain.words))
        assert all(rel.accepts(plain.words[rel.left],plain.words[rel.right]) for rel in graph.relations)
    # Changes to continuation/truth cannot change the training-only proposal API inputs.
    case['holdout']={'words':[]};case.pop('truth')
    q2,rules2=b.request_for(case,'letters',p)
    assert b.proposals(q2,p['models'][case['language']],rules2,16,3)==proposed


def test_model_scores_expansion_spellings_equally():
    p=b.prepare();model=p['models']['latin'];rules=p['config']['rules']['latin']
    assert b.training_score([tuple('et'),tuple('in')],model,rules)==b.training_score([('<et>',),tuple('in')],model,rules)
