"""Replay frozen oracle predictions and attribute underspecified readings."""
from benchmarks.grammar_pos_oracle_iteration72 import *
def run():
    for p,h in load(OUT/'design-freeze.json')['inputs'].items():assert digest(p)==h,p
    assert digest(OUT/'predictions.json')==load(OUT/'prediction-freeze.json')['predictions']
    rows=load(OUT/'predictions.json');old=load(PREVIOUS/'predictions.json');m=load(ROOT/'iteration70/model.json');counts=Counter()
    assert len(rows)==len(old)==1273
    for r,b in zip(rows,old):
        assert all(r[k]==b[k] for k in ('sid','index','word','other','gold_profile'))
        replay=scores(m,b)
        for name,s in replay.items():assert np.allclose(s,r['scores'][name],atol=1e-12,rtol=1e-12)
        pos=b['gold_profile'][0]
        unspecified=any(a[0]==pos and not a[1] and not a[2] for a in b['readings'][1])
        if unspecified:
            counts['distractor_has_correctPOS_with_unspecified_Case_Number']+=1
            if b['gold_profile'][1] or b['gold_profile'][2]:
                counts['unspecified_distractor_with_nonempty_gold_morphology']+=1
                counts['within_context_losses_nonempty_gold']+=r['scores']['pos_oracle_within_context'][0]<r['scores']['pos_oracle_within_context'][1]-1e-10
            counts['within_context_losses_in_that_group']+=r['scores']['pos_oracle_within_context'][0]<r['scores']['pos_oracle_within_context'][1]-1e-10
    ev=load(OUT/'evaluation.json');assert summarize(rows)==ev['all'];assert summarize([r for r in rows if r['scores']['oracle_morph'][0]==1])==ev['original_gold_analysis_present']
    checked=0
    for path in ROOT.glob('iteration*/verification-manifest.json'):
        if path.parent==OUT:continue
        for p,h in load(path).get('inputs',{}).items():assert digest(p)==h,(path,p);checked+=1
    result=dict(replayed=len(rows),prior_input_hashes_verified=checked,posthoc_specificity_attribution=dict(counts),reserve_unscored=True);save(OUT/'audit.json',result);print(result)
if __name__=='__main__':run()
