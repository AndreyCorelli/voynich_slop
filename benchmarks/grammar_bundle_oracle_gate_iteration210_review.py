"""Independent oracle filter, sorted tie groups and scalar metric replay."""
from pathlib import Path
from itertools import groupby
import json,hashlib,math
P=Path('experiments/results/grammar-restoration');O=P/'iteration210'
def read(p):return json.loads(p.read_text())
def close(a,b):
    if a is None:assert b is None
    else:assert math.isclose(a,b,abs_tol=1e-12,rel_tol=1e-12)
def run():
    dd=read(O/'details.json');ss=read(O/'summary.json');pred=read(P/'iteration207/predictions.json');yy=read(P/'iteration207/teacher-labels.json');rr=read(P/'iteration209/details.json');old=read(P/'iteration207/selections.json');os=read(P/'iteration207/summary.json');lists=0;ranks=0
    for a,d in dd.items():
        keep=[i for i,r in enumerate(rr[a]) if r['center_global_case_fraction']!=0];assert keep==d['eligible'];removed=[i for i in range(len(rr[a])) if i not in keep];assert removed==[r['index'] for r in d['rejected']];assert all(r['word']==rr[a][r['index']]['word'] for r in d['rejected']);positives=[i for i,v in enumerate(yy[a]) if v];assert all(i in keep for i in positives)
        assert ss[a]['eligible']==len(keep) and ss[a]['rejected']==len(removed) and ss[a]['original_candidates']==len(rr[a]);assert ss[a]['original_supported']==ss[a]['retained_supported']==len(positives)
        for name,scores in pred[a].items():
            for mode,universe in [('original',list(range(len(scores)))),('gated',keep)]:
                ordered=sorted(universe,key=lambda i:-scores[i]);rankmap={};cumulative=[];expected={}
                for score,tied in groupby(ordered,key=lambda i:scores[i]):
                    batch=list(tied);start=len(cumulative)+1;cumulative.extend(batch)
                    for i in batch:rankmap[i]=(start,len(cumulative))
                    for k in [3,5]:
                        if 'top'+str(k) not in expected and len(cumulative)>=min(k,len(ordered)):expected['top'+str(k)]=sorted(cumulative)
                for k in [3,5]:
                    label='top'+str(k);ix=expected.get(label,[]);assert ix==d['models'][name]['lists'][mode][label];v=ss[a]['models'][name][mode][label];hit=sum(yy[a][i] for i in ix);assert v['supported']==hit and v['selected']==len(ix)
                    close(v['precision'],hit/len(ix) if ix else None);close(v['recall'],hit/len(positives) if positives else None);close(v['original_coverage'],len(ix)/len(scores));close(v['eligible_coverage'],len(ix)/len(universe) if universe else None)
                    if mode=='original':
                        assert ix==old[a][name][label];ov=os[a]['models'][name]['lists'][label];assert hit==ov['supported'] and len(ix)==ov['selected'];close(v['precision'],ov['precision']);close(v['recall'],ov['recall'])
                    lists+=1
                records=d['models'][name][mode+'_ranks'];assert [r['index'] for r in records]==positives
                for r in records:assert (r['first'],r['last'])==rankmap[r['index']];ranks+=1
    hashes=0
    for manifest in [read(O/'design-freeze.json')]+[read(P/it/'verification-manifest.json') for it in ['iteration207','iteration209']]:
        for p,h in manifest.items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h;hashes+=1
    result=dict(status='passed',lists=lists,supported_rank_records=ranks,hashes=hashes);(O/'independent-review.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
if __name__=='__main__':run()
