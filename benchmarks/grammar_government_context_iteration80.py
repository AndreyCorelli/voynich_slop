"""Case eligibility using government/marker geometry and readable anchors."""
from benchmarks.grammar_direct_nominative_iteration79 import *
from voynich_smt.government_context import features as gf
from voynich_smt.factor_morphology import probabilities as morphology_probabilities
OUT=ROOT/'iteration80';PREVIOUS=ROOT/'iteration79'
ARMS=('local','baseline','baseline_shuffle','geometry','geometry_shuffle','anchors','anchors_shuffle','prior')

def dataset80(sentences,pm,lex,morph,seed):
    rows=dataset(sentences,pm,lex,seed);lookup={(r['sid'],r['index']):r for r in rows};rng=np.random.default_rng(seed);cache={}
    for s in sentences:
        ts=s['tokens'];words=[t['word'] for t in ts];pos=[candidate_pos(w,pm,lex.get(w,[]))[0] for w in words];finite=[]
        for w,p in zip(words,pos):
            if (w,p) not in cache:cache[w,p]=morphology_probabilities(morph,w,p,'role')[1] if p in ('VERB','AUX') else 0.
            finite.append(cache[w,p])
        order=rng.permutation(len(pos));sw=[words[j] for j in order];sp=[pos[j] for j in order];sf=[finite[j] for j in order]
        for i,t in enumerate(ts):
            if (s['sent_id'],i) not in lookup:continue
            r=lookup[s['sent_id'],i]
            for name,identity in [('geometry',False),('anchors',True)]:
                r[name+'_features']=gf(words,pos,finite,i,identity);r[name+'_shuffle_features']=gf(sw,sp,sf,i,identity)
    return rows

def infer80(rows,role,models):
    values={}
    for name in ('baseline','geometry','anchors'):
        normal='features' if name=='baseline' else name+'_features';shuffled='shuffle_features' if name=='baseline' else name+'_shuffle_features'
        values[name]=probability([r[normal] for r in rows],models[name]);values[name+'_shuffle']=probability([r[shuffled] for r in rows],models[name])
    result=[]
    for i,r in enumerate(rows):
        p=posterior(role,r['context']);sh=posterior(role,r['shuffle']);scores={'local':task_scores(role['labels'],p),'prior':task_scores(role['labels'],role['prior'])}
        for name,qs in values.items():scores[name]=dict(nominative=float(qs[i]),subject=task_scores(role['labels'],replace_nominal(role['labels'],sh if name.endswith('_shuffle') else p,qs[i]))['subject'])
        result.append(dict(sid=r['sid'],index=r['index'],word=r['word'],labels=r['labels'],scores=scores))
    return result

def run():
    assert not OUT.exists();OUT.mkdir()
    for p,h in load(PREVIOUS/'verification-manifest.json')['inputs'].items():assert digest(p)==h,p
    paths=[Path(__file__),Path('src/voynich_smt/government_context.py'),Path('src/voynich_smt/contextual_nominative.py'),Path('src/voynich_smt/factor_morphology.py'),Path('benchmarks/grammar_direct_nominative_iteration79.py'),ROOT/'iteration49/models.json',ROOT/'iteration79/model.json',ROOT/'iteration70/model.json',ROOT/'iteration71/word-pos-model.json',ROOT/'iteration49/manifest.json',ROOT/'iteration44/annotations-truth.json',ROOT/'iteration23/datasets.json',ROOT/'iteration1/morphology-lattice.json',ROOT/'iteration23/morphology-lattice.json',ROOT/'iteration71/predictions.json',PREVIOUS/'verification-manifest.json',Path('experiments/holdouts/grammar-construction-next.json')]
    (OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='Samefixedsource49fit/cal and1273targetcontentpositions. Frozen79directmodel baseline. Train2matchednominalNom binarylogistic models with79fixedmincount3/L2.001: geometry adds nearestADP,CCONJ/SCONJmarker, predictedfinitecarrier within8eachside, distance1/2/3-4/5-8, interveningnominal/marker counts capped2; finiteconfidence .5/.9 using frozen49expandedrole probability withcandidatePOS. Anchors adds readable identities of nearestpredictedADP/marker, nevercenter orcontentwordidentity. Allcenterword/POS/finitefeaturesmasked. Correctneighborcandidatewords/sentenceboundaries supplied; identities NOT establishedcipheranchors, explicitdiagnosticprivilege. Matchedshuffle permutes words/POS/finite tuples together withsame7001target/7701cal permutation; no targetgoldfeatures/links. Fit-onlylabels trainmodels; sourceonlycal F1/precision90samegrid/support. No targetselection. EvaluateNom andsofttransferredsubject withlocal/baseline/shuffle/prior controls. No refits ofupstreammodels, no reserve/sealedtest/newannotations/search.'))
    role=load(ROOT/'iteration70/model.json');pm=load(ROOT/'iteration71/word-pos-model.json');lex=load(ROOT/'iteration23/morphology-lattice.json');lex.update(load(ROOT/'iteration1/morphology-lattice.json'));morph=load(ROOT/'iteration49/models.json')['0']['expanded']['model'];data=load(ROOT/'iteration44/annotations-truth.json');part=load(ROOT/'iteration49/manifest.json')['partitions']['0']
    fits=dataset80([dict(sent_id=sid,**data[sid]) for sid in part['fit']],pm,lex,morph,7901);models={'baseline':load(ROOT/'iteration79/model.json')}
    for name in ('geometry','anchors'):models[name]=nfit([r[name+'_features'] for r in fits],[r['labels']['nominative'] for r in fits])
    save(OUT/'models.json',models);save(OUT/'model-freeze.json',dict(models=digest(OUT/'models.json')))
    calqueries=dataset80([dict(sent_id=sid,**data[sid]) for sid in part['calibration']],pm,lex,morph,7701);cal=infer80(calqueries,role,models);save(OUT/'calibration-predictions.json',cal);policies={task:{a:select_policy(cal,task,a) for a in ARMS} for task in ('subject','nominative')};save(OUT/'policies.json',policies);save(OUT/'calibration-freeze.json',dict(inputs={str(p):digest(p) for p in (OUT/'calibration-predictions.json',OUT/'policies.json')}))
    ann={(r['sid'],r['index']):r for r in load(ROOT/'iteration71/predictions.json')};target=[]
    for s in load(ROOT/'iteration23/datasets.json')['test_caesar']:
        ts=[]
        for i,w in enumerate(s['tokens']):
            r=ann.get((s['sent_id'],i));ts.append(dict(word=w,pos=r['gold_profile'][0] if r else 'X',features=dict(Case=r['gold_profile'][1],Number=r['gold_profile'][2]) if r else {},rel=r['role'] if r else '?'))
        target.append(dict(sent_id=s['sent_id'],tokens=ts))
    rows=infer80(dataset80(target,pm,lex,morph,7001),role,models);assert len(rows)==1273;save(OUT/'predictions.json',rows);save(OUT/'prediction-freeze.json',dict(predictions=digest(OUT/'predictions.json')));result=evaluation(rows,policies);save(OUT/'evaluation.json',result);print(json.dumps(result,indent=2))
if __name__=='__main__':run()
