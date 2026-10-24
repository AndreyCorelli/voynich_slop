"""Verify scalar fits, frozen gates, and monotone-veto dominance witnesses."""
from benchmarks.grammar_monotone_calibration_iteration117 import *
from benchmarks.grammar_endpoint_reliability_iteration116_review import independent_stats
from scipy.optimize import brentq
from scipy.special import expit


def run():
    hashes=0
    for name in ['design-freeze','model-freeze','policy-freeze','predictions-freeze']:
        for p,h in load(OUT/(name+'.json'))['inputs'].items():assert digest(p)==h,p;hashes+=1
    split=load(PREVIOUS/'type-split.json');anchors=load(ROOT/'iteration85/anchor-budgets.json')['195'];oof=load(PREVIOUS/'oof-profiles.json');models=load(OUT/'models.json');rawcal=load(PREVIOUS/'calibration-probabilities.json');train=split['training'];cal=split['calibration'];lookup=lambda w:hashlib.sha256(('cal98-full|'+w).encode()).hexdigest()
    for arm,m in models.items():
        words=cal if arm=='offset8' else train;p=np.array([rawcal['full']['raw'][lookup(w)] if arm=='offset8' else oof[w]['mean'] for w in words]);y=np.array([int(anchors[w]=='CCONJ') for w in words]);w=np.ones(len(y))
        if arm=='balanced13':
            for c in [0,1]:w[y==c]=1./np.count_nonzero(y==c)
        x=np.log((p+1e-12)/(1-p+1e-12));f=lambda b:float(np.dot(w,expit(x+b)-y));root=brentq(f,-40,40,xtol=1e-13);assert abs(root-m['offset'])<1e-11 and abs(f(m['offset']))<1e-10
    curves=load(OUT/'calibration-curves.json');chosen=load(OUT/'chosen.json');rows=load(OUT/'calibration-cases.json');baseline=independent_stats(rows,'base',None);cutoffs=0
    for arm,curve in curves.items():
        eligible=[]
        for r in curve:
            s=independent_stats(rows,arm,r['cutoff']);assert s==r['stats'];ok=all(v['calls'] and v['hit']/v['calls']>=.9 and not v['clean_wrong'] and not v['unsupported_wrong'] and v['hit']>=math.ceil(.8*baseline[g]['hit']) for g,v in s.items()) and s['complete']['hit']>=4 and s['omission']['distinct_hits']>=4 and s['literal']['distinct_hits']>=4;assert ok==r['qualified'];cutoffs+=1
            if ok:eligible.append(r)
        expected=max(eligible,key=lambda r:(r['stats']['complete']['hit'],sum(s['hit'] for s in r['stats'].values()),-sum(s['wrong'] for s in r['stats'].values()),r['cutoff'])) if eligible else dict(cutoff=None,qualified=False);assert expected==chosen[arm]
    quality={};profiles=0
    for name,pool in [('calibration',cal),('evaluation',split['evaluation'])]:
        raw=load(PREVIOUS/(name+'-probabilities.json'));calibrated=load(OUT/(name+'-probabilities.json'));cases=load(OUT/(name+'-cases.json'));old=load(PREVIOUS/(name+'-cases.json'))
        for view,pp in raw.items():
            for arm,m in models.items():
                ids=list(pp['raw']);p=np.array([pp['raw'][i] for i in ids]);q=expit(np.log((p+1e-12)/(1-p+1e-12))+m['offset']);assert np.allclose(q,[calibrated[view][arm][i] for i in ids],rtol=1e-12,atol=1e-12);assert all((p[i]<p[j])==(q[i]<q[j]) for i in range(len(p)) for j in range(len(p)));profiles+=len(ids)
        for r,prior in zip(cases,old):
            assert all(r[k]==prior[k] for k in prior if k!='margins')
            for arm,margin in r['margins'].items():assert margin==pair_margin(r['base_pair'],r['proposed'],calibrated[r['physical_view']][arm])
        quality[name]={}
        for arm in ['raw']+list(models):
            pp=raw['full']['raw'] if arm=='raw' else calibrated['full'][arm];p=[pp[lookup(w)] for w in pool];y=[anchors[w]=='CCONJ' for w in pool];pos=[q for q,v in zip(p,y) if v];neg=[q for q,v in zip(p,y) if not v];quality[name][arm]=dict(types=len(pool),accuracy=sum((q>.5)==v for q,v in zip(p,y))/len(p),nll=-sum(math.log(max(1e-12,q if v else 1-q)) for q,v in zip(p,y))/len(p),auc=sum((a>b)+.5*(a==b) for a in pos for b in neg)/(len(pos)*len(neg)))
    test=load(OUT/'evaluation-cases.json');expected={'base':independent_stats(test,'base',None),**{a:independent_stats(test,a,r['cutoff']) for a,r in chosen.items()}};assert expected==load(OUT/'evaluation-summary.json')
    # Independent direct-probability two-threshold enumeration and witnesses.
    active=[r for r in rows if r['base_pair'] is not None]
    def xy(r):
        pp=rawcal[r['physical_view']]['raw'];return tuple(next(pp[i] for i in r['base_pair'] if r['proposed'][i]==tag) for tag in ['ADP','CCONJ'])
    points=[xy(r) for r in active];bad=[i for i,r in enumerate(active) if r['base_pair']!=r['reference']['pair']];witnesses=[];counts={};oracle=load(OUT/'calibration-ceiling.json');grid=0;qualifiers=0;best=None
    for low in sorted({p[0] for p in points}|{float('-inf'),float('inf')}):
        for high in sorted({p[1] for p in points}|{float('-inf'),float('inf')}):
            accepted=[r for r,(x,y) in zip(active,points) if x>=low and y<=high];grid+=1
            if any(r['base_pair']!=r['reference']['pair'] for r in accepted):continue
            s={g:sum(r['regime']==g for r in accepted) for g in ['complete','omission','literal']}
            if best is None or (s['complete'],sum(s.values()))>(best['complete'],sum(best.values())):best=s
            if all(s[g]>=math.ceil(.8*baseline[g]['hit']) for g in s) and s['complete']>=4 and all(len({r['case'] for r in accepted if r['regime']==g})>=4 for g in ['omission','literal']):qualifiers+=1
    # This bank's safe policies have no residual wrong calls, so the zero-wrong
    # independent oracle and the design's >=90% precision oracle coincide.
    assert grid==oracle['grid_settings'] and qualifiers==oracle['qualifying_settings']==0;assert best=={g:v['hit'] for g,v in oracle['best_safe']['stats'].items()}
    for i,r in enumerate(active):
        if r['base_pair']!=r['reference']['pair']:continue
        x,y=points[i];w=next((j for j in bad if points[j][0]>=x and points[j][1]<=y),None)
        if w is not None:witnesses.append(dict(regime=r['regime'],case=r['case'],physical_view=r['physical_view'],correct_scores=[x,y],wrong_case=active[w]['case'],wrong_regime=active[w]['regime'],wrong_view=active[w]['physical_view'],wrong_scores=list(points[w])))
    for g in ['complete','omission','literal']:counts[g]=dict(correct=baseline[g]['hit'],dominated=sum(w['regime']==g for w in witnesses),not_dominated=baseline[g]['hit']-sum(w['regime']==g for w in witnesses))
    save(OUT/'dominance-witnesses.json',dict(calibration_only=True,counts=counts,witnesses=witnesses));save(OUT/'diagnostic-summary.json',dict(class_quality=quality,all_three_arms_off=True,monotone_weaker_endpoint_veto_calibration_ceiling=oracle,dominance_counts=counts));save(OUT/'audit.json',dict(input_hashes_verified=hashes,scalar_fits_independently_recomputed=3,calibration_cutoffs_replayed=cutoffs,calibrated_type_probabilities_checked=profiles,oracle_threshold_settings_independently_checked=grid,dominance_witnesses_verified=len(witnesses),heldout_policies_replayed=len(expected),ranking_preserved=True));print('QUALITY',quality);print('DOMINANCE',counts);print('AUDIT',load(OUT/'audit.json'))
if __name__=='__main__':run()
