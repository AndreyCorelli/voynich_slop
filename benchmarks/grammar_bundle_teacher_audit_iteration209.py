"""Reference-only mechanism audit; no model or teacher changes."""
from pathlib import Path
from collections import Counter,defaultdict
import math,json,hashlib
import numpy as np
P=Path('experiments/results/grammar-restoration');O=P/'iteration209'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
FIELDS=['center_global_case_fraction','center_queried_case_fraction','observed_both','expected_both','observed_match','expected_match','mean_surplus','term_match_variability','robust_statistic','null_std','raw_tail','adjusted_tail']
def group(rows):
    return dict(n=len(rows),means={k:float(np.mean([r[k] for r in rows])) if rows else None for k in FIELDS},no_recognized_comparison_opportunity=sum(not r['recognized_opportunity'] for r in rows),no_variable_match_opportunity=sum(not r['variable_match_opportunity'] for r in rows),sampled_zero_robust_null_variation=sum(r['null_range']<=1e-12 for r in rows),positive_robust_statistic=sum(r['robust_statistic']>1e-12 for r in rows),positive_surplus=sum(r['mean_surplus']>1e-12 for r in rows))
def run():
    assert not O.exists();O.mkdir();(O/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__)]+[P/n for n in ['iteration193/graphs.json','iteration201/development-references.json','iteration205/candidates.json','iteration205/details.json','iteration205/statistics.json','iteration207/selections.json','iteration207/teacher-labels.json','iteration207/verification-manifest.json','iteration208/verification-manifest.json']]
    save(O/'design-freeze.json',{str(p):sha(p) for p in paths})
    for it in ['iteration207','iteration208']:
        for p,h in read(P/it/'verification-manifest.json').items():assert sha(Path(p))==h
    graphs=read(P/'iteration193/graphs.json');refs=read(P/'iteration201/development-references.json');bb=read(P/'iteration205/candidates.json');old=read(P/'iteration205/details.json');stats=read(P/'iteration205/statistics.json');selections=read(P/'iteration207/selections.json');yy=read(P/'iteration207/teacher-labels.json');details={};summary={}
    for a in selections:
        g=graphs[a];ref=refs[a];profiles=defaultdict(Counter);loc=defaultdict(list)
        for i,p in enumerate(g['positions']):
            if p:profiles[(g['ids'][i],ref['pos'][i])][ref['case'][i]]+=1;loc[g['ids'][i]].append(i)
        prob={k:{c:n/sum(v.values()) for c,n in v.items() if c} for k,v in profiles.items()};rows=[]
        for j,b in enumerate(bb[a]):
            total=Counter();recognized=False;variable=False;pivots=set()
            for ei in b['edges']:
                e=g['descriptors'][ei];side='a' if e['a']==b['word'] else 'b'
                for f in e['frames']:
                    pivots.update(f[side+'_positions']);w=1/(len(e['frames'])*len(f['a_positions'])*len(f['b_positions']))
                    for p in f['a_positions']:
                        for q in f['b_positions']:
                            u=prob[(g['ids'][p],ref['pos'][p])];v=prob[(g['ids'][q],ref['pos'][q])];expected=sum(x*v.get(c,0) for c,x in u.items());both=sum(u.values())*sum(v.values());observed=int(bool(ref['case'][p]) and ref['case'][p]==ref['case'][q]);oboth=int(bool(ref['case'][p]) and bool(ref['case'][q]));recognized|=bool(u) and bool(v);variable|=expected>1e-12 and expected<1-1e-12
                            for k,value in [('observed_both',oboth),('expected_both',both),('observed_match',observed),('expected_match',expected),('term_match_variability',expected*(1-expected))]:total[k]+=w*value
            d=old[a]['edge_or_pivot'][j];null=np.array(stats[a]['edge_or_pivot']['values'])[1:,j];degree=len(b['edges']);r=dict(index=j,word=b['word'],degree=degree,supported=bool(yy[a][j]),center_global_case_fraction=sum(bool(ref['case'][p]) for p in loc[b['word']])/len(loc[b['word']]),center_queried_case_fraction=sum(bool(ref['case'][p]) for p in pivots)/len(pivots),**{k:total[k]/degree for k in ['observed_both','expected_both','observed_match','expected_match','term_match_variability']},mean_surplus=(total['observed_match']-total['expected_match'])/degree,recognized_opportunity=bool(recognized),variable_match_opportunity=bool(variable),robust_statistic=d['statistic'],raw_tail=d['raw_tail'],adjusted_tail=d['max_stat_tail'],null_std=float(null.std()),null_range=float(np.ptp(null)))
            assert abs(r['mean_surplus']*degree-d['original_sum'])<1e-10;rows.append(r)
        details[a]=rows;summary[a]=dict(all=group(rows),supported=group([r for r in rows if r['supported']]),unsupported=group([r for r in rows if not r['supported']]),heads={name:group([rows[i] for i in ix['top5'] if not rows[i]['supported']]) for name,ix in selections[a].items()})
    save(O/'details.json',details);save(O/'summary.json',summary)
    for a,v in summary.items():print(a,json.dumps({'supported':v['supported'],'full12_head':v['heads']['full12']}))
if __name__=='__main__':run()
