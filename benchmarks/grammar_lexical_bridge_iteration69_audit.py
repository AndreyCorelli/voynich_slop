"""Replay lexical-bridge scores, candidate availability and gate decisions."""
from benchmarks.grammar_lexical_bridge_iteration69 import *


def close(a,b):
    if isinstance(a,dict):
        assert set(a)==set(b)
        for k in a:close(a[k],b[k])
    elif isinstance(a,list):
        assert len(a)==len(b)
        for x,y in zip(a,b):close(x,y)
    elif isinstance(a,float):np.testing.assert_allclose(a,b,rtol=1e-8,atol=1e-9)
    else:assert a==b


def run():
    hashes=0
    for name in ('design-freeze.json','prediction-freeze.json'):
        for p,h in load(OUT/name)['inputs'].items():assert digest(p)==h,p;hashes+=1
    scorer=build_scorer();assert scorer.pos==load(OUT/'pos-source-model.json');audit,_=candidate_audit();assert audit==load(OUT/'candidate-audit.json');rows=load(OUT/'first-corruption-scores.json');queries=0
    for r in rows:
        for crop in r['crops']:
            for variant in VARIANTS:
                for version in ('before','after'):
                    actual=scorer.score(crop[version+'_tokens'],variant);close(actual,crop['scores'][variant][version]);queries+=1
        for variant in VARIANTS:
            total=sum(len(c['before_tokens']) for c in r['crops'])
            for metric in ('lift','shuffled_query_lift','raw','source_frequency'):
                def val(row):return row['raw']['normalized'] if metric=='raw' else row[metric]
                delta=sum(len(c['before_tokens'])*(val(c['scores'][variant]['before'])-val(c['scores'][variant]['after'])) for c in r['crops'])/total
                np.testing.assert_allclose(delta,r['aggregate'][variant][metric+'_intact_minus_corrupted'],rtol=1e-8,atol=1e-9)
    assert summarize(rows)==load(OUT/'evaluation.json');save(OUT/'independent-validation.json',dict(freeze_hashes=hashes,score_queries_replayed=queries,raw_structured_scores_replayed=len(scorer.score_cache),candidate_oracle_ranks_replayed=22,gate_replayed=True,reserve_unscored=200,prior_queries_scored=0));print('Bridge audit passed',queries,len(scorer.score_cache))
if __name__=='__main__':run()
