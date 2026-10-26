"""Descriptive audit of frozen rankings; no model or teacher changes."""
from pathlib import Path
import json,hashlib
import numpy as np
P=Path('experiments/results/grammar-restoration');O=P/'iteration208';S=P/'iteration207'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def median(rows):return np.median(rows,axis=0).tolist() if len(rows) else None

def run():
    assert not O.exists();O.mkdir();(O/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    inputs=[Path(__file__)]+[S/n for n in ['verification-manifest.json','features.json','teacher-labels.json','predictions.json','models.json','selections.json']]
    save(O/'design-freeze.json',{str(p):sha(p) for p in inputs})
    for p,h in read(S/'verification-manifest.json').items():assert sha(Path(p))==h
    ff=read(S/'features.json');yy=read(S/'teacher-labels.json');pp=read(S/'predictions.json');mm=read(S/'models.json');ss=read(S/'selections.json');details={};summary={}
    for a,rows in ff.items():
        positive=[i for i,v in enumerate(yy[a]) if v];negative=[i for i,v in enumerate(yy[a]) if not v];x=np.array([r['values'] for r in rows]);details[a]={};summary[a]={}
        for name,s in pp[a].items():
            supported=[]
            for i in positive:
                higher=[j for j in negative if s[j]>s[i]];tied=[j for j in negative if s[j]==s[i]]
                supported.append(dict(index=i,word=rows[i]['word'],rank_first=1+sum(v>s[i] for v in s),rank_last=sum(v>=s[i] for v in s),higher_unsupported=higher,tied_unsupported=tied))
            head=[i for i in ss[a][name]['top5'] if i in negative]
            detail=dict(supported=supported,unsupported_top5=[dict(index=i,word=rows[i]['word'],degree_above_supported_fraction=sum(x[i,1]>x[j,1] for j in positive)/len(positive) if positive else None,frequency_above_supported_fraction=sum(x[i,0]>x[j,0] for j in positive)/len(positive) if positive else None) for i in head],feature_medians=dict(supported=median(x[positive]),unsupported_head=median(x[head]),all_unsupported=median(x[negative])))
            if name=='full12' and positive and head:
                m=mm[a][name];delta=(x[head].mean(0)-x[positive].mean(0))/np.array(m['scale']);contribution=delta*np.array(m['beta'][1:]);detail['head_minus_supported_mean_logit_contributions']=contribution.tolist();detail['head_minus_supported_mean_logit']=float(contribution.sum())
            else:detail['head_minus_supported_mean_logit_contributions']=None;detail['head_minus_supported_mean_logit']=None
            details[a][name]=detail
            summary[a][name]=dict(supported_rank_intervals=[[r['rank_first'],r['rank_last']] for r in supported],unsupported_head=len(head),head_degree_above_supported_fraction=float(np.mean([r['degree_above_supported_fraction'] for r in detail['unsupported_top5']])) if positive and head else None,head_frequency_above_supported_fraction=float(np.mean([r['frequency_above_supported_fraction'] for r in detail['unsupported_top5']])) if positive and head else None,logit_gap=detail['head_minus_supported_mean_logit'])
    save(O/'details.json',details);save(O/'summary.json',summary)
    print(json.dumps(summary,indent=2))
if __name__=='__main__':run()
