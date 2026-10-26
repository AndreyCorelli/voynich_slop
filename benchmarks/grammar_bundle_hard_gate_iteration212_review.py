"""Independent hard-gate memberships, tie groups, metrics and comparators."""
from pathlib import Path
import json,hashlib,math
from itertools import groupby
P=Path('experiments/results/grammar-restoration');O=P/'iteration212'
def read(p):return json.loads(p.read_text())
def near(a,b):
    if a is None:assert b is None
    else:assert math.isclose(a,b,abs_tol=1e-12,rel_tol=1e-12)
def run():
    pred=read(P/'iteration211/predictions.json');yy=read(P/'iteration207/teacher-labels.json');app=read(P/'iteration211/applicability-labels.json');ff=read(P/'iteration211/features.json');sel=read(O/'selections.json');ss=read(O/'summary.json');rr=read(O/'supported-ranks.json');orig=read(P/'iteration207/summary.json');soft=read(P/'iteration211/summary.json');oracle=read(P/'iteration210/summary.json');lists=0;records=0
    for a,models in pred.items():
        positive=[i for i,v in enumerate(yy[a]) if v]
        for name,scores in models.items():
            keep=[i for i,p in enumerate(scores['applicability']) if not p<.5];assert keep==sel[a][name]['eligible'];s=ss[a][name];ret=[i for i in positive if i in keep];rej=[i for i in positive if i not in keep];assert s['retained_supported']==ret and s['rejected_supported']==rej;assert s['eligible']==len(keep) and s['eligible_case_bearing']==sum(app[a][i] for i in keep) and s['candidates']==len(yy[a]) and s['supported']==len(positive)
            ordering=sorted(keep,key=lambda i:-scores['support'][i]);cumulative=[];rankmap={};expected={}
            for value,group in groupby(ordering,key=lambda i:scores['support'][i]):
                batch=list(group);first=len(cumulative)+1;cumulative+=batch
                for i in batch:rankmap[i]=(first,len(cumulative))
                for k in [3,5]:
                    if k not in expected and len(cumulative)>=min(k,len(keep)):expected[k]=sorted(cumulative)
            assert [r['index'] for r in rr[a][name]]==positive
            for r in rr[a][name]:
                i=r['index'];assert r['word']==ff[a][i]['word'] and r['retained']==(i in keep);assert (r['rank_first'],r['rank_last'])==rankmap.get(i,(None,None));records+=1
            for k in [3,5]:
                label=f'top{k}';ix=expected.get(k,[]);assert ix==sel[a][name]['lists'][label];v=s['lists'][label];hit=sum(yy[a][i] for i in ix);assert v['selected']==len(ix) and v['supported']==hit and v['case_bearing']==sum(app[a][i] for i in ix)
                for key,x in [('precision',hit/len(ix) if ix else None),('recall',hit/len(positive) if positive else None),('coverage',len(ix)/len(yy[a])),('eligible_coverage',len(ix)/len(keep) if keep else None),('retained_support_recall',hit/len(ret) if ret else None)]:near(x,v[key])
                assert s['comparators'][label]==dict(original=orig[a]['models'][name]['lists'][label],product=soft[a]['models'][name]['lists']['product'][label]['support'],oracle=oracle[a]['models'][name]['gated'][label]);lists+=1
    hashes=0
    for manifest in [read(O/'design-freeze.json')]+[read(P/it/'verification-manifest.json') for it in ['iteration207','iteration210','iteration211']]:
        for p,h in manifest.items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h;hashes+=1
    for p,h in read(O/'selection-freeze.json').items():assert hashlib.sha256((O/p).read_bytes()).hexdigest()==h;hashes+=1
    result=dict(status='passed',lists=lists,supported_records=records,hashes=hashes);(O/'independent-review.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
if __name__=='__main__':run()
