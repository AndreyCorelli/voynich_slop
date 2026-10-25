"""Independent volume selections, combinatorial statistics and paired metrics."""
from benchmarks.grammar_overlap_volume_iteration136 import *
from benchmarks.grammar_context_overlap_iteration135_review import independent_stats,equal_stats

def run():
    hashes=0
    for name in ['design-freeze','selection-freeze','predictions-freeze']:
        for p,h in load(OUT/(name+'.json'))['inputs'].items():assert digest(p)==h,p;hashes+=1
    contexts={a:load(p['expanded']) for a,p in INPUTS.items()};selection=load(OUT/'selection.json');lookups=load(OUT/'lookups.json');old=load(ROOT/'iteration135/predictions.json');models=load(ROOT/'iteration135/models.json');cal=load(ROOT/'iteration135/calibrators.json');saved=load(OUT/'statistics.json');pred=load(OUT/'predictions.json');summary=load(OUT/'summary.json');paired=load(OUT/'paired-comparisons.json');anchors=load(ROOT/'iteration85/anchor-budgets.json')['195'];reserved={r['sent_id'] for rr in load('experiments/holdouts/grammar-construction-next.json')['authors'].values() for r in rr};expected={}
    for author,context in contexts.items():
        ids=[s['sent_id'] for s in context];assert not set(ids)&reserved;expected[author+'/full']=ids;expected[author+'/original100']=[s['sent_id'] for s in load(INPUTS[author]['base'])];assert lookups[author]=={r['type']:r['opaque'] for r in old[author+'-expanded']['corrected']}
        for seed in SEEDS:
            order=sorted(ids,key=lambda sid:hashlib.sha256((str(seed)+'|'+sid).encode()).hexdigest())
            for n in SIZES[author][:-1]:expected[author+'/'+str(seed)+'/'+str(n)]=order[:n]
    assert selection==expected and len(selection)==31;statchecks=probchecks=metricchecks=0
    for key,ids in selection.items():
        author=key.split('/')[0];byid={s['sent_id']:s for s in contexts[author]};public=[byid[i] for i in ids];lookup=lookups[author];st=independent_stats(public,set(lookup.values()));equal_stats(st,saved[key]);statchecks+=len(st)
        for arm,rows in pred[key].items():
            assert {r['opaque'] for r in rows}==set(st);present={r['type'] for r in rows};assert summary[key][arm]['missing_types']==sorted(set(lookup)-present)
            for r in rows:
                identity=r['opaque'];assert r['n']==st[identity]['n'];assert r['sentences']==sum(any(t['id']==identity for t in s['tokens']) for s in public);assert r['supported']==(r['n']>=5 and r['sentences']>=3);assert abs(r['statistic']-st[identity][arm])<1e-11;raw=predict_scalar(st[identity][arm],models[arm]['final']);assert abs(raw-r['probabilities']['raw'])<1e-10;assert abs(float(apply_offset([raw],cal[arm])[0])-r['probabilities']['new'])<1e-10;probchecks+=1
            for group,ms in summary[key][arm]['metrics'].items():
                rr=[r for r in rows if group=='all' or r['supported']]
                for name,m in ms.items():
                    assert m['n']==len(rr)
                    if not rr:continue
                    p=np.array([r['probabilities'][name] for r in rr]);y=np.array([anchors[r['type']]=='CCONJ' for r in rr]);assert m['correct']==int(((p>.5)==y).sum());assert abs(m['nll']-float(-np.log(np.where(y,p,1-p)).mean()))<1e-12
                    if y.any() and (~y).any():assert m['auc']==float(np.mean((p[y,None]>p[~y][None,:])+.5*(p[y,None]==p[~y][None,:])))
                    metricchecks+=1
            pair=paired[key][arm];full={r['type']:r for r in pred[author+'/full'][arm]};core={r['type'] for r in old[author+'-base'][arm]};correct=lambda r:(r['probabilities']['new']>.5)==(anchors[r['type']]=='CCONJ');assert pair['missing_original_core']==sorted(core-present);assert pair['original_core_present_metrics']['correct']==sum(correct(r) for r in rows if r['type'] in core);assert pair['full_same_present_metrics']['correct']==sum(correct(full[w]) for w in present);assert pair['correct_here_wrong_full']==[r['type'] for r in rows if correct(r) and not correct(full[r['type']])];assert pair['wrong_here_correct_full']==[r['type'] for r in rows if not correct(r) and correct(full[r['type']])]
            if key.endswith('/full') or key.endswith('/original100'):
                phase='expanded' if key.endswith('/full') else 'base';previous={r['type']:r for r in old[author+'-'+phase][arm]};assert present==set(previous)
                for r in rows:assert abs(r['probabilities']['new']-previous[r['type']]['probabilities']['new'])<1e-10
    save(OUT/'audit.json',dict(input_hashes_verified=hashes,views_reconstructed=31,independent_combinatorial_type_statistics=statchecks,probabilities_replayed=probchecks,metric_groups=metricchecks,paired_core_and_missing_comparisons_verified=True,original_and_full135_results_reproduced=True,no_fit_or_target_threshold_change=True,reserve_absent=True));print(load(OUT/'audit.json'))
if __name__=='__main__':run()
