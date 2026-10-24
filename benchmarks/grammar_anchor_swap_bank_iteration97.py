"""All59 unused candidate swaps; frozen pair detector and downstream PP policies."""
from benchmarks.grammar_anchor_shadow_pp_iteration96 import *
from voynich_smt.anchor_swap_bank import remaining_bank
from voynich_smt.paired_anchor_class import target_features
OUT=ROOT/'iteration97'

def signature(public):
    values=sorted({(t['id'],t['anchor'],t['tag']) for s in public for t in s['tokens']})
    return __import__('hashlib').sha256(json.dumps(values,separators=(',',':')).encode()).hexdigest()

def delta_public(base,changed):
    return {t['id']:[t['anchor'],t['tag']] for s,z in zip(base,changed) for b,t in zip(s['tokens'],z['tokens']) if b!=t}

def apply_delta(base,delta):
    return [dict(s,tokens=[dict(t,anchor=delta[t['id']][0],tag=delta[t['id']][1]) if t['id'] in delta else dict(t) for t in s['tokens']]) for s in base]

def compact(rows):
    return dict(pooled_pos=[r['scores']['pooled_pos']['pp'] for r in rows],left=[r['scores']['left']['pp'] for r in rows],prior=rows[0]['scores']['prior']['pp'])

def expand(reference,scores):
    return [dict(r,scores={'pooled_pos':{'pp':scores['pooled_pos'][i]},'left':{'pp':scores['left'][i]},'prior':{'pp':scores['prior']}}) for i,r in enumerate(reference)]

def independent_records(public,words,models):
    candidates={t['id']:t['tag'] for s in public for t in s['tokens'] if t['anchor'] in words and t['tag'] in BINARY_CLASSES};records=[]
    for opaque,proposed in candidates.items():
        rows=target_features(public,{opaque});q=ag.predict([r['features'] for r in rows],models['context']).mean(axis=0).tolist();margin,mass=disagreement(q,list(BINARY_CLASSES),proposed);sentences=len({r['sid'] for r in rows});records.append(dict(anchor_id=opaque,proposed=proposed,n=len(rows),sentences=sentences,disagreement=margin,supported=len(rows)>=5 and sentences>=3))
    return records

