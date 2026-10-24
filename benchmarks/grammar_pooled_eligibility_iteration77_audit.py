"""Replay calibration/test predictions, freeze boundaries and decisions."""
from benchmarks.grammar_pooled_eligibility_iteration77 import *
def run():
    for p,h in load(OUT/'design-freeze.json')['inputs'].items():assert digest(p)==h,p
    for p,h in load(OUT/'calibration-freeze.json')['inputs'].items():assert digest(p)==h,p
    assert digest(OUT/'predictions.json')==load(OUT/'prediction-freeze.json')['predictions']
    partition=load(ROOT/'iteration49/manifest.json')['partitions']['0'];assert not set(partition['fit'])&set(partition['calibration'])
    m=load(ROOT/'iteration70/model.json');pm=load(ROOT/'iteration71/word-pos-model.json');lex=load(ROOT/'iteration23/morphology-lattice.json');lex.update(load(ROOT/'iteration1/morphology-lattice.json'));data=load(ROOT/'iteration44/annotations-truth.json');source=[dict(sent_id=sid,**data[sid]) for sid in partition['calibration']]
    cal=load(OUT/'calibration-predictions.json');replay=predict_split(source,m,pm,lex,7701);assert replay==cal
    policies=load(OUT/'policies.json')
    for task in ('subject','nominative'):
        for arm in ARMS:assert select_policy(cal,task,arm)==policies[task][arm]
    ann={(r['sid'],r['index']):r for r in load(ROOT/'iteration71/predictions.json')};target=[]
    for s in load(ROOT/'iteration23/datasets.json')['test_caesar']:
        ts=[]
        for i,w in enumerate(s['tokens']):
            b=ann.get((s['sent_id'],i));ts.append(dict(word=w,pos=b['gold_profile'][0] if b else 'X',features=dict(Case=b['gold_profile'][1],Number=b['gold_profile'][2]) if b else {},rel=b['role'] if b else '?'))
        target.append(dict(sent_id=s['sent_id'],tokens=ts))
    rows=load(OUT/'predictions.json');assert predict_split(target,m,pm,lex,7001)==rows;assert len(rows)==1273;assert sum(r['labels']['subject'] for r in rows)==107
    assert evaluate(rows,policies)==load(OUT/'evaluation.json')
    # Gold center annotations may select rows and label evaluation, but cannot
    # affect inference scores or the composition of pooled word occurrences.
    altered=[dict(sent_id=s['sent_id'],tokens=[dict(word=t['word'],pos='NOUN',rel='nsubj',features={'Case':'Nom'}) for t in s['tokens']]) for s in target]
    changed={(r['sid'],r['index']):r for r in predict_split(altered,m,pm,lex,7001)}
    assert all(r['scores']==changed[r['sid'],r['index']]['scores'] for r in rows)
    checked=0
    for path in ROOT.glob('iteration*/verification-manifest.json'):
        if path.parent==OUT:continue
        for p,h in load(path).get('inputs',{}).items():assert digest(p)==h,(path,p);checked+=1
    result=dict(calibration_sentences=len(source),calibration_positions=len(cal),target_positions=len(rows),prior_hashes_verified=checked,target_annotation_invariance=True,calibration_fit_disjoint=True,reserve_unscored=True);save(OUT/'audit.json',result);print(result)
if __name__=='__main__':run()
