"""Independent source cutoff, fixed top-k and class-reference selection audit."""
from benchmarks.grammar_selective_classes_iteration140 import *
from scipy.special import expit

def checked_metrics(rows,anchors,metric):
    correct=sum((r['probability']>.5)==(anchors[r['type']]=='CCONJ') for r in rows);assert metric['selected']==len(rows) and metric['correct']==correct and metric['wrong']==len(rows)-correct;assert metric['accuracy']==(correct/len(rows) if rows else None)

def run():
    hashes=0
    for name in ['design-freeze','policy-freeze','selection-freeze']:
        for p,h in load(OUT/(name+'.json'))['inputs'].items():assert digest(p)==h,p;hashes+=1
    anchors=load(ROOT/'iteration85/anchor-budgets.json')['195'];train=load(ROOT/'iteration116/type-split.json')['training'];oof=load(ROOT/'iteration135/oof-probabilities.json')['corrected'];offset=load(ROOT/'iteration135/calibrators.json')['corrected']['offset'];stats=load(ROOT/'iteration135/training-statistics.json');source=[]
    for w in train:
        p=oof[w];q=float(expit(math.log((p+1e-12)/(1-p+1e-12))+offset));n=stats[hashlib.sha256(('fit116|'+w).encode()).hexdigest()]['n']
        if n>=5:source.append(dict(type=w,n=n,probability=q,confidence=max(q,1-q)))
    frozen=load(OUT/'source-candidates.json');assert len(source)==len(frozen)
    for a,b in zip(source,frozen):assert a['type']==b['type'] and abs(a['probability']-b['probability'])<1e-12
    curve=load(OUT/'source-curve.json');assert [r['threshold'] for r in curve]==sorted({.5,1.}|{r['confidence'] for r in frozen});good=[]
    for r in curve:
        rows=[x for x in frozen if x['confidence']>=r['threshold']];checked_metrics(rows,anchors,r['metrics']);ok=len(rows)>=3 and sum((x['probability']>.5)==(anchors[x['type']]=='CCONJ') for x in rows)*10>=9*len(rows);assert ok==r['qualified'];assert r['selected_types']==[x['type'] for x in rows]
        if ok:good.append(r)
    chosen=max(good,key=lambda r:(r['metrics']['correct'],-r['metrics']['wrong'],r['threshold'])) if good else dict(threshold=None,qualified=False);assert chosen==load(OUT/'chosen.json');old=load(ROOT/'iteration137/predictions.json');raw=load(ROOT/'iteration138/predictions.json');inputs={'Caesar':old['Caesar-expanded']['concat']['corrected'],'Jerome':old['Jerome-expanded']['concat']['corrected'],**{w:raw[w]['original']['corrected'] for w in ['gellius-1','livy-1']}};selections=load(OUT/'selections.json');evaluation=load(OUT/'evaluation.json');core=set(load(ROOT/'iteration139/common-core.json'));checks=0
    for work,rows in inputs.items():
        eligible=[dict(type=r['type'],n=r['n'],probability=r['probabilities']['new'],confidence=max(r['probabilities']['new'],1-r['probabilities']['new'])) for r in rows if r['n']>=5];expected=dict(eligible=eligible,primary=[r for r in eligible if r['confidence']>=chosen['threshold']] if chosen['qualified'] else [])
        for k in [3,5]:
            cut=sorted((r['confidence'] for r in eligible),reverse=True)[min(k,len(eligible))-1] if eligible else 1.;expected['top'+str(k)]=[r for r in eligible if r['confidence']>=cut]
        assert expected==selections[work]
        for arm,rr in expected.items():
            e=evaluation[work][arm];checked_metrics(rr,anchors,e['all']);checked_metrics([r for r in rr if r['type'] in core],anchors,e['common14']);assert e['wrong_types']==[r['type'] for r in rr if (r['probability']>.5)!=(anchors[r['type']]=='CCONJ')];assert e['selected_types']==[r['type'] for r in rr];assert e['raw_c_reference_ambiguity_present']==(work=='gellius-1' and any(r['type']=='c' for r in rr));checks+=2
    result=load(OUT/'result.json');passed=chosen['qualified'] and all(evaluation[w]['primary']['all']['selected']>=3 and evaluation[w]['primary']['all']['accuracy']>=.9 for w in evaluation);assert result['all_four_texts_passed']==passed;assert not passed;assert all(not s['primary'] for s in selections.values())
    save(OUT/'audit.json',dict(input_hashes_verified=hashes,source_probabilities_verified=len(source),source_thresholds_replayed=len(curve),fixed_target_selection_arms_verified=16,reference_metric_groups_verified=checks,tie_and_support_rules_verified=True,all_primary_target_selections_empty=True,no_fit_or_new_annotations=True));print(load(OUT/'audit.json'))
if __name__=='__main__':run()
