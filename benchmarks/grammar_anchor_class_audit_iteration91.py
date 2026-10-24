"""Independently audit anchor classes by hiding each type throughout a split."""
from benchmarks.grammar_anchor_challenge_iteration90 import *
from voynich_smt.anchor_class_audit import disagreement,flagged,metrics,choose_threshold
OUT=ROOT/'iteration91'

def class_records(public, candidates,models):
    records=[];classes=models['pos_classes'];flat=[(s['sent_id'],t) for s in public for t in s['tokens']]
    for opaque_id,proposed in candidates.items():
        hidden=[dict(s,tokens=[dict(t,anchor=None,tag='X') if t['id']==opaque_id else dict(t) for t in s['tokens']]) for s in public]
        rows=[r for r in ag.public_features(hidden) if r['word']==opaque_id];n=len(rows)
        q=np.mean([ag.predict([r['features'] for r in rows],m) for m in models['pos'].values()],axis=0).mean(axis=0) if n else np.zeros(len(classes));margin,mass=disagreement(q.tolist(),classes,proposed);sentences=len({r['sid'] for r in rows})
        records.append(dict(anchor_id=opaque_id,proposed=proposed,n=n,sentences=sentences,mean=q.tolist(),disagreement=margin,class_mass=mass,supported=n>=5 and sentences>=3 and mass>=.05))
    return records

def prepare_audit(sentences,anchors,candidate_words,replacements,salt,models):
    public=ag.public_sentences(sentences,anchors,salt);changed=perturb(public,replacements,anchors);lookup={t['anchor']:t['id'] for s in public for t in s['tokens'] if t['anchor'] in candidate_words};candidates={lookup[w]:anchors[replacements.get(w,w)] for w in candidate_words if w in lookup};records=class_records(changed,candidates,models)
    # Simulation labels are assigned AFTER computing public-only class evidence.
    inverse={opaque:w for w,opaque in lookup.items()}
    for r in records:r['class_wrong']=r['proposed']!=anchors[inverse[r['anchor_id']]]
    return records,{opaque:w for w,opaque in lookup.items()}

def run():
    assert not OUT.exists();OUT.mkdir()
    data=load(ROOT/'iteration44/annotations-truth.json');part=load(ROOT/'iteration49/manifest.json')['partitions']['0'];source=lambda split:[dict(sent_id=sid,**data[sid]) for sid in part[split]];catalogue=load(ROOT/'iteration85/anchor-budgets.json');anchors=catalogue['195'];candidates=sorted(w for w,p in catalogue['20'].items() if p in ('ADP','CCONJ'));patterns=load(ROOT/'iteration90/patterns.json');models=load(BASE/'models.json');save(OUT/'patterns.json',patterns);save(OUT/'candidate-words.json',candidates)
    (OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),Path('src/voynich_smt/anchor_class_audit.py'),Path('src/voynich_smt/anchor_grammar.py'),Path('src/voynich_smt/anchor_perturbation.py'),ROOT/'iteration44/annotations-truth.json',ROOT/'iteration49/manifest.json',ROOT/'iteration85/anchor-budgets.json',BASE/'models.json',ROOT/'iteration90/verification-manifest.json',CACHE,DECLARATION,OUT/'patterns.json',OUT/'candidate-words.json']
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='Independent anchor-class detection only, NO PP integration. Candidate types common20 withsourceMAPADP/CCONJ, presenttypesallreported. For each candidate trueopaqueID hide allitsoccurrences frompublic anchors/tags and predictcontextPOS withfrozen85ensemble, NO anchoroverride. Mean acrossoccurrences then log(oppositeclassmass/proposedclassmass) epsilon1e-12. Support>=5occurrences,3sentences,ADP+CCONJmeanmass>=.05. Thresholdgrid0,.5,1,2,3,4,8,OFF. Calibrate ONLYsourcecal correct and rehearsedin/et scenarios; requireclean<=1falseflag andflaggedoccurrences<=5%candidateoccurrences; maximizeknownswapTP,thenmincorruptedFP,cleanflaggedtokens,higherthreshold. OFFavailable; if0TP no detectionclaim. Freeze policy beforeevaluating sourcetest,cachedJerome/Caesar all8patterns90. Sameclassswaps areclasscorrect negatives evenwhenlexicallywrong. Errorreference isoriginalsourceMAPclass under simulatedmapping, nottargettokenPOS; labelsassignedAFTERpublicscores. No targetprivateannotationsusedbydetector, no newtraining/rawqueries/reserve/sealedtest. No targetpickedthresholds. Reportunsupportederrors, falsealarms,errorflagsandtokenweights, classdistributions; no correction or recoverednucleusclaim.'))
    cal={}
    for pattern in ('correct','rehearsed_in_et'):
        rows,identities=prepare_audit(source('calibration'),anchors,candidates,patterns[pattern],'cal91',models);save(OUT/('calibration-'+pattern+'.json'),dict(records=rows,identities=identities));cal[pattern]=rows
    chosen,curve=choose_threshold(cal['correct'],cal['rehearsed_in_et']);save(OUT/'calibration-curve.json',curve);save(OUT/'policy.json',chosen);save(OUT/'policy-freeze.json',dict(inputs={str(p):digest(p) for p in [OUT/'policy.json',OUT/'calibration-curve.json']+list(OUT.glob('calibration-*.json'))}));print('calibration',chosen,flush=True)
    threshold=float('inf') if chosen['threshold'] is None else chosen['threshold'];cache=load(CACHE);decl=load(DECLARATION)['split_ids'];datasets={'source':source('test')};datasets.update({a:cached_sentences(cache,decl[a]) for a in AUTHORS});summary={}
    for name,sentences in datasets.items():
        for pattern,replacements in patterns.items():
            folder=OUT/(name.lower()+'-'+pattern);folder.mkdir();rows,identities=prepare_audit(sentences,anchors,candidates,replacements,'eval91-'+name,models);save(folder/'predictions.json',dict(records=rows,identities=identities));save(folder/'prediction-freeze.json',dict(inputs={str(folder/'predictions.json'):digest(folder/'predictions.json')}));result=metrics(rows,threshold);save(folder/'evaluation.json',result);summary[name+'/'+pattern]=result
        print('evaluated',name,flush=True)
    save(OUT/'evaluation.json',summary)
if __name__=='__main__':run()
