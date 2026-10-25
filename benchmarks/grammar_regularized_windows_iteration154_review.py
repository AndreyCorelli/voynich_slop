"""Independent fixed-window model/probability/metric replay."""
from benchmarks.grammar_regularized_windows_iteration154 import *
from scipy.special import expit

def run():
    hc=pc=mc=0
    for name in ['design-freeze','predictions-freeze']:
        for p,h in load(OUT/(name+'.json'))['inputs'].items():assert digest(p)==h,p;hc+=1
    selection=load(ROOT/'iteration144/selection.json');assert len(selection)==70;features=load(ROOT/'iteration144/features.json');old=load(ROOT/'iteration144/predictions.json');pred=load(OUT/'predictions.json');summary=load(OUT/'summary.json');anchors=load(ROOT/'iteration85/anchor-budgets.json')['195'];core=set(load(ROOT/'iteration139/common-core.json'));catalogue=set(load(ROOT/'iteration93/types.json')['candidates']);models={'selected':load(ROOT/'iteration153/models.json')['full'],'fixed':load(ROOT/'iteration152/models.json')['full']}
    for key,arms in pred.items():
        assert arms['original']==old[key]['joint'];w=selection[key]['work'];assert set(arms)=={'original','fixed','selected'}
        for name,rows in arms.items():
            if name in models:
                m=models[name];ww=np.array(m['weights']);b=ww[:,1]-ww[:,0]
                for r in rows:
                    f=features[key][r['opaque']];x=(np.array([f[c] for c in COLS])-m['mean'])/m['scale'];p=float(expit(b[0]+x@b[1:]));assert abs(p-r['probabilities']['raw'])<1e-10;pc+=1
            present={r['type'] for r in rows};s=summary[key][name];assert s['missing_types']==sorted(catalogue-present) and s['missing_common14']==sorted(core-present);assert s['tokens']==selection[key]['stop']-selection[key]['start']
            groups={'all':rows,'supported':[r for r in rows if r['supported']],'common14':[r for r in rows if r['type'] in core],'full_same_present':[r for r in pred[w+'/full'][name] if r['type'] in present]}
            for group,rr in groups.items():
                mm=s['full_same_present'] if group=='full_same_present' else s['metrics'][group];q=np.array([r['probabilities']['raw'] for r in rr]);y=np.array([anchors[r['type']]=='CCONJ' for r in rr]);assert mm==metrics([dict(r,**{'class':anchors[r['type']]}) for r in rr],'raw');assert mm['n']==len(rr) and mm['correct']==int(((q>.5)==y).sum());assert abs(mm['nll']-float(-np.log(np.where(y,q,1-q)).mean()))<1e-12;assert mm['auc']==float(np.mean((q[y,None]>q[~y][None,:])+.5*(q[y,None]==q[~y][None,:])));mc+=1
        if key.endswith('/full'):
            assert arms['selected']==load(ROOT/'iteration153/predictions.json')[w]['full']['selected'];assert arms['fixed']==load(ROOT/'iteration152/predictions.json')[w]['full']['constrained']
    save(OUT/'audit.json',dict(input_hashes_verified=hc,views_verified=70,new_probability_replays=pc,metric_groups_independently_checked=mc,full_reference_pairs_verified=14,no_fitting_or_selection=True,missing_and_same_present_comparators_checked=True))
if __name__=='__main__':run()
