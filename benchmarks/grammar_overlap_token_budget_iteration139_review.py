"""Replay token windows, independent statistics and common-type accounting."""
from benchmarks.grammar_overlap_token_budget_iteration139 import *
from benchmarks.grammar_context_overlap_iteration135_review import independent_stats,equal_stats

def run():
    hashes=0
    for name in ['design-freeze','selection-freeze','predictions-freeze']:
        for p,h in load(OUT/(name+'.json'))['inputs'].items():assert digest(p)==h,p;hashes+=1
    streams,lookups=streams_and_lookups();selection=load(OUT/'selection.json');core=load(OUT/'common-core.json');present={w:{t for t,i in lookups[w].items() if i in set(seq)} for w,seq in streams.items()};assert core==sorted(set.intersection(*present.values()));expected={}
    for work,seq in streams.items():
        expected[work+'/full']=dict(work=work,start=0,stop=len(seq),full=True)
        for seed in SEEDS:
            start=int(hashlib.sha256((str(seed)+'|'+work).encode()).hexdigest(),16)%(len(seq)-7000+1)
            for n in SIZES:
                lo=start+(7000-n)//2;expected[work+'/'+str(seed)+'/'+str(n)]=dict(work=work,start=lo,stop=lo+n,full=False)
    assert selection==expected and len(selection)==40;models=load(ROOT/'iteration135/models.json');cal=load(ROOT/'iteration135/calibrators.json');pred=load(OUT/'predictions.json');saved=load(OUT/'statistics.json');summary=load(OUT/'summary.json');paired=load(OUT/'full-same-present.json');anchors=load(ROOT/'iteration85/anchor-budgets.json')['195'];catalogue=load(ROOT/'iteration93/types.json')['candidates'];coverage={};statchecks=probchecks=metricchecks=0
    for key,r in selection.items():
        work=r['work'];seq=streams[work][r['start']:r['stop']];lookup=lookups[work];stats=independent_stats([dict(tokens=[dict(id=i) for i in seq])],set(lookup.values()));equal_stats(stats,saved[key]);statchecks+=len(stats);coverage[key]=dict(missing_from_full_catalogue=sorted(set(catalogue)-{x['type'] for x in pred[key]['corrected']}))
        for arm,rows in pred[key].items():
            current={x['type'] for x in rows};assert summary[key][arm]['missing_types']==sorted(set(lookup)-current);assert summary[key][arm]['missing_common_core']==sorted(set(core)-current)
            for x in rows:
                identity=x['opaque'];assert x['n']==stats[identity]['n'];assert x['supported']==(x['n']>=5);assert abs(x['statistic']-stats[identity][arm])<1e-11;raw=predict_scalar(stats[identity][arm],models[arm]['final']);assert abs(raw-x['probabilities']['raw'])<1e-10;assert abs(float(apply_offset([raw],cal[arm])[0])-x['probabilities']['new'])<1e-10;probchecks+=1
            for group,ms in summary[key][arm]['metrics'].items():
                rr=[x for x in rows if group=='all' or group=='supported' and x['supported'] or group=='common_core_present' and x['type'] in core]
                for name,m in ms.items():
                    assert m['n']==len(rr)
                    if not rr:continue
                    p=np.array([x['probabilities'][name] for x in rr]);y=np.array([anchors[x['type']]=='CCONJ' for x in rr]);assert m['correct']==int(((p>.5)==y).sum());assert abs(m['nll']-float(-np.log(np.where(y,p,1-p)).mean()))<1e-12
                    if y.any() and (~y).any():assert m['auc']==float(np.mean((p[y,None]>p[~y][None,:])+.5*(p[y,None]==p[~y][None,:])))
                    metricchecks+=1
            full={x['type']:x for x in pred[work+'/full'][arm]};assert paired[key][arm]['n']==len(rows);assert paired[key][arm]['correct']==sum((full[w]['probabilities']['new']>.5)==(anchors[w]=='CCONJ') for w in current)
    old=load(ROOT/'iteration138/four-text-summary.json')
    for work in streams:assert summary[work+'/full']['corrected']['metrics']['all']['new']==old[work]
    save(OUT/'catalogue-coverage.json',coverage);save(OUT/'audit.json',dict(input_hashes_verified=hashes,window_selections_reconstructed=40,independent_combinatorial_type_statistics=statchecks,probabilities_replayed=probchecks,metric_groups=metricchecks,common14_and_missing_type_accounting_verified=True,full138results_reproduced=True,no_fit_or_target_threshold_change=True));print(load(OUT/'audit.json'))
if __name__=='__main__':run()
