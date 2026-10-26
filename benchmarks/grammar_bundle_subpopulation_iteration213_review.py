"""Independent position counters, group macro/pooled summaries and logit replay."""
from pathlib import Path
from collections import Counter
import json,math,statistics,hashlib
P=Path('experiments/results/grammar-restoration');O=P/'iteration213'
def read(p):return json.loads(p.read_text())
def close(a,b):
    if isinstance(a,dict):
        assert set(a)==set(b)
        for k in a:close(a[k],b[k])
    elif isinstance(a,list):
        assert len(a)==len(b)
        for x,y in zip(a,b):close(x,y)
    elif a is None:assert b is None
    elif isinstance(a,(int,float)):assert math.isclose(a,b,abs_tol=1e-10,rel_tol=1e-10),(a,b)
    else:assert a==b

def run():
    gg=read(P/'iteration193/graphs.json');refs=read(P/'iteration201/development-references.json');bb=read(P/'iteration205/candidates.json');dd=read(O/'details.json');groups=read(O/'groups.json');ss=read(O/'summary.json');cc=read(O/'contrasts.json');y=read(P/'iteration207/teacher-labels.json');app=read(P/'iteration211/applicability-labels.json');pred=read(P/'iteration211/predictions.json');sel=read(P/'iteration212/selections.json');ff=read(P/'iteration211/features.json');mm=read(P/'iteration211/models.json');checked=0;groupcount=0
    for a,rows in dd.items():
        g=gg[a];r=refs[a]
        for row,b in zip(rows,bb[a]):
            w=b['word'];globalpos=[i for i,p in enumerate(g['positions']) if p is not None and g['ids'][i]==w];queried=set()
            for ei in b['edges']:
                for frame in g['descriptors'][ei]['frames']:
                    queried.update(i for side in ['a_positions','b_positions'] for i in frame[side] if g['ids'][i]==w)
            assert row['word']==w and row['global_positions_count']==len(globalpos) and row['queried_positions']==sorted(queried);assert row['global']==dict(Counter(r['pos'][i] for i in globalpos));assert row['queried']==dict(Counter(r['pos'][i] for i in queried));checked+=1
        for name,group in groups[a].items():
            accepted=set(sel[a][name]['eligible']);expected=dict(all=list(range(len(rows))),case_bearing=[i for i in range(len(rows)) if app[a][i]],accepted_case_bearing=[i for i in range(len(rows)) if app[a][i] and i in accepted],rejected_case_bearing=[i for i in range(len(rows)) if app[a][i] and i not in accepted],supported_retained=[i for i in range(len(rows)) if y[a][i] and i in accepted],supported_rejected=[i for i in range(len(rows)) if y[a][i] and i not in accepted],admitted_unsupported_head=[i for i in sel[a][name]['lists']['top5'] if not y[a][i]]);assert expected==group
            for label,ix in group.items():
                value=ss[a][name][label];assert value['n']==len(ix);probs=[pred[a][name]['applicability'][i] for i in ix];close(value['probability_range'],[min(probs),max(probs)] if probs else None)
                for view in ['global','queried']:
                    total=Counter()
                    for i in ix:total.update(rows[i][view])
                    n=sum(total.values());macro={tag:statistics.mean(rows[i][view].get(tag,0)/sum(rows[i][view].values()) for i in ix) for tag in total}
                    close(value[view],dict(occurrences=n,counts=dict(total),pooled_fractions={tag:v/n for tag,v in total.items()} if n else {},center_macro_fractions=macro))
                groupcount+=1
            rejected=group['supported_rejected'];accepted=group['accepted_case_bearing'];m=mm[a][name]
            if rejected and accepted:
                delta=[];contrib=[]
                for j,col in enumerate(m['columns']):
                    d=(statistics.mean(ff[a][i]['values'][col] for i in rejected)-statistics.mean(ff[a][i]['values'][col] for i in accepted))/m['scale'][j];delta.append(d);contrib.append(d*m['beta'][j+1])
                close(cc[a][name],dict(rejected_supported_minus_accepted_case_bearing_standardized_feature=delta,logit_contributions=contrib,mean_logit_gap=sum(contrib)))
                def logit(i):return m['beta'][0]+sum((ff[a][i]['values'][col]-m['mean'][j])/m['scale'][j]*m['beta'][j+1] for j,col in enumerate(m['columns']))
                close(sum(contrib),statistics.mean(logit(i) for i in rejected)-statistics.mean(logit(i) for i in accepted))
            else:assert cc[a][name] is None
    hashes=0
    for manifest in [read(O/'design-freeze.json'),read(P/'iteration212/verification-manifest.json')]:
        for p,h in manifest.items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h;hashes+=1
    for p,h in read(O/'group-freeze.json').items():assert hashlib.sha256((O/p).read_bytes()).hexdigest()==h;hashes+=1
    result=dict(status='passed',center_profiles=checked,groups=groupcount,logit_contrasts=5,hashes=hashes);(O/'independent-review.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
if __name__=='__main__':run()
