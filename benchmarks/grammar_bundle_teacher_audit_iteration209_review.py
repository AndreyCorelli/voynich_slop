"""Rational reference reconstruction and independent cached-statistic replay."""
from pathlib import Path
from collections import Counter,defaultdict
from fractions import Fraction as F
import json,math,statistics,hashlib
P=Path('experiments/results/grammar-restoration');O=P/'iteration209'
def read(p):return json.loads(p.read_text())
def close(x,y):
    if x is None:assert y is None
    else:assert math.isclose(x,y,abs_tol=1e-10,rel_tol=1e-10),(x,y)
def run():
    graphs=read(P/'iteration193/graphs.json');refs=read(P/'iteration201/development-references.json');bb=read(P/'iteration205/candidates.json');old=read(P/'iteration205/details.json');stats=read(P/'iteration205/statistics.json');selections=read(P/'iteration207/selections.json');yy=read(P/'iteration207/teacher-labels.json');dd=read(O/'details.json');ss=read(O/'summary.json');terms=0;groups=0
    for a,rows in dd.items():
        g=graphs[a];r=refs[a];profiles=defaultdict(Counter);loc=defaultdict(list)
        for i,p in enumerate(g['positions']):
            if p is not None:profiles[(g['ids'][i],r['pos'][i])][r['case'][i]]+=1;loc[g['ids'][i]].append(i)
        def profile(i):
            v=profiles[(g['ids'][i],r['pos'][i])];return {c:F(n,sum(v.values())) for c,n in v.items() if c}
        for j,(row,b) in enumerate(zip(rows,bb[a])):
            total=[F(0) for _ in range(5)];pivots=set();op=False;var=False
            for ei in b['edges']:
                e=g['descriptors'][ei];side='a' if e['a']==b['word'] else 'b'
                for frame in e['frames']:
                    pivots.update(frame[side+'_positions']);weight=F(1,len(e['frames'])*len(frame['a_positions'])*len(frame['b_positions']))
                    for i in frame['a_positions']:
                        for k in frame['b_positions']:
                            u=profile(i);v=profile(k);expected=sum((u[c]*v[c] for c in set(u)&set(v)),F(0));both=sum(u.values(),F(0))*sum(v.values(),F(0));op|=both>0;var|=0<expected<1
                            values=[int(bool(r['case'][i]) and bool(r['case'][k])),both,int(bool(r['case'][i]) and r['case'][i]==r['case'][k]),expected,expected*(1-expected)]
                            total=[x+weight*y for x,y in zip(total,values)];terms+=1
            degree=len(b['edges']);assert row['word']==b['word'] and row['supported']==bool(yy[a][j]) and row['degree']==degree
            for field,value in zip(['observed_both','expected_both','observed_match','expected_match','term_match_variability'],total):close(float(value/degree),row[field])
            close(float((total[2]-total[3])/degree),row['mean_surplus']);close(float(total[2]-total[3]),old[a]['edge_or_pivot'][j]['original_sum'])
            for field,pp in [('center_global_case_fraction',loc[b['word']]),('center_queried_case_fraction',pivots)]:close(sum(bool(r['case'][i]) for i in pp)/len(pp),row[field])
            assert op==row['recognized_opportunity'] and var==row['variable_match_opportunity']
            matrix=stats[a]['edge_or_pivot']['values'];null=[v[j] for v in matrix[1:]];maximum=[max(v) for v in matrix[1:]];real=matrix[0][j];close(real,row['robust_statistic']);close(statistics.pstdev(null),row['null_std']);close(max(null)-min(null),row['null_range'])
            for field,values in [('raw_tail',null),('adjusted_tail',maximum)]:close((1+sum(v>=real-1e-12 for v in values))/200,row[field])
        groupset={'all':rows,'supported':[r for r in rows if r['supported']],'unsupported':[r for r in rows if not r['supported']]}
        groupset.update({'head/'+n:[rows[i] for i in v['top5'] if not rows[i]['supported']] for n,v in selections[a].items()})
        for name,rr in groupset.items():
            v=ss[a]['heads'][name[5:]] if name.startswith('head/') else ss[a][name];assert v['n']==len(rr)
            for field,mean in v['means'].items():close(statistics.mean(r[field] for r in rr) if rr else None,mean)
            for field,key in [('no_recognized_comparison_opportunity','recognized_opportunity'),('no_variable_match_opportunity','variable_match_opportunity')]:assert v[field]==sum(not r[key] for r in rr)
            assert v['sampled_zero_robust_null_variation']==sum(r['null_range']<=1e-12 for r in rr)
            assert v['positive_robust_statistic']==sum(r['robust_statistic']>1e-12 for r in rr) and v['positive_surplus']==sum(r['mean_surplus']>1e-12 for r in rr);groups+=1
    hashes=0
    for manifest in [read(O/'design-freeze.json')]+[read(P/it/'verification-manifest.json') for it in ['iteration207','iteration208']]:
        for p,h in manifest.items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h;hashes+=1
    result=dict(status='passed',centers=sum(map(len,dd.values())),rational_weighted_terms=terms,groups=groups,hashes=hashes);(O/'independent-review.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
if __name__=='__main__':run()
