"""Independent plaintext-reference overlap and frozen-prediction replay."""
from benchmarks.grammar_case_applicability_iteration180_review import close,independent_evaluate
from benchmarks.grammar_case_pair_selection_iteration178_review import independent_metrics
from benchmarks.grammar_case_overlap_iteration182 import *

def run():
    hashes=groups=0
    for name in ['design-freeze','strata-freeze']:
        for p,h in load(OUT/(name+'.json'))['inputs'].items():assert digest(p)==h;hashes+=1
    mapping=load(OUT/'identity-mapping.json');vocab=load(OUT/'vocabularies.json');rows=load(OUT/'overlap.json');strata=load(OUT/'strata.json');summary=load(OUT/'summary.json');selections=load(OUT/'selections.json');ff=load(ROOT/'iteration180/features.json');cached=load(ROOT/'iteration44/annotations-truth.json');words={};reference={}
    for pool,it,key,salt in [('earlier','iteration159','Cicero','frames164-Cicero|'),('replication','iteration168','fit-Cicero','replication168-fit-Cicero|')]:
        sids=load(ROOT/it/'selection.json')[key]['sent_ids'];tokens=[t['word'] for sid in sids for t in cached[sid]['tokens']];words[pool]=set(tokens);reference[pool]={hashlib.sha256((salt+w).encode()).hexdigest():w for w in tokens}
        assert load(ROOT/('iteration164' if pool=='earlier' else 'iteration168')/'streams.json')[key]==[hashlib.sha256((salt+w).encode()).hexdigest() for w in tokens]
        assert mapping[pool]=={opaque:hashlib.sha256(('overlap182|'+w).encode()).hexdigest() for opaque,w in reference[pool].items()};assert vocab[pool]==sorted(set(mapping[pool].values()))
    sourcepairs={frozenset([reference['earlier'][r['a']],reference['earlier'][r['b']]]) for r in ff['earlier']};endpoints=set().union(*sourcepairs);expected=[]
    for i,r in enumerate(ff['replication']):
        a,b=[reference['replication'][r[k]] for k in ['a','b']];expected.append(dict(index=i,pair=sorted(hashlib.sha256(('overlap182|'+w).encode()).hexdigest() for w in [a,b]),seen_pair=frozenset([a,b]) in sourcepairs,seen_training_endpoints=int(a in endpoints)+int(b in endpoints),seen_source_vocabulary=int(a in words['earlier'])+int(b in words['earlier'])))
    assert expected==rows
    expected_masks={'all':list(range(len(rows))),'seen_pair':[i for i,r in enumerate(expected) if r['seen_pair']],'unseen_pair':[i for i,r in enumerate(expected) if not r['seen_pair']],'new_pair_both_training_endpoints':[i for i,r in enumerate(expected) if not r['seen_pair'] and r['seen_training_endpoints']==2],'one_unseen_training_endpoint':[i for i,r in enumerate(expected) if r['seen_training_endpoints']==1],'both_unseen_training_endpoints':[i for i,r in enumerate(expected) if r['seen_training_endpoints']==0]}
    for n in [0,1,2]:expected_masks['source_vocabulary_seen_'+str(n)]=[i for i,r in enumerate(expected) if r['seen_source_vocabulary']==n]
    assert expected_masks==strata
    for names,expected_indices in [(['seen_pair','new_pair_both_training_endpoints','one_unseen_training_endpoint','both_unseen_training_endpoints'],strata['all']),(['new_pair_both_training_endpoints','one_unseen_training_endpoint','both_unseen_training_endpoints'],strata['unseen_pair']),(['source_vocabulary_seen_0','source_vocabulary_seen_1','source_vocabulary_seen_2'],strata['all'])]:
        flat=[i for n in names for i in strata[n]];assert len(flat)==len(set(flat)) and sorted(flat)==expected_indices
    predictions=load(ROOT/'iteration180/predictions.json')['replication'];oldlists=load(ROOT/'iteration180/selections.json')['replication'];baseline=load(ROOT/'iteration180/summary.json')['replication'];truth=load(ROOT/'iteration172/details.json')['replication']['original']['all']
    for name,ix in strata.items():
        for arm,pp in predictions.items():
            yy=[int(truth[i]['case_occurrence_pairs']>0) for i in ix];assert summary[name][arm]['n']==len(ix);close(summary[name][arm]['classification'],independent_evaluate(yy,[pp[i] for i in ix]) if ix else None)
            lists={}
            for label,old in oldlists[arm].items():lists['global_'+label]=[i for i in old if i in ix]
            for k in [10,20]:
                order=sorted(ix,key=lambda i:pp[i],reverse=True);cut=pp[order[min(k,len(order))-1]] if order else None;lists['within_top'+str(k)]=[i for i in ix if cut is not None and pp[i]>=cut]
            assert lists==selections[name][arm]
            for label,selected in lists.items():close(summary[name][arm]['lists'][label],independent_metrics([truth[i] for i in selected],857));groups+=1
            if name=='all':
                assert summary[name][arm]['classification']==baseline[arm]['classification']
                for label in oldlists[arm]:assert summary[name][arm]['lists']['global_'+label]==baseline[arm]['lists'][label]
    save(OUT/'audit.json',dict(input_strata_hashes_verified=hashes,word_streams_and_cross_salt_identity_maps_verified=2,target_overlap_rows_verified=len(rows),all_training_pair_endpoint_and_full_vocabulary_partitions=True,selection_metric_groups_verified=groups,all_classification_and_calibration_metrics_verified=True,all180_global_baselines_exact=True,no_refitting_or_identity_inference_features=True))
    print('audit passed',len(rows),groups,flush=True)
if __name__=='__main__':run()
