"""Matched Case/Number oracles and a source-trained direct nominative model."""
from benchmarks.grammar_pooled_eligibility_iteration77 import *
from voynich_smt.contextual_nominative import features as nf,fit as nfit,probability,replace_nominal
OUT=ROOT/'iteration79';PREVIOUS=ROOT/'iteration78'

def oracle_subject(model,p,g,field):
    admitted=[i for i,(_,a) in enumerate(model['labels']) if a[0]==g[0] and (field=='pos' or a[1 if field=='case' else 2]==g[1 if field=='case' else 2])];z=sum(p[i] for i in admitted)
    return float(sum(p[i] for i in admitted if model['labels'][i][0]=='nsubj')/z) if z else 0.

def dataset(sentences,pm,lex,seed):
    rng=np.random.default_rng(seed);result=[]
    for s in sentences:
        ts=s['tokens'];pp=[candidate_pos(t['word'],pm,lex.get(t['word'],[]))[0] for t in ts];sp=list(rng.permutation(pp))
        for i,t in enumerate(ts):
            if t['pos'] in CONTENT:result.append(dict(sid=s['sent_id'],index=i,word=t['word'],g=profile(t),labels=dict(subject=t['rel'].split(':')[0]=='nsubj',nominative=t['pos'] in ('NOUN','PROPN','ADJ') and t['features'].get('Case')=='Nom'),context=context(pp,i),shuffle=context(sp,i),features=nf(pp,i),shuffle_features=nf(sp,i)))
    return result

def infer(rows,model,direct):
    pp=probability([r['features'] for r in rows],direct);ss=probability([r['shuffle_features'] for r in rows],direct);result=[]
    for r,q,sq in zip(rows,pp,ss):
        p=posterior(model,r['context']);sh=posterior(model,r['shuffle']);scores={'local':task_scores(model['labels'],p),'shuffle':task_scores(model['labels'],sh),'prior':task_scores(model['labels'],model['prior'])}
        scores['direct']=dict(nominative=float(q),subject=task_scores(model['labels'],replace_nominal(model['labels'],p,q))['subject']);scores['direct_shuffle']=dict(nominative=float(sq),subject=task_scores(model['labels'],replace_nominal(model['labels'],sh,sq))['subject'])
        for field in ('pos','case','number'):
            for name,v in [('context',p),('shuffle',sh),('prior',model['prior'])]:scores['oracle_'+field+'_'+name]={'subject':oracle_subject(model,v,r['g'],field)}
        result.append(dict(sid=r['sid'],index=r['index'],word=r['word'],gold_profile=r['g'],labels=r['labels'],scores=scores))
    return result

def evaluation(rows,policies):
    result={}
    for task,arms in policies.items():
        result[task]={}
        for arm,pol in arms.items():
            ys=[r['labels'][task] for r in rows];ps=[r['scores'][arm][task] for r in rows];result[task][arm]=dict(f1_policy=counts(rows,task,arm,pol['f1']['threshold']),precision90_policy=counts(rows,task,arm,pol['precision90']['threshold']) if pol['precision90'] else None,brier=float(np.mean([(p-y)**2 for p,y in zip(ps,ys)])),nll=float(np.mean([-math.log(max(1e-12,p if y else 1-p)) for p,y in zip(ps,ys)])))
    return result

