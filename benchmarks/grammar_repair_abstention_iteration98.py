"""Source-only diverse/sparse corruption calibration, fixed classifier and PP models."""
from benchmarks.grammar_anchor_swap_bank_iteration97 import *
from voynich_smt.repair_abstention import pair_features,select,calibrate,evaluate as evaluate_cal
OUT=ROOT/'iteration98';EVAL=ROOT/'iteration97'

def calibration_bank(anchors,previous):
    bank={'correct':{}}
    for a in sorted(w for w,p in anchors.items() if p=='ADP'):
        for c in sorted(w for w,p in anchors.items() if p=='CCONJ'):bank['swap_'+a+'__'+c]={a:c,c:a}
    bank['same_adp']=previous['same_adp'];bank['same_conjunction']=previous['same_conjunction'];return bank

def reference_for(public,replacements,error,scores,words):
    lookup={t['anchor']:t['id'] for s in public for t in s['tokens'] if t['anchor'] in words};pair=sorted(lookup[w] for w in replacements) if error and all(w in lookup for w in replacements) else None
    return dict(error=error,pair=pair,supported=any(r['supported'] and r['pair']==pair for r in scores))

def run():
    assert not OUT.exists();OUT.mkdir();data=load(ROOT/'iteration44/annotations-truth.json');part=load(ROOT/'iteration49/manifest.json')['partitions']['0'];cat=load(ROOT/'iteration85/anchor-budgets.json');anchors=cat['195'];words=load(ROOT/'iteration93/types.json')['candidates'];models=load(ROOT/'iteration93/models.json');bank=calibration_bank(cat['20'],load(ROOT/'iteration93/patterns.json'));assert len(bank)==67
    ordered=sorted(part['calibration'],key=lambda sid:__import__('hashlib').sha256(('cal98|'+sid).encode()).hexdigest());blocks={'full':part['calibration']};blocks.update({'sparse'+str(i):ordered[100*i:100*(i+1)] for i in range(8)});assert all(len(v)==100 for k,v in blocks.items() if k!='full');save(OUT/'blocks.json',dict(scored=blocks,not_in_sparse=ordered[800:]));save(OUT/'calibration-bank.json',bank);(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),Path('src/voynich_smt/repair_abstention.py'),Path('src/voynich_smt/paired_anchor_class.py'),ROOT/'iteration44/annotations-truth.json',ROOT/'iteration49/manifest.json',ROOT/'iteration85/anchor-budgets.json',ROOT/'iteration93/models.json',ROOT/'iteration93/types.json',ROOT/'iteration95/policies.json',EVAL/'verification-manifest.json',BASE/'models.json',ROOT/'iteration89/models.json',OUT/'blocks.json',OUT/'calibration-bank.json']
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='Fixed93classifier/95jointpairedscore, support5occ3sentences unchanged. SOURCECAL829full+8disjoint100sentenceblockshashcal98SID,29remainderfullonly. ALL64crossswaps+3controls each=603calibrationcases. No targetlabels/caseoutcomes selectparameters. CalibratePRIMARYabsolute-gain andSECONDARYgain+runnerupgap(grid0,.1,.25,.5,1), allattainable nonnegativeCALtopgains+OFF. Unique top amongALLsupportedpairs; gapcomputedbeforethresholding. Asharedpolicy acrossfull/sparse requires empiricalexactpairprecision>=90%eachregime, >=10fullcalls/20pooledsparsecalls, ZEROclean/sameclassfalsecalls and ZEROwrongcallswhenreferencepartnerabsent/unsupported. Maxsummedhits,minwrong,prefergap0whenotherwiseequal,thenhighergain. Noqualifier=>OFF. These empiricalguards diagnosticnotformalguarantee. FreezeBOTHpoliciesbeforeloading97evaluationcases; compareoriginal95frozencut.61747. ClassifierandPPmodels unchanged; no target-picked support/parameters. Reuse97ALL186test/authorcases, selectednewrecommendations appliedblind evenwrong; fixed85PP.80/89PP.71and.80, reusepublic-signaturePPcacheorcomputeNEWview. No referencecorrectnessgate. Reuseddevelopmentdata; noreserve/sealedtest/newannotations.'))
    cases=[]
    for block,ids in blocks.items():
        dataset=OUT/block;dataset.mkdir();sentences=[dict(sent_id=sid,**data[sid]) for sid in ids];public=ag.public_sentences(sentences,anchors,'cal98-'+block);cache={}
        for j,(case,replacements) in enumerate(bank.items()):
            changed=perturb(public,replacements,anchors);sig=signature(changed)
            if sig not in cache:cache[sig]=pair_scores(changed,independent_records(changed,words,models),models)['joint_context']
            scores=cache[sig];path=dataset/(case+'.json');save(path,dict(scores=scores));save(dataset/(case+'.freeze.json'),dict(inputs={str(path):digest(path)}));ref=reference_for(public,replacements,case.startswith('swap_'),scores,words);cases.append(dict(block=block,case=case,regime='full' if block=='full' else 'sparse',features=pair_features(scores),reference=ref))
            if j%20==0:print('calibration',block,j+1,'/',len(bank),flush=True)
    save(OUT/'calibration-cases.json',cases);policies={}
    for arm,allow_gap in (('absolute',False),('margin',True)):
        chosen,curve=calibrate(cases,allow_gap);policies[arm]=chosen;save(OUT/('calibration-curve-'+arm+'.json'),curve);print('policy',arm,chosen,flush=True)
    old=load(ROOT/'iteration95/policies.json')['joint_context'];policies['frozen95']=dict(threshold=old['threshold'],gap=0.,qualified=True);save(OUT/'policies.json',policies);save(OUT/'policy-freeze.json',dict(inputs={str(p):digest(p) for p in [OUT/'policies.json',OUT/'calibration-cases.json']+list(OUT.glob('calibration-curve-*.json'))}));summary={}
    ppmodels={'original':load(BASE/'models.json'),'augmented':load(ROOT/'iteration89/models.json')}
    for name in ('source','Jerome','Caesar'):
        old_dataset=EVAL/name.lower();dataset=OUT/('eval-'+name.lower());dataset.mkdir();newstore=dataset/'new-pp-cache';newstore.mkdir();public=load(old_dataset/'public-clean.json');reference=load(old_dataset/'reference-rows.json');labels=[dict(sid=r['sid'],index=r['index'],labels=r['labels']) for r in reference];cache={}
        def get_scores(view):
            sig=signature(view)
            if sig not in cache:
                path=old_dataset/'pp-cache'/(sig+'.json')
                if path.exists():payload=load(path)
                else:
                    payload=dict(delta=delta_public(public,view),scores={a:compact(infer85(query_rows(view,labels),m)) for a,m in ppmodels.items()});path=newstore/(sig+'.json');save(path,payload);save(newstore/(sig+'.freeze.json'),dict(inputs={str(path):digest(path)}))
                cache[sig]=payload['scores']
            return sig,cache[sig]
        _,clean=get_scores(public)
        for case,replacements in load(EVAL/'bank.json').items():
            oldcase=old_dataset/case;actions=load(oldcase/'actions.json');detector=load(oldcase/'detector.json')['joint_context'];features=pair_features(detector);before_public=apply_delta(public,load(old_dataset/'pp-cache'/(actions['before']+'.json'))['delta']);before_sig,before=get_scores(before_public);result={};traces={}
            for arm,policy in policies.items():
                pair=select(features,policy['threshold'],policy['gap']);repaired=swap_assignments(before_public,pair);after_sig,after=get_scores(repaired);ref=actions['reference'];hit=pair is not None and ref['pair'] is not None and pair==ref['pair'];pair_eval=dict(hit=int(hit),wrong=int(pair is not None and not hit),abstain=pair is None,reference_present=ref['pair'] is not None,reference_supported=any(r['supported'] and r['pair']==ref['pair'] for r in detector));result[arm]=dict(pair=pair_eval,pp={a:{p:effect(expand(reference,after[a]),expand(reference,before[a]),expand(reference,clean[a]),cut) for p,cut in cuts.items()} for a,cuts in PP_SETTINGS.items()});traces[arm]=dict(pair=pair,after=after_sig)
            folder=dataset/case;folder.mkdir();save(folder/'actions.json',dict(features=features,before=before_sig,arms=traces));save(folder/'evaluation.json',result);summary[name+'/'+case]=result
        print('evaluated',name,flush=True)
    save(OUT/'evaluation.json',summary)
if __name__=='__main__':run()
