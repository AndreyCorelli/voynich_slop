"""Frozen-model lexical-overlap audit; word references only define strata."""
from benchmarks.grammar_case_applicability_iteration180 import *
OUT=ROOT/'iteration182'

def identities():
    cached=load(ROOT/'iteration44/annotations-truth.json');result={};vocab={}
    for pool,it,key,salt in [('earlier','iteration159','Cicero','frames164-Cicero|'),('replication','iteration168','fit-Cicero','replication168-fit-Cicero|')]:
        sids=load(ROOT/it/'selection.json')[key]['sent_ids'];words=[t['word'] for sid in sids for t in cached[sid]['tokens']];stream=load(ROOT/('iteration164' if pool=='earlier' else 'iteration168')/'streams.json')[key];assert stream==[hashlib.sha256((salt+w).encode()).hexdigest() for w in words]
        result[pool]={hashlib.sha256((salt+w).encode()).hexdigest():hashlib.sha256(('overlap182|'+w).encode()).hexdigest() for w in words};vocab[pool]=sorted(set(result[pool].values()))
    return result,vocab

def overlap_rows(features,mapping,vocab):
    sourcepairs={tuple(sorted([mapping['earlier'][r['a']],mapping['earlier'][r['b']]])) for r in features['earlier']};endpoints={w for p in sourcepairs for w in p};sourcevocab=set(vocab['earlier']);rows=[]
    for i,r in enumerate(features['replication']):
        pair=sorted([mapping['replication'][r['a']],mapping['replication'][r['b']]]);rows.append(dict(index=i,pair=pair,seen_pair=tuple(pair) in sourcepairs,seen_training_endpoints=sum(w in endpoints for w in pair),seen_source_vocabulary=sum(w in sourcevocab for w in pair)))
    strata={'all':list(range(len(rows))),'seen_pair':[r['index'] for r in rows if r['seen_pair']],'unseen_pair':[r['index'] for r in rows if not r['seen_pair']],'new_pair_both_training_endpoints':[r['index'] for r in rows if not r['seen_pair'] and r['seen_training_endpoints']==2],'one_unseen_training_endpoint':[r['index'] for r in rows if r['seen_training_endpoints']==1],'both_unseen_training_endpoints':[r['index'] for r in rows if r['seen_training_endpoints']==0]}
    for count in [0,1,2]:strata['source_vocabulary_seen_'+str(count)]=[r['index'] for r in rows if r['seen_source_vocabulary']==count]
    return rows,strata

def run():
    assert not OUT.exists();OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),ROOT/'iteration181/verification-manifest.json',ROOT/'iteration180/features.json',ROOT/'iteration180/predictions.json',ROOT/'iteration180/summary.json',ROOT/'iteration180/selections.json',ROOT/'iteration159/selection.json',ROOT/'iteration168/selection.json',ROOT/'iteration44/annotations-truth.json',ROOT/'iteration164/streams.json',ROOT/'iteration168/streams.json',ROOT/'iteration172/details.json']
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='Frozen180 models/predictions only, NO refitting. Audit cached exact word identity via crosspool common salt, no additional normalization; reconstruct/verify streams from cached WORD fields only. Identity used solely to partition evaluation, never model inputs. Freeze source52 pair identity set/endpoints and target126 overlap rows/strata before labels/metrics. PRIMARY unseen exact unordered training pair; disjoint strata seen pair,new pair both training endpoints,one unseen training endpoint,both unseen training endpoints. Also report source WHOLE passage vocabulary endpoint counts0/1/2 (distinct from supervised graph endpoints). Keep every sparse/empty/oneclass stratum. All three180 model arms; evaluate frozen classification within strata; global original threshold/top10/top20 INTERSECTIONS primary shortlist diagnostic, separately fixed within-stratum top10/top20 tie-inclusive reranking descriptive. No claiming a reranked list was original top10. Exact all-stratum180 classification/global shortlist baselines; all masks disjoint partitions checked. Sameauthor/development/known-target followup not fresh generalization, no namedcase/POS/nuclei restoration or reserve/sealed/newannotations.'))
    mapping,vocab=identities();features=load(ROOT/'iteration180/features.json');rows,strata=overlap_rows(features,mapping,vocab)
    save(OUT/'identity-mapping.json',mapping);save(OUT/'vocabularies.json',vocab);save(OUT/'overlap.json',rows);save(OUT/'strata.json',strata);save(OUT/'strata-freeze.json',dict(inputs={str(OUT/n):digest(OUT/n) for n in ['identity-mapping.json','vocabularies.json','overlap.json','strata.json']}))
    predictions=load(ROOT/'iteration180/predictions.json')['replication'];global_lists=load(ROOT/'iteration180/selections.json')['replication'];truth=load(ROOT/'iteration172/details.json')['replication']['original']['all'];summary={};selections={}
    for stratum,ix in strata.items():
        summary[stratum]={};selections[stratum]={};allowed=set(ix)
        for arm,pp in predictions.items():
            lists={'global_'+label:[i for i in indices if i in allowed] for label,indices in global_lists[arm].items()}
            for k in [10,20]:
                cutoff=sorted([pp[i] for i in ix],reverse=True)[min(k,len(ix))-1] if ix else None;lists['within_top'+str(k)]=[i for i in ix if cutoff is not None and pp[i]>=cutoff]
            yy=[int(truth[i]['case_occurrence_pairs']>0) for i in ix];summary[stratum][arm]=dict(n=len(ix),classification=evaluate(yy,[pp[i] for i in ix]) if ix else None,lists={name:metrics([truth[i] for i in selected],857) for name,selected in lists.items()});selections[stratum][arm]=lists
        print(stratum,json.dumps(summary[stratum]['rich']),flush=True)
    save(OUT/'selections.json',selections);save(OUT/'summary.json',summary)
if __name__=='__main__':run()
