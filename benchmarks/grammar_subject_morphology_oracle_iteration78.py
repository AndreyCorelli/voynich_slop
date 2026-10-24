"""Condition frozen role prediction on privileged POS or full morphology."""
from benchmarks.grammar_pooled_eligibility_iteration77 import *
OUT=ROOT/'iteration78';PREVIOUS=ROOT/'iteration77'
ARMS=('local','oracle_pos_context','oracle_profile_context','oracle_pos_shuffle','oracle_profile_shuffle','oracle_pos_prior','oracle_profile_prior')

def conditional_subject(model,p,g,full):
    admitted=[i for i,(_,a) in enumerate(model['labels']) if (list(a)==list(g) if full else a[0]==g[0])]
    z=sum(p[i] for i in admitted)
    return float(sum(p[i] for i in admitted if model['labels'][i][0]=='nsubj')/z) if z else 0.,bool(z)

def predictions(sentences,model,pm,lex,seed):
    rng=np.random.default_rng(seed);rows=[]
    for s in sentences:
        ts=s['tokens'];pp=[candidate_pos(t['word'],pm,lex.get(t['word'],[]))[0] for t in ts];sp=list(rng.permutation(pp))
        for i,t in enumerate(ts):
            if t['pos'] not in CONTENT:continue
            g=profile(t);p=posterior(model,context(pp,i));sh=posterior(model,context(sp,i));scores={'local':{'subject':task_scores(model['labels'],p)['subject']}};support={}
            for name,q in [('context',p),('shuffle',sh),('prior',model['prior'])]:
                for full,kind in [(False,'pos'),(True,'profile')]:
                    value,ok=conditional_subject(model,q,g,full);arm='oracle_'+kind+'_'+name;scores[arm]={'subject':value};support[arm]=ok
            rows.append(dict(sid=s['sent_id'],index=i,word=t['word'],gold_profile=g,labels={'subject':t['rel'].split(':')[0]=='nsubj'},scores=scores,support=support))
    return rows

def evaluation(rows,policies):
    result={}
    for arm in ARMS:
        vals=[r['scores'][arm]['subject'] for r in rows];ys=[r['labels']['subject'] for r in rows];p=policies[arm]
        result[arm]=dict(brier=float(np.mean([(a-y)**2 for a,y in zip(vals,ys)])),binary_nll=float(np.mean([-math.log(max(1e-12,a if y else 1-a)) for a,y in zip(vals,ys)])),f1_policy=counts(rows,'subject',arm,p['f1']['threshold']),precision90_policy=counts(rows,'subject',arm,p['precision90']['threshold']) if p['precision90'] else None,unsupported=sum(not r['support'].get(arm,True) for r in rows))
    return result

def run():
    assert not OUT.exists();OUT.mkdir()
    for p,h in load(PREVIOUS/'verification-manifest.json')['inputs'].items():assert digest(p)==h,p
    paths=[Path(__file__),Path('benchmarks/grammar_pooled_eligibility_iteration77.py'),Path('benchmarks/grammar_role_compatibility_iteration70.py'),Path('src/voynich_smt/pooled_grammar.py'),ROOT/'iteration70/model.json',ROOT/'iteration71/word-pos-model.json',ROOT/'iteration49/manifest.json',ROOT/'iteration44/annotations-truth.json',ROOT/'iteration23/datasets.json',ROOT/'iteration1/morphology-lattice.json',ROOT/'iteration23/morphology-lattice.json',ROOT/'iteration71/predictions.json',PREVIOUS/'verification-manifest.json',Path('experiments/holdouts/grammar-construction-next.json')]
    (OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='Frozen70role/profilemodel, same source49fold0calibration and1273contenttargets/100Caesar sentences. ReferencePOS or exactjointPOS/Case/Number supplied by zeroing incompatible labels and normalizing. Exactempty fields are categories, not wildcard; unsupported zero and reportcount. No goldrole enters probabilities. Context/shuffle/prior eachconditioned on sameoracle. Local77replay. Source-only perarmF1 and precision90policies withsame77grid/support20predictions10types; freeze beforetarget. Report confusionF1/precisionrecall, Brier andbinaryNLL. Oracle informationdiagnostic only, not deployable restoration and not absoluteceiling of allpossiblemodels. No refits/reserve/sealedtest/newtargetannotations/search.'))
    m=load(ROOT/'iteration70/model.json');pm=load(ROOT/'iteration71/word-pos-model.json');lex=load(ROOT/'iteration23/morphology-lattice.json');lex.update(load(ROOT/'iteration1/morphology-lattice.json'));data=load(ROOT/'iteration44/annotations-truth.json');ids=load(ROOT/'iteration49/manifest.json')['partitions']['0']['calibration'];source=[dict(sent_id=sid,**data[sid]) for sid in ids]
    cal=predictions(source,m,pm,lex,7701);save(OUT/'calibration-predictions.json',cal);policies={a:select_policy(cal,'subject',a) for a in ARMS};save(OUT/'policies.json',policies);save(OUT/'calibration-freeze.json',dict(inputs={str(p):digest(p) for p in (OUT/'calibration-predictions.json',OUT/'policies.json')}))
    ann={(r['sid'],r['index']):r for r in load(ROOT/'iteration71/predictions.json')};target=[]
    for s in load(ROOT/'iteration23/datasets.json')['test_caesar']:
        ts=[]
        for i,w in enumerate(s['tokens']):
            r=ann.get((s['sent_id'],i));ts.append(dict(word=w,pos=r['gold_profile'][0] if r else 'X',features=dict(Case=r['gold_profile'][1],Number=r['gold_profile'][2]) if r else {},rel=r['role'] if r else '?'))
        target.append(dict(sent_id=s['sent_id'],tokens=ts))
    rows=predictions(target,m,pm,lex,7001);assert len(rows)==1273;save(OUT/'predictions.json',rows);save(OUT/'prediction-freeze.json',dict(predictions=digest(OUT/'predictions.json')));result=evaluation(rows,policies);save(OUT/'evaluation.json',result);print(json.dumps(result,indent=2))
if __name__=='__main__':run()