def run():
    assert not OUT.exists();OUT.mkdir()
    for p,h in load(PREVIOUS/'verification-manifest.json')['inputs'].items():assert digest(p)==h,p
    paths=[Path(__file__),Path('src/voynich_smt/contextual_nominative.py'),Path('src/voynich_smt/dependency_role_proxy.py'),Path('src/voynich_smt/pooled_grammar.py'),Path('benchmarks/grammar_pooled_eligibility_iteration77.py'),ROOT/'iteration70/model.json',ROOT/'iteration71/word-pos-model.json',ROOT/'iteration49/manifest.json',ROOT/'iteration44/annotations-truth.json',ROOT/'iteration23/datasets.json',ROOT/'iteration1/morphology-lattice.json',ROOT/'iteration23/morphology-lattice.json',ROOT/'iteration71/predictions.json',PREVIOUS/'verification-manifest.json',Path('experiments/holdouts/grammar-construction-next.json')]
    (OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='Bothphases run regardless of results. A: frozen70rolemodel, oraclePOS versus POS+Case versus POS+Number; exactemptyfeaturecategory, conditionalrole ongivenfields; matching context/shuffle/prior. Fullprofile78retained as frozenreference, not reselected. B: direct binary logistic nominalnominative predictor (NOUN/PROPN/ADJ+annotatedNom) trained only49fold0fit contentpositions; maskedcenter neighborPOS +/-2 plusflankpair, no centerword/POS/suffix or goldfeatures. Candidate-derivedneighborPOS frozen71model. minfeaturecount3, L2=.001, no tuning. DirectNomprobability softreweights frozen70nominalNom vsothergroups, preserves conditionalroles; reportnominative andsubject separately vs local/shuffle/prior. Source49calibration F1/precision90same77grid/support; models thenpolicies frozen beforetarget. Same1273contenttargets andknownsurroundingplaintext; no fullsubjectattachment claim. Exactannotationlabel absences countednonNom, no labeldropping. Seeds7701cal7001target, fitseed7901 irrelevanttofeaturecounts. No reserve/sealedtest/newtargetgrammarqueries/search.'))
    model=load(ROOT/'iteration70/model.json');pm=load(ROOT/'iteration71/word-pos-model.json');lex=load(ROOT/'iteration23/morphology-lattice.json');lex.update(load(ROOT/'iteration1/morphology-lattice.json'));data=load(ROOT/'iteration44/annotations-truth.json');parts=load(ROOT/'iteration49/manifest.json')['partitions']['0']
    fitrows=dataset([dict(sent_id=sid,**data[sid]) for sid in parts['fit']],pm,lex,7901);direct=nfit([r['features'] for r in fitrows],[r['labels']['nominative'] for r in fitrows]);save(OUT/'model.json',direct);save(OUT/'model-freeze.json',dict(model=digest(OUT/'model.json')))
    calrows=dataset([dict(sent_id=sid,**data[sid]) for sid in parts['calibration']],pm,lex,7701);cal=infer(calrows,model,direct);save(OUT/'calibration-predictions.json',cal);arms={task:[a for a in cal[0]['scores'] if task in cal[0]['scores'][a]] for task in ('subject','nominative')};pol={task:{a:select_policy(cal,task,a) for a in aa} for task,aa in arms.items()};save(OUT/'policies.json',pol);save(OUT/'calibration-freeze.json',dict(inputs={str(p):digest(p) for p in (OUT/'calibration-predictions.json',OUT/'policies.json')}))
    ann={(r['sid'],r['index']):r for r in load(ROOT/'iteration71/predictions.json')};target=[]
    for s in load(ROOT/'iteration23/datasets.json')['test_caesar']:
        ts=[]
        for i,w in enumerate(s['tokens']):
            r=ann.get((s['sent_id'],i));ts.append(dict(word=w,pos=r['gold_profile'][0] if r else 'X',features=dict(Case=r['gold_profile'][1],Number=r['gold_profile'][2]) if r else {},rel=r['role'] if r else '?'))
        target.append(dict(sent_id=s['sent_id'],tokens=ts))
    rows=infer(dataset(target,pm,lex,7001),model,direct);assert len(rows)==1273;save(OUT/'predictions.json',rows);save(OUT/'prediction-freeze.json',dict(predictions=digest(OUT/'predictions.json')));result=evaluation(rows,pol);save(OUT/'evaluation.json',result);print(json.dumps(result,indent=2))
if __name__=='__main__':run()
