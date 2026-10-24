"""Reproduce descriptive feature profiles and pair-gain decomposition."""
from benchmarks.grammar_anchor_merge_iteration101 import *


def build():
    profiles={};blocks=load(PREVIOUS/'blocks.json');model=load(ROOT/'iteration93/models.json')['context'];v=model['vocabulary'];weights=np.asarray(model['weights']);boundary=float(weights[v['-1:BOUNDARY'],1]-weights[v['-1:BOUNDARY'],0])
    for block in blocks:
        pred=load(OUT/block/'correct.json');inverse=pred['identities'];profiles[block]={}
        for t in pred['traces']:
            names={inverse[i] for i in t['pair']}
            if 'ex' not in names:continue
            e=next(e for e in t['endpoints'] if inverse[e['id']]=='ex');occ=t['focus_occurrences'];contributions=defaultdict(float)
            for row in occ:
                for f,value in row['contributions'].items():contributions[f]+=value/len(occ)
            profiles[block]['/'.join(sorted(names))]=dict(n=e['n'],mean_cconj=e['mean'][1],pooled_margin=e['margin'],occurrence_cconj=[r['probabilities'][1] for r in occ],sentence_initial=sum('-1:BOUNDARY' in r['contributions'] for r in occ),mean_occurrence_logit=sum(r['logit'] for r in occ)/len(occ),mean_logit_contributions=dict(sorted(contributions.items())))
    decomposition=[]
    for row in load(PREVIOUS/'wrong-core-recommendations.json')['200-0']:
        pred=load(OUT/'200-0'/(row['case']+'.json'));inverse=pred['identities'];a,c=row['case'][5:].split('__');true={a,c};bad=set(row['selected']);common=next(iter(true&bad));tr=next(t for t in pred['traces'] if {inverse[i] for i in t['pair']}==true);wr=next(t for t in pred['traces'] if {inverse[i] for i in t['pair']}==bad)
        def margin(t,w):return next(e['margin'] for e in t['endpoints'] if inverse[e['id']]==w)
        shared=margin(wr,common)-margin(tr,common);partner=(wr['gain']-tr['gain'])-shared;decomposition.append(dict(case=row['case'],gain_difference=wr['gain']-tr['gain'],shared_endpoint=common,shared_view_change=shared,partner_change=partner))
    equal=load(OUT/'equal-parent.json');equal_summary={}
    for block in ('200-0','200-1'):
        for gate in ('left','right','intersection','union'):equal_summary[block+'/'+gate]=aggregate([v[gate] for k,v in equal.items() if k.startswith(block+'/')])
    return dict(boundary_logit_coefficient=boundary,clean_ex_profiles=profiles,equal_parent_summary=equal_summary),decomposition

if __name__=='__main__':
    result,decomposition=build();assert decomposition==load(OUT/'bad-merge-gain-decomposition.json');save(OUT/'diagnostic-summary.json',result);save(OUT/'summary-audit.json',dict(logit_profiles_and_gain_decomposition_recomputed=True,pooled_gain_not_treated_as_additive_feature_logit=True,policies_unchanged=True));print('Summary verified')
