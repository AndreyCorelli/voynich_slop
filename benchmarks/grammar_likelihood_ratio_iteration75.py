"""Fixed-pair contextual Bayes-factor ablation; no tuned prior mixing."""
from benchmarks.grammar_normalized_readings_iteration73 import *
from benchmarks.grammar_weighted_readings_iteration71 import weights
PREVIOUS=ROOT/'iteration74';OUT=ROOT/'iteration75'
def evidence(p,rr,ww,profiles,prior,normalize=False):
    # Candidate analysis prior remains explicit. Context-only normalizes total
    # supported reading weight; raw evidence retains candidate supported mass.
    ratio=np.divide(p,prior,out=np.zeros_like(p),where=prior>0)
    distributions=[reading_distribution(r,profiles,prior) for r in rr]
    supported=sum(w for w,d in zip(ww,distributions) if d.sum()>0)
    numerator=float(sum(w*np.dot(d,ratio) for w,d in zip(ww,distributions)))
    return numerator/supported if normalize and supported>0 else numerator

def compute75(model,r):
    profiles,prior=profile_space(model);rr=r['readings'];ww=r['weights'];out={}
    for arm,p in [('context',posterior(model,r['context'])),('shuffle',posterior(model,r['shuffled_context'])),('prior',model['prior'])]:
        cp=collapse(model,p,profiles)
        out['likelihood_'+arm]=[evidence(cp,a,w,profiles,prior) for a,w in zip(rr,ww)]
        out['context_only_'+arm]=[evidence(cp,a,w,profiles,prior,True) for a,w in zip(rr,ww)]
    out['frequency']=r['scores']['frequency'];out['baseline_weighted_context']=r['scores']['weighted_context']
    return out

def run():
    assert not OUT.exists();OUT.mkdir()
    for p,h in load(PREVIOUS/'verification-manifest.json')['inputs'].items():assert digest(p)==h,p
    paths=[Path(__file__),Path('benchmarks/grammar_normalized_readings_iteration73.py'),Path('benchmarks/grammar_role_compatibility_iteration70.py'),Path('benchmarks/grammar_pos_oracle_iteration72.py'),ROOT/'iteration70/model.json',ROOT/'iteration71/predictions.json',PREVIOUS/'verification-manifest.json',Path('experiments/holdouts/grammar-construction-next.json')]
    (OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='Same1273frozenpairs; no refit. Jointprofile ratio posterior/context divided by sourceprior. Integrate against73normalized reading distributions and71wordPOS weights. Primary raw likelihood retains supported candidate reading mass (explicit lexicalprior); contextonly divides by supportedmass, keeps0 for unknown/unsupported. Report both vs savedshuffle and prior; no goldPOS inference arms. Frequency and71baseline controls. Primary rawlikelihood strictwins>=65%, >=prior+10pp, >=shuffle+5pp and >=frequency+10pp. Contextonly secondary not selectable after results. No tunableweights. If primaryfails no historicalcorruption or search; ifpasses freeze corruption phase before evaluation. Reserveunscored. Existingpairselection referencePOS and correctsurroundingplaintext remain privileges.'))
    model=load(ROOT/'iteration70/model.json');old=load(ROOT/'iteration71/predictions.json');rows=[dict(sid=r['sid'],index=r['index'],word=r['word'],other=r['other'],gold_profile=r['gold_profile'],scores=compute75(model,r)) for r in old]
    save(OUT/'predictions.json',rows);save(OUT/'prediction-freeze.json',dict(predictions=digest(OUT/'predictions.json')));result=summarize(rows);a=result['arms'];c=a['likelihood_context']['strict_accuracy'];result.update(gate_passed=c>=.65 and c>=a['likelihood_prior']['strict_accuracy']+.10 and c>=a['likelihood_shuffle']['strict_accuracy']+.05 and c>=a['frequency']['strict_accuracy']+.10,search_run=False,nuclei_measured=False);save(OUT/'evaluation.json',result);print(json.dumps(result,indent=2))
if __name__=='__main__':run()
