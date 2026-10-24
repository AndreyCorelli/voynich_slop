"""Remove supplied POS and nominal cohort from source PP prediction."""
from benchmarks.grammar_learned_government_iteration82 import *
from voynich_smt.government_context import features as government_features
from voynich_smt.coarse_government import probe,fit_probe,structure_label,fold
OUT=ROOT/'iteration83';PREVIOUS=ROOT/'iteration82'
ARMS=('masked_center','predicted_pos','left','either','prior')

def rows83(sentences,pm,lex,morph):
    result=[];cache={}
    for s in sentences:
        ts=s['tokens'];words=[t['word'] for t in ts];pos=[candidate_pos(w,pm,lex.get(w,[]))[0] for w in words];finite=[]
        for w,p in zip(words,pos):
            if (w,p) not in cache:cache[w,p]=morphology_probabilities(morph,w,p,'role')[1] if p in ('VERB','AUX') else 0.
            finite.append(cache[w,p])
        for i,t in enumerate(ts):
            pp,full=bundles(ts,pos,i);features=government_features(words,pos,finite,i,True);cohort=t['pos'] in ('NOUN','PROPN','ADJ') and t['features'].get('Case') in CASES
            result.append(dict(sid=s['sent_id'],index=i,word=t['word'],gold_pos=t['pos'],matched=cohort,structure_gold=structure_label(dict(pp_bundle=pp,structure_bundle=full)),masked_center=features,predicted_pos=features+['predictedCenterPOS:'+coarse(pos[i])]))
    return result

def proximity83(r,side):
    values=[]
    for s in (('left',) if side=='left' else ('left','right')):
        for f in r['masked_center']:
            prefix=s+':adp:distance='
            if f.startswith(prefix):values.append({'1':1.,'2':.5,'3-4':1/3,'5-8':.2}[f[len(prefix):]])
    return max(values,default=0.)

def infer83(rows,models,prior):
    probs={a:np.mean([probe([r[a] for r in rows],m) for m in mm.values()],axis=0) for a,mm in models.items()}
    return [dict(sid=r['sid'],index=r['index'],word=r['word'],gold_pos=r['gold_pos'],labels={'pp':r['structure_gold']>=4},structure_gold=r['structure_gold'],scores={a:{'pp':float(probs[a][i,4:].sum()) if a in probs else float(prior) if a=='prior' else proximity83(r,a)} for a in ARMS}) for i,r in enumerate(rows)]

def evaluate83(rows,pol):
    return {a:dict(f1_policy=counts(rows,'pp',a,p['f1']['threshold']),precision90_policy=counts(rows,'pp',a,p['precision90']['threshold']) if p['precision90'] else None) for a,p in pol.items()}

