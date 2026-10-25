"""Replay boundary transformations, integer-combination nulls and controls."""
from benchmarks.grammar_overlap_boundaries_iteration137 import *
from benchmarks.grammar_context_overlap_iteration135_review import independent_stats,equal_stats

def run():
    hashes=0
    for name in ['design-freeze','transform-freeze','predictions-freeze']:
        for p,h in load(OUT/(name+'.json'))['inputs'].items():assert digest(p)==h,p;hashes+=1
    contexts={'source':load(ROOT/'iteration118/public.json')};contexts.update({a+'-'+v:load(p) for a,vv in INPUTS.items() for v,p in vv.items()});old=load(ROOT/'iteration135/predictions.json');models=load(ROOT/'iteration135/models.json');cal=load(ROOT/'iteration135/calibrators.json');transforms=load(OUT/'transforms.json');saved=load(OUT/'statistics.json');pred=load(OUT/'predictions.json');summary=load(OUT/'summary.json');contrast=load(OUT/'contrasts.json');anchors=load(ROOT/'iteration85/anchor-budgets.json')['195'];reserved={r['sent_id'] for rr in load('experiments/holdouts/grammar-construction-next.json')['authors'].values() for r in rr};statchecks=probchecks=metricchecks=0
    for key,context in contexts.items():
        assert not {s['sent_id'] for s in context}&reserved;ids=[s['sent_id'] for s in context];byid={s['sent_id']:s for s in context};flat=[t['id'] for s in context for t in s['tokens']];lookup={r['type']:r['opaque'] for r in old[key]['corrected']};assert len(transforms[key])==20
        for name,t in transforms[key].items():
            if name=='concat':assert t==dict(kind='sentence_order',sentence_ids=ids)
            elif name.startswith('sentence'):
                seed=int(name[8:]);assert seed in ORDER_SEEDS;assert t==dict(kind='sentence_order',sentence_ids=sorted(ids,key=lambda sid:hashlib.sha256((str(seed)+'|'+sid).encode()).hexdigest()))
            else:
                seed=int(name[4:]);assert seed in NULL_SEEDS;assert t==dict(kind='word_order',indices=np.random.default_rng(seed).permutation(len(flat)).tolist());assert sorted(t['indices'])==list(range(len(flat)))
            seq=[w['id'] for sid in t['sentence_ids'] for w in byid[sid]['tokens']] if t['kind']=='sentence_order' else [flat[i] for i in t['indices']];assert Counter(seq)==Counter(flat);public=[dict(tokens=[dict(id=i) for i in seq])];stats=independent_stats(public,set(lookup.values()));equal_stats(stats,saved[key][name]);statchecks+=len(stats)
            for arm,rows in pred[key][name].items():
                assert {r['type'] for r in rows}==set(lookup)
                for r in rows:
                    identity=r['opaque'];assert r['n']==stats[identity]['n'];assert abs(r['statistic']-stats[identity][arm])<1e-11;raw=predict_scalar(stats[identity][arm],models[arm]['final']);assert abs(raw-r['probabilities']['raw'])<1e-10;assert abs(float(apply_offset([raw],cal[arm])[0])-r['probabilities']['new'])<1e-10;probchecks+=1
                for p,m in summary[key][name][arm].items():
                    q=np.array([r['probabilities'][p] for r in rows]);y=np.array([anchors[r['type']]=='CCONJ' for r in rows]);a=q>.5;assert m['correct']==int((a==y).sum());assert abs(m['nll']-float(-np.log(np.where(y,q,1-q)).mean()))<1e-12;assert m['auc']==float(np.mean((q[y,None]>q[~y][None,:])+.5*(q[y,None]==q[~y][None,:])));metricchecks+=1
        for arm,c in contrast[key].items():
            rr=[dict(r,**{'class':anchors[r['type']]}) for r in old[key][arm]];assert c['sentence_preserved']==metrics(rr,'new');actual=summary[key]['concat'][arm]['new'];assert c['concat']==actual;null=[summary[key]['word'+str(seed)][arm]['new'] for seed in NULL_SEEDS];assert c['sentence_orders']==[summary[key]['sentence'+str(seed)][arm]['new'] for seed in ORDER_SEEDS]
            for m in ['accuracy','nll','auc']:
                assert abs(c['null_mean'][m]-np.mean([r[m] for r in null]))<1e-12;assert c['null_min'][m]==min(r[m] for r in null);assert c['null_max'][m]==max(r[m] for r in null)
            assert c['null_auc_at_least_concat']==sum(r['auc']>=actual['auc'] for r in null);assert c['null_accuracy_at_least_concat']==sum(r['accuracy']>=actual['accuracy'] for r in null)
        print('audited',key,flush=True)
    save(OUT/'audit.json',dict(input_hashes_verified=hashes,transformed_views_reconstructed=100,independent_combinatorial_type_statistics=statchecks,probabilities_replayed=probchecks,metric_groups=metricchecks,all_word_counts_and_type_sets_preserved=True,null_summaries_replayed=True,no_sentence_boundaries_anchors_or_fit_in_new_predictions=True,reserve_absent=True));print(load(OUT/'audit.json'))
if __name__=='__main__':run()