def run():
    assert not OUT.exists();OUT.mkdir();data=load(ROOT/'iteration44/annotations-truth.json');part=load(ROOT/'iteration49/manifest.json')['partitions']['0'];source=lambda split:[dict(sent_id=sid,**data[sid]) for sid in part[split]];cat=load(ROOT/'iteration85/anchor-budgets.json');anchors=cat['195'];previous=load(ROOT/'iteration93/patterns.json');bank=remaining_bank(cat['20'],previous);assert len(bank)==62;assert sum(k.startswith('swap_') for k in bank)==59;save(OUT/'bank.json',bank);(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),Path('src/voynich_smt/anchor_swap_bank.py'),Path('src/voynich_smt/paired_anchor_class.py'),Path('src/voynich_smt/anchor_shadow_repair.py'),ROOT/'iteration44/annotations-truth.json',ROOT/'iteration49/manifest.json',ROOT/'iteration85/anchor-budgets.json',ROOT/'iteration93/models.json',ROOT/'iteration93/types.json',ROOT/'iteration93/patterns.json',ROOT/'iteration95/policies.json',ROOT/'iteration96/verification-manifest.json',BASE/'models.json',BASE/'policies.json',ROOT/'iteration89/models.json',ROOT/'iteration89/policies.json',CACHE,DECLARATION,OUT/'bank.json']
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='ALL59remainingADPxCCONJpairs amongsame16sourcefitcommon20candidates (8x8minus5previouscrosspairs), pluscorrect/sameADP/sameCCONJcontrols=62perdataset,186total. SamecachedsourceTEST/Jerome100/Caesar100, nofilters/targetpairselection. Fixed93classifiers,95ALL6pairpolicies, support5occ3sentences,tieabstention. Recomputeblindallpairjoint/independent/prior/permutation scores ineachcorruptedinput, referenceattachedAFTERrecommendations. EVERYrecommendedswap appliedregardlesscorrectness. Fixed85originalPP.80,89augPP.71and.80, nearestF1control; nofit/recalibration/thresholdselection. PPpublicsignaturecache withinDATASET only (samepositions/equalitygroups), savecompactscorearrays+reconstructibledeltas+predictionfreezes. Reportpairhits/wrongrecommendations/abstentions/absentunsupportedendpoints/zeroaffectedcases, ALLPPnewTP,newFP,lostTP,removedFPversuscorrupted andclean. Noformalindependenceguarantee, singlebijectiveclassswapdevelopmentonly, priordatasetsreused though59pairsspecificsnew. No newannotations/reserve/sealedtest/nucleussearch.'))
    classmodels=load(ROOT/'iteration93/models.json');ppmodels={'original':load(BASE/'models.json'),'augmented':load(ROOT/'iteration89/models.json')};policies=load(ROOT/'iteration95/policies.json');words=load(ROOT/'iteration93/types.json')['candidates'];oldpol=load(BASE/'policies.json');cache=load(CACHE);decl=load(DECLARATION)['split_ids'];datasets={'source':source('test')};datasets.update({a:cached_sentences(cache,decl[a]) for a in AUTHORS});summary={}
    for name,sentences in datasets.items():
        dataset=OUT/name.lower();dataset.mkdir();store=dataset/'pp-cache';store.mkdir();public,labels=transfer_rows(sentences,anchors,'bank97-'+name,ppmodels['original']['pos_classes']);save(dataset/'public-clean.json',public);clean_original=infer85(query_rows(public,labels),ppmodels['original']);reference=[{k:r[k] for k in ('sid','index','word','visible','labels')} for r in clean_original];save(dataset/'reference-rows.json',reference);cached={}
        def pp_scores(view):
            sig=signature(view)
            if sig not in cached:
                scores={a:compact(infer85(query_rows(view,labels),model)) for a,model in ppmodels.items()};payload=dict(delta=delta_public(public,view),scores=scores);path=store/(sig+'.json');save(path,payload);save(store/(sig+'.freeze.json'),dict(inputs={str(path):digest(path)}));cached[sig]=scores
            return sig,cached[sig]
        _,clean=pp_scores(public);lookup={t['anchor']:t['id'] for s in public for t in s['tokens'] if t['anchor'] in words}
        for j,(case,replacements) in enumerate(bank.items()):
            folder=dataset/case;folder.mkdir();corrupted=perturb(public,replacements,anchors);records=independent_records(corrupted,words,classmodels);scores=pair_scores(corrupted,records,classmodels);save(folder/'detector.json',scores);save(folder/'detector-freeze.json',dict(inputs={str(folder/'detector.json'):digest(folder/'detector.json')}));selected={arm:recommend(scores[arm],float('inf') if policy['threshold'] is None else policy['threshold']) for arm,policy in policies.items()};before_sig,before=pp_scores(corrupted);result={};after_signatures={}
            # The reference is attached after both recommendation and public action selection.
            ref=dict(error=case.startswith('swap_'),pair=sorted(lookup[w] for w in replacements) if case.startswith('swap_') and all(w in lookup for w in replacements) else None)
            for arm,pair in selected.items():
                repaired=swap_assignments(corrupted,pair);after_sig,after=pp_scores(repaired);after_signatures[arm]=after_sig;pair_eval=pair_metrics(scores[arm],float('inf') if policies[arm]['threshold'] is None else policies[arm]['threshold'],ref);result[arm]=dict(pair=pair_eval,pp={a:{p:effect(expand(reference,after[a]),expand(reference,before[a]),expand(reference,clean[a]),cut) for p,cut in cuts.items()} for a,cuts in PP_SETTINGS.items()},nearest_f1=counts(expand(reference,after['original']),'pp','left',oldpol['left']['standard']['f1']['threshold']))
            info=dict(before=before_sig,after=after_signatures,selected=selected,reference=ref,affected_tokens=sum(x!=y for s,t in zip(public,corrupted) for x,y in zip(s['tokens'],t['tokens'])));save(folder/'actions.json',info);save(folder/'evaluation.json',result);summary[name+'/'+case]=result
            if j%10==0:print('completed',name,j+1,'/',len(bank),'uniquePPinputs',len(cached),flush=True)
    save(OUT/'evaluation.json',summary)
if __name__=='__main__':run()
