"""Source-calibrated subject/nominal eligibility from pooled soft POS."""
from voynich_smt.pooled_grammar import pos_mass,replace_pos,pooled_marginal,task_scores,counts,select_policy
from benchmarks.grammar_role_compatibility_iteration70 import *
from voynich_smt.grammar_lexical_bridge import candidate_pos
OUT=ROOT/'iteration77';PREVIOUS=ROOT/'iteration76'
ARMS=('local','pooled','other_occurrences','shuffle_local','shuffle_pooled','prior')

def predict_split(sentences,model,pm,lex,seed):
    labels=model['labels'];rng=np.random.default_rng(seed);raw=[]
    for s in sentences:
        tt=s['tokens'];pp=[candidate_pos(t['word'],pm,lex.get(t['word'],[]))[0] for t in tt];shuffled=list(rng.permutation(pp))
        for i,t in enumerate(tt):raw.append(dict(sid=s['sent_id'],index=i,word=t['word'],token=t,local=posterior(model,context(pp,i)),shuffle=posterior(model,context(shuffled,i))))
    groups=defaultdict(list)
    for i,r in enumerate(raw):groups[r['word']].append(i)
    marg=[pos_mass(labels,r['local']) for r in raw];smarg=[pos_mass(labels,r['shuffle']) for r in raw];result=[]
    for i,r in enumerate(raw):
        t=r['token']
        if t['pos'] not in CONTENT:continue # Evaluation cohort only; pooling used every position.
        indices=groups[r['word']];pool=pooled_marginal(marg,indices);other=pooled_marginal(marg,indices,i);spool=pooled_marginal(smarg,indices)
        arms=dict(local=r['local'],pooled=replace_pos(labels,r['local'],pool),other_occurrences=replace_pos(labels,r['local'],other) if other is not None else r['local'],shuffle_local=r['shuffle'],shuffle_pooled=replace_pos(labels,r['shuffle'],spool),prior=model['prior'])
        result.append(dict(sid=r['sid'],index=r['index'],word=r['word'],occurrences=len(indices),labels=dict(subject=t['rel'].split(':')[0]=='nsubj',nominative=t['pos'] in ('NOUN','PROPN','ADJ') and t['features'].get('Case')=='Nom'),scores={a:task_scores(labels,p) for a,p in arms.items()}))
    return result

def evaluate(rows,policies):
    result={}
    for cohort,rr in [('all',rows),('repeated',[r for r in rows if r['occurrences']>=2])]:
        result[cohort]={}
        for task in ('subject','nominative'):
            result[cohort][task]={}
            for arm in ARMS:
                p=policies[task][arm];r=dict(brier=float(np.mean([(x['scores'][arm][task]-x['labels'][task])**2 for x in rr])),f1_policy=counts(rr,task,arm,p['f1']['threshold']),precision90_policy=counts(rr,task,arm,p['precision90']['threshold']) if p['precision90'] is not None else None)
                result[cohort][task][arm]=r
    return result

def run():
    assert not OUT.exists();OUT.mkdir()
    for p,h in load(PREVIOUS/'verification-manifest.json')['inputs'].items():assert digest(p)==h,p
    paths=[Path(__file__),Path('src/voynich_smt/pooled_grammar.py'),Path('benchmarks/grammar_role_compatibility_iteration70.py'),ROOT/'iteration70/model.json',ROOT/'iteration71/word-pos-model.json',ROOT/'iteration49/manifest.json',ROOT/'iteration44/annotations-truth.json',ROOT/'iteration23/datasets.json',ROOT/'iteration1/morphology-lattice.json',ROOT/'iteration23/morphology-lattice.json',ROOT/'iteration71/predictions.json',PREVIOUS/'verification-manifest.json',Path('experiments/holdouts/grammar-construction-next.json')]
    (OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='Grammarrestoration is standaloneobjective. Frozen70jointrole/profilemodel and71wordPOSmodel. Replace localPOSmarginal with arithmeticmean across all occurrences of wordtype while preserving local(role,Case,Number|POS). Alltoken occurrences used for pooling, including functionpositions; goldCONTENT selects evaluationonly. Prior, local, pooled, leavecurrentout(otherfallbacklocal forsingletons), shuffledlocal/pooled controls. Source49fold0calibration only selects perarm/task threshold maximizingF1 ongrid0..1 step.01 (tieshigherthreshold); secondaryprecision90requires20predictions10types, choosemaxTP thenprecisionthenhigherthreshold; absent ifnone. Target same100declaredCaesar sentences, rolelabels saved71+profiles; no newtargetgrammarqueries. Primary nsubjrole onallcontentpositions; secondary morphologicalnominal eligibility NOUN/PROPN/ADJ+Nom, not actualsubjectidentity. Report all/repeated, confusionF1/Brier and precision90support. No goldPOS passed toinference. Perfect surroundingplaintext/sentenceboundaries/content evaluationcohort stillprivileged. Seed7701cal and7001target(matches70). No refits, reserve or sealedtest scoring. No defaultadoption fromreused results.'))
    model=load(ROOT/'iteration70/model.json');pm=load(ROOT/'iteration71/word-pos-model.json');lex=load(ROOT/'iteration23/morphology-lattice.json');lex.update(load(ROOT/'iteration1/morphology-lattice.json'));data=load(ROOT/'iteration44/annotations-truth.json');ids=load(ROOT/'iteration49/manifest.json')['partitions']['0']['calibration'];source=[dict(sent_id=sid,**data[sid]) for sid in ids];assert all(s['author']!='Caesar' for s in source)
    cal=predict_split(source,model,pm,lex,7701);save(OUT/'calibration-predictions.json',cal);policies={task:{arm:select_policy(cal,task,arm) for arm in ARMS} for task in ('subject','nominative')};save(OUT/'policies.json',policies);save(OUT/'calibration-freeze.json',dict(inputs={str(p):digest(p) for p in (OUT/'calibration-predictions.json',OUT/'policies.json')}))
    # Gold content annotations already saved in71; restore evaluation fields only.
    annotations={(r['sid'],r['index']):r for r in load(ROOT/'iteration71/predictions.json')};target=[]
    for s in load(ROOT/'iteration23/datasets.json')['test_caesar']:
        tt=[]
        for i,w in enumerate(s['tokens']):
            r=annotations.get((s['sent_id'],i));tt.append(dict(word=w,pos=r['gold_profile'][0] if r else 'X',features=dict(Case=r['gold_profile'][1],Number=r['gold_profile'][2]) if r else {},rel=r['role'] if r else '?'))
        target.append(dict(sent_id=s['sent_id'],tokens=tt))
    rows=predict_split(target,model,pm,lex,7001);assert len(rows)==1273;save(OUT/'predictions.json',rows);save(OUT/'prediction-freeze.json',dict(predictions=digest(OUT/'predictions.json')));result=evaluate(rows,policies);save(OUT/'evaluation.json',result);print(json.dumps(result,indent=2))
if __name__=='__main__':run()
