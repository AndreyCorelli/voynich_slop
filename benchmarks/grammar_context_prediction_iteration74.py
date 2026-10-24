"""Direct predictive audit of frozen contextual grammar, independent of candidates."""
from benchmarks.grammar_role_compatibility_iteration70 import *
from benchmarks.grammar_normalized_readings_iteration73 import profile_space,collapse
from benchmarks.grammar_pos_oracle_iteration72 import condition_pos
OUT=ROOT/'iteration74';PREVIOUS=ROOT/'iteration73';EPS=1e-12

def probability_record(model,p,g,profiles):
    cp=collapse(model,p,profiles);pos=sorted({x[0] for x in profiles});pp=[sum(v for x,v in zip(profiles,cp) if x[0]==t) for t in pos];cq=collapse(model,condition_pos(model,p,g[0]),profiles)
    ix=profiles.index(tuple(g)) if tuple(g) in profiles else None
    return dict(pos_probability=pp[pos.index(g[0])] if g[0] in pos else 0.,pos_correct=pos[int(np.argmax(pp))]==g[0],joint_probability=float(cp[ix]) if ix is not None else 0.,joint_correct=list(profiles[int(np.argmax(cp))])==list(g),conditional_probability=float(cq[ix]) if ix is not None else 0.,conditional_correct=bool(cq.sum()) and list(profiles[int(np.argmax(cq))])==list(g),pos_prediction=pos[int(np.argmax(pp))],conditional_prediction=profiles[int(np.argmax(cq))] if cq.sum() else None)

def metrics(rows,task,arm):
    prob=[r['predictions'][arm][task+'_probability'] for r in rows];correct=[r['predictions'][arm][task+'_correct'] for r in rows]
    return dict(n=len(rows),nll=float(np.mean([-math.log(max(EPS,p)) for p in prob])),accuracy=float(np.mean(correct)),zero_probability=int(sum(p==0 for p in prob)))

def evaluate(rows):
    subsets={'all':rows,'supported_reference_profile':[r for r in rows if r['supported']], 'specified_case_or_number':[r for r in rows if r['gold_profile'][1] or r['gold_profile'][2]],'supported_specified':[r for r in rows if r['supported'] and (r['gold_profile'][1] or r['gold_profile'][2])]}
    result={name:{task:{arm:metrics(rr,task,arm) for arm in ('context','shuffle','prior')} for task in ('pos','joint','conditional')} for name,rr in subsets.items()}
    types=defaultdict(list)
    for r in rows:types[r['word']].append(r)
    macro={task:{arm:{metric:float(np.mean([metrics(rr,task,arm)[metric] for rr in types.values()])) for metric in ('nll','accuracy')} for arm in ('context','shuffle','prior')} for task in ('pos','joint','conditional')}
    # Cluster resampling is descriptive: these are reused development sentences.
    groups=defaultdict(list)
    for r in rows:groups[r['sid']].append(r)
    ids=sorted(groups);rng=np.random.default_rng(7401);boot={}
    for task in ('pos','conditional'):
        for control in ('prior','shuffle'):
            sums=np.array([sum(-math.log(max(EPS,r['predictions']['context'][task+'_probability']))+math.log(max(EPS,r['predictions'][control][task+'_probability'])) for r in groups[sid]) for sid in ids]);sizes=np.array([len(groups[sid]) for sid in ids]);draw=rng.integers(len(ids),size=(1000,len(ids)));d=sums[draw].sum(axis=1)/sizes[draw].sum(axis=1);boot[task+'/'+control]=dict(context_minus_control_nll=float(sums.sum()/sizes.sum()),descriptive_sentence_cluster_95_percentiles=np.quantile(d,[.025,.975]).tolist())
    passed=all(result['all'][task]['context']['nll']<result['all'][task][a]['nll'] for task in ('pos','conditional') for a in ('prior','shuffle'))
    return dict(subsets=result,word_type_macro=macro,types=len(types),sentences=len(ids),unsupported=sum(not r['supported'] for r in rows),descriptive_cluster_bootstrap=boot,both_tasks_beat_both_controls=passed,search_run=False,nuclei_measured=False)

def run():
    assert not OUT.exists();OUT.mkdir()
    for p,h in load(PREVIOUS/'verification-manifest.json')['inputs'].items():assert digest(p)==h,p
    paths=[Path(__file__),Path('benchmarks/grammar_normalized_readings_iteration73.py'),Path('benchmarks/grammar_pos_oracle_iteration72.py'),Path('benchmarks/grammar_role_compatibility_iteration70.py'),ROOT/'iteration70/model.json',ROOT/'iteration71/predictions.json',PREVIOUS/'verification-manifest.json',Path('experiments/holdouts/grammar-construction-next.json')]
    (OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='Direct prediction of reference POS and exactjointPOS/Case/Number from frozen70model on1273fixed contentpositions. No candidate scores or dictionary matches used. Arms frozen neighborcontext, savedshuffle and sourceprior. Marginalize roles. WithinPOS condition on goldPOS explicitly privileged. Report exactcategorical accuracy and NLL floored1e-12; zero/unsupported separately and supportedsubset, specifiedfeature subset, wordtype macro and1000sentencecluster bootstrap seed7401 descriptive only. No refits/tuning. Diagnostic condition bothPOS and conditionalmorph NLL beat bothcontrols; not recoverygate. Reserve and sealedtest unscored; previously reused labels only. Contentselection and correctsurrounding words remain supplied.'))
    model=load(ROOT/'iteration70/model.json');profiles,_=profile_space(model);rows=[]
    for r in load(ROOT/'iteration71/predictions.json'):
        g=r['gold_profile'];pred={arm:probability_record(model,p,g,profiles) for arm,p in [('context',posterior(model,r['context'])),('shuffle',posterior(model,r['shuffled_context'])),('prior',model['prior'])]}
        rows.append(dict(sid=r['sid'],index=r['index'],word=r['word'],gold_profile=g,supported=tuple(g) in profiles,predictions=pred))
    save(OUT/'predictions.json',rows);save(OUT/'prediction-freeze.json',dict(predictions=digest(OUT/'predictions.json')));result=evaluate(rows);save(OUT/'evaluation.json',result);print(json.dumps({k:v for k,v in result.items() if k!='word_type_macro'},indent=2))
if __name__=='__main__':run()
