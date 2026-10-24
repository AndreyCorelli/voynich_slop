"""Normalize missing dictionary features over joint source profiles."""
from benchmarks.grammar_role_compatibility_iteration70 import *
from benchmarks.grammar_pos_oracle_iteration72 import condition_pos,summarize
PREVIOUS=ROOT/'iteration72';OUT=ROOT/'iteration73'
def profile_space(model):
    profiles=sorted({tuple(g) for _,g in model['labels']});index={g:i for i,g in enumerate(profiles)}
    prior=np.zeros(len(profiles))
    for (_,g),q in zip(model['labels'],model['prior']):prior[index[tuple(g)]]+=q
    return profiles,prior

def collapse(model,p,profiles):
    index={g:i for i,g in enumerate(profiles)};q=np.zeros(len(profiles))
    for (_,g),v in zip(model['labels'],p):q[index[tuple(g)]]+=v
    return q

def reading_distribution(reading,profiles,prior):
    # Blank or X-derived fields are unresolved. Expand only to joint source
    # profiles admitted by the reading, never a Cartesian product of fields.
    q=np.array([v if compatible(g,reading) else 0. for g,v in zip(profiles,prior)])
    return q/q.sum() if q.sum() else q

def normalized_score(p,rr,ww,profiles,prior):
    return float(sum(w*np.dot(p,reading_distribution(r,profiles,prior)) for r,w in zip(rr,ww)))

def compute(model,r):
    profiles,prior=profile_space(model);out={};rr=r['readings'];ww=r['weights'];pos=r['gold_profile'][0]
    for name,p in [('context',posterior(model,r['context'])),('shuffle',posterior(model,r['shuffled_context'])),('prior',model['prior'])]:
        for prefix,q in [('',p),('oracle_pos_',condition_pos(model,p,pos))]:
            cp=collapse(model,q,profiles);out[prefix+'normalized_'+name]=[normalized_score(cp,a,w,profiles,prior) for a,w in zip(rr,ww)]
    out['baseline_weighted_context']=r['scores']['weighted_context'];out['frequency']=r['scores']['frequency']
    return out

def run():
    assert not OUT.exists();OUT.mkdir()
    for p,h in load(PREVIOUS/'verification-manifest.json')['inputs'].items():assert digest(p)==h,p
    paths=[Path(__file__),Path('benchmarks/grammar_role_compatibility_iteration70.py'),Path('benchmarks/grammar_pos_oracle_iteration72.py'),ROOT/'iteration71/predictions.json',ROOT/'iteration70/model.json',ROOT/'iteration1/morphology-lattice.json',PREVIOUS/'verification-manifest.json',Path('experiments/holdouts/grammar-construction-next.json')]
    (OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='Fixed1273pairs, frozencontextmodel and71wordPOSreadingweights. Collapse role labels into jointPOS/Case/Number profiles. Each reading becomes normalized sourceprior over compatible joint profiles; blank/X-derived feature is unresolved, not unrestricted posterior mass. Structural NA represented by empty sourceprofile feature; candidate emptyfields integrate over admitted profiles, no crossfeature recombination. Unsupportedreading zero; unknownentry zero; wordPOS mass not renormalized. Score expected overlap of contextual posterior and candidate reading distribution. Report predicted and oraclePOS arms against matching prior/shuffle, baseline and frequency. Primary predicted strictwin>=65%, >=matchingprior+10pp, >=shuffle+5pp and >=frequency+10pp. If fails no historical corruption or search. Oracle gains diagnostic only. Fixed-pair candidate construction referencePOS remains privileged. No tuning; reserve unscored.'))
    # Audit raw schema before scoring the fixed pairs.
    lex=load(ROOT/'iteration1/morphology-lattice.json');save(OUT/'schema-audit.json',dict(affected612='All612specifiedreference/unspecifieddistractor cases are NOUN readings of non.',raw_non=lex['non'],interpretation='NOUN Case=X Number=X is unresolved dictionary inflection, not nonapplicable; ADV blankCase/Number represents structural absence in sourceprofiles. Projected caches cannot resolve all missingness causes; no universal schema repair claimed.'))
    m=load(ROOT/'iteration70/model.json');old=load(ROOT/'iteration71/predictions.json');rows=[dict(sid=r['sid'],index=r['index'],word=r['word'],other=r['other'],gold_profile=r['gold_profile'],scores=compute(m,r)) for r in old]
    save(OUT/'predictions.json',rows);save(OUT/'prediction-freeze.json',dict(predictions=digest(OUT/'predictions.json')));result=summarize(rows);a=result['arms'];c=a['normalized_context']['strict_accuracy'];result.update(gate_passed=c>=.65 and c>=a['normalized_prior']['strict_accuracy']+.10 and c>=a['normalized_shuffle']['strict_accuracy']+.05 and c>=a['frequency']['strict_accuracy']+.10,search_run=False,nuclei_measured=False);save(OUT/'evaluation.json',result);print(json.dumps(result,indent=2))
if __name__=='__main__':run()
