"""Independent ranking, medians and linear score decomposition replay."""
from pathlib import Path
import json,hashlib,statistics,math
P=Path('experiments/results/grammar-restoration');O=P/'iteration208';S=P/'iteration207'
def read(p):return json.loads(p.read_text())
def close(a,b):
    if isinstance(a,list):
        assert len(a)==len(b)
        for x,y in zip(a,b):close(x,y)
    elif a is None:assert b is None
    else:assert math.isclose(a,b,abs_tol=1e-11,rel_tol=1e-11),(a,b)
def run():
    f=read(S/'features.json');y=read(S/'teacher-labels.json');pred=read(S/'predictions.json');models=read(S/'models.json');d=read(O/'details.json');summary=read(O/'summary.json');ranks=0;heads=0
    for a,rows in f.items():
        pos=[i for i in range(len(rows)) if y[a][i]];neg=[i for i in range(len(rows)) if not y[a][i]]
        for name,s in pred[a].items():
            v=d[a][name];assert [r['index'] for r in v['supported']]==pos
            for r in v['supported']:
                i=r['index'];higher=[j for j in range(len(s)) if s[j]>s[i]];equal=[j for j in range(len(s)) if s[j]==s[i]]
                assert r['rank_first']==len(higher)+1 and r['rank_last']==len(higher)+len(equal)
                assert r['higher_unsupported']==[j for j in higher if j in neg] and r['tied_unsupported']==[j for j in equal if j in neg];assert r['word']==rows[i]['word'];ranks+=1
            cut=sorted(s,reverse=True)[4];head=[i for i in neg if s[i]>=cut];assert head==[r['index'] for r in v['unsupported_top5']];heads+=len(head)
            for r in v['unsupported_top5']:
                for field,col in [('degree',1),('frequency',0)]:
                    value=sum(rows[r['index']]['values'][col]>rows[j]['values'][col] for j in pos)/len(pos) if pos else None
                    close(value,r[field+'_above_supported_fraction'])
            for label,indices in [('supported',pos),('unsupported_head',head),('all_unsupported',neg)]:
                expected=[statistics.median(rows[i]['values'][j] for i in indices) for j in range(12)] if indices else None;close(expected,v['feature_medians'][label])
            if name=='full12' and pos and head:
                m=models[a][name];contributions=[]
                for j in range(12):
                    delta=statistics.mean(rows[i]['values'][j] for i in head)-statistics.mean(rows[i]['values'][j] for i in pos)
                    contributions.append(delta*m['beta'][j+1]/m['scale'][j])
                close(contributions,v['head_minus_supported_mean_logit_contributions']);close(sum(contributions),v['head_minus_supported_mean_logit'])
            srow=summary[a][name];assert srow['supported_rank_intervals']==[[r['rank_first'],r['rank_last']] for r in v['supported']];assert srow['unsupported_head']==len(head)
            for field in ['degree','frequency']:
                close(statistics.mean(r[field+'_above_supported_fraction'] for r in v['unsupported_top5']) if pos and head else None,srow['head_'+field+'_above_supported_fraction'])
            close(v['head_minus_supported_mean_logit'],srow['logit_gap'])
    n=0
    for manifest in [read(O/'design-freeze.json'),read(S/'verification-manifest.json')]:
        for p,h in manifest.items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h;n+=1
    result=dict(status='passed',supported_rank_records=ranks,unsupported_head_records=heads,ranking_groups=16,hashes=n)
    (O/'independent-review.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
if __name__=='__main__':run()