def run():
    assert not OUT.exists();OUT.mkdir()
    for p,h in load(PREVIOUS/'verification-manifest.json')['inputs'].items():assert digest(p)==h,p
    paths=[Path(__file__),Path('src/voynich_smt/coarse_government.py'),Path('src/voynich_smt/government_context.py'),Path('src/voynich_smt/government_oracle.py'),ROOT/'iteration82/models.json',ROOT/'iteration82/predictions.json',ROOT/'iteration82/pp-policy.json',ROOT/'iteration49/models.json',ROOT/'iteration71/word-pos-model.json',ROOT/'iteration49/manifest.json',ROOT/'iteration44/annotations-truth.json',ROOT/'iteration1/morphology-lattice.json',ROOT/'iteration23/morphology-lattice.json',PREVIOUS/'verification-manifest.json',Path('experiments/holdouts/grammar-construction-next.json')]
    (OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='Sourceonlysame49split. A matched81/82nominalatomicCasecohort, refit3foldensemble8classPP/headprobes WITHOUT suppliedcenterPOS, models maskedcenter versus inferredcenterPOS(frozen71candidatewordPOS). B train/evaluateALLstoredtokens, nopos/case/cohortfilter. Label forEVERYtoken: PPgovernednode iff owncase-linkedADP or inheritanceamod/conj/flat/fixed as81; no arbitraryPOS restriction. ADPmarkers themselves and arbitraryPPsubtree descendants notautomaticallypositive; notfullspanorattachmenttask. Samebaselinefeatures government/finite/readablemarkeridentities; no goldPOS/heads/rels/features ininference. Source3foldshaSIDsplit identical82, no downstreamCasefit. No hyperparamtuning. Nearestleft/either controls andsourcefitPPprior percohort. Separate sourcecalF1/precision90samegrid/support perarm; freeze beforetest. Report alltokenFPsbygoldPOS metadata only, authors, lexicalinputprivilege. Fixed82oraclePOS arm onlymatchedreference, no directcomparison acrosschangedcohorts. No Caesar/newtargetqueries/reserve/sealedtest/search.'))
    pm=load(ROOT/'iteration71/word-pos-model.json');lex=load(ROOT/'iteration23/morphology-lattice.json');lex.update(load(ROOT/'iteration1/morphology-lattice.json'));morph=load(ROOT/'iteration49/models.json')['0']['expanded']['model'];data=load(ROOT/'iteration44/annotations-truth.json');part=load(ROOT/'iteration49/manifest.json')['partitions']['0']
    fitrows=rows83([dict(sent_id=sid,**data[sid]) for sid in part['fit']],pm,lex,morph);calrows=rows83([dict(sent_id=sid,**data[sid]) for sid in part['calibration']],pm,lex,morph)
    models={};provenance={};priors={}
    for cohort in ('matched','all_tokens'):
        rr=[r for r in fitrows if r['matched']] if cohort=='matched' else fitrows;models[cohort]={};provenance[cohort]={};priors[cohort]=(sum(r['structure_gold']>=4 for r in rr)+.5)/(len(rr)+1)
        for arm in ('masked_center','predicted_pos'):
            models[cohort][arm]={};provenance[cohort][arm]={}
            for f in range(3):
                train=[r for r in rr if fold(r['sid'])!=f];models[cohort][arm][str(f)]=fit_probe([r[arm] for r in train],[r['structure_gold'] for r in train]);provenance[cohort][arm][str(f)]=dict(training_sids=sorted({r['sid'] for r in train}),train_n=len(train))
        print('Fitted',cohort,len(rr),flush=True)
    save(OUT/'models.json',dict(models=models,priors=priors));save(OUT/'provenance.json',provenance);save(OUT/'model-freeze.json',dict(inputs={str(p):digest(p) for p in (OUT/'models.json',OUT/'provenance.json')}))
    policies={}
    for cohort in ('matched','all_tokens'):
        rr=[r for r in calrows if r['matched']] if cohort=='matched' else calrows;pred=infer83(rr,models[cohort],priors[cohort]);save(OUT/(cohort+'-calibration.json'),pred);policies[cohort]={a:select_policy(pred,'pp',a) for a in ARMS}
    save(OUT/'policies.json',policies);save(OUT/'calibration-freeze.json',dict(inputs={str(p):digest(p) for p in (OUT/'policies.json',OUT/'matched-calibration.json',OUT/'all_tokens-calibration.json')}))
    testrows=rows83([dict(sent_id=sid,**data[sid]) for sid in part['test']],pm,lex,morph);result={}
    for cohort in ('matched','all_tokens'):
        rr=[r for r in testrows if r['matched']] if cohort=='matched' else testrows;pred=infer83(rr,models[cohort],priors[cohort]);save(OUT/(cohort+'-predictions.json'),pred);result[cohort]=evaluate83(pred,policies[cohort])
    save(OUT/'prediction-freeze.json',dict(inputs={str(p):digest(p) for p in (OUT/'matched-predictions.json',OUT/'all_tokens-predictions.json')}));save(OUT/'evaluation.json',result);print(json.dumps(result,indent=2))
if __name__=='__main__':run()
