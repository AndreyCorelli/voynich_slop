"""Frozen13-type class model and balanced scalar calibration on cached source test."""
from benchmarks.grammar_monotone_calibration_iteration117 import *
OUT=ROOT/'iteration118'


def metrics(rows,arm):
    if not rows:return dict(n=0,accuracy=None,nll=None,brier=None,auc=None,token_weighted_accuracy=None)
    p=[r['probabilities'][arm] for r in rows];y=[r['class']=='CCONJ' for r in rows];pred=[q>.5 for q in p];pos=[q for q,v in zip(p,y) if v];neg=[q for q,v in zip(p,y) if not v];n=sum(r['n'] for r in rows)
    return dict(n=len(rows),correct=sum(a==b for a,b in zip(pred,y)),accuracy=sum(a==b for a,b in zip(pred,y))/len(rows),nll=-sum(math.log(max(1e-12,q if v else 1-q)) for q,v in zip(p,y))/len(rows),brier=sum((q-v)**2 for q,v in zip(p,y))/len(rows),auc=sum((a>b)+.5*(a==b) for a in pos for b in neg)/(len(pos)*len(neg)) if pos and neg else None,token_weighted_accuracy=sum(r['n']*(a==b) for r,a,b in zip(rows,pred,y))/n,predicted_conjunctions=sum(pred),confusion=dict(ADP_as_ADP=sum(not v and not a for a,v in zip(pred,y)),ADP_as_CCONJ=sum(not v and a for a,v in zip(pred,y)),CCONJ_as_ADP=sum(v and not a for a,v in zip(pred,y)),CCONJ_as_CCONJ=sum(v and a for a,v in zip(pred,y))))


def run():
    assert not OUT.exists();OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),ROOT/'iteration116/verification-manifest.json',ROOT/'iteration116/class-models.json',ROOT/'iteration116/type-split.json',ROOT/'iteration117/verification-manifest.json',ROOT/'iteration117/models.json',ROOT/'iteration49/manifest.json',ROOT/'iteration44/annotations-truth.json',ROOT/'iteration93/types.json',ROOT/'iteration85/anchor-budgets.json',Path('experiments/holdouts/grammar-construction-next.json')]
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='SOURCE-TEST frozenvalidation of116final13noncatalogtypeclassmodel+117balanced13singleintercept1.4074229894692558. No fit/calibration/thresholdselection/veto/pair/PPinference. ONLYwordforms ofexisting44cached49partition0test770sentences; author/sourceSIDmetadataallowed. Verifydisjointfit/cal/reserve BEFOREprojectingtestwords. ALL16cataloguetypes classlabelsheldoutofnewmodelandintercepttraining. All16maskedglobally(namesNone/tagX); opaqueIDsgroupoccurrences only,195otheranchorlookupunchanged. PrimaryFULL770 allpresent16type-macroclassaccuracy/NLL; unsupported>=5occ3sent flagONLYreporting, neverdropprimarytypes. Perclass/allpresent/supported/116cal8-vs-eval8subsets; missingtypesexplicit. SecondaryEACHmetadataauthorblock regardlessvolume, noauthorselection; type-heldoutlabels constant suppliedsourceMAPreference, NOTnewtokenPOSannotations. FixedqCC>.5 tiesADP; compare raw,balanced13,13typeclassprior3/13 ANDbalancedprior.5; NLL/Brier/AUC/tokenweightedclassaccuracydescriptive. Frozenallchoicesbeforetestprofiles/predictions; words andmodels alreadyexist, source-test previouslyusedbyotherexperiments=>notnewcorpus/universalconfirmation. BinaryADP/CCONJconditionalinference only, notlexicalnuclei/fullgrammar/cleanPPcoverage/anchorlearning orrepairclaim. No reservefeatures/newannotations/sealedlexicaltest/authorholdoutdata.'))
    part=load(ROOT/'iteration49/manifest.json')['partitions']['0'];ids=part['test'];reserved={r['sent_id'] for rr in load('experiments/holdouts/grammar-construction-next.json')['authors'].values() for r in rr};assert len(ids)==770 and not set(ids)&(set(part['fit'])|set(part['calibration'])|reserved)
    # Existing cached annotations are not consumed by inference: project FORM only.
    cache=load(ROOT/'iteration44/annotations-truth.json');sentences=[dict(sent_id=i,author=cache[i]['author'],tokens=[dict(word=t['word']) for t in cache[i]['tokens']]) for i in ids];anchors=load(ROOT/'iteration85/anchor-budgets.json')['195'];words=load(ROOT/'iteration93/types.json')['candidates'];split=load(ROOT/'iteration116/type-split.json');assert not set(words)&set(split['training']);model=load(ROOT/'iteration116/class-models.json')['final'];calibrator=load(ROOT/'iteration117/models.json')['balanced13'];assert calibrator['n']==13
    public=ag.public_sentences(sentences,anchors,'class118');lookup={w:hashlib.sha256(('class118|'+w).encode()).hexdigest() for w in words};hidden=set(lookup.values());byid={s['sent_id']:s for s in public};views={'full':public};views.update({'author-'+a:[byid[s['sent_id']] for s in sentences if s['author']==a] for a in sorted({s['author'] for s in sentences})})
    save(OUT/'input-words.json',sentences);save(OUT/'public.json',public);save(OUT/'selection.json',dict(ids=ids,views={v:[s['sent_id'] for s in p] for v,p in views.items()},types=words));save(OUT/'context-freeze.json',dict(inputs={str(p):digest(p) for p in [OUT/'input-words.json',OUT/'public.json',OUT/'selection.json']}))
    predictions={};profiles={}
    for view,pub in views.items():
        profiles[view]=grouped_profile(pub,words,lookup,hidden,model);rows=[]
        for w,r in profiles[view].items():
            raw=r['mean'];balanced=float(apply_offset([raw],calibrator)[0]);rows.append(dict(type=w,opaque=lookup[w],n=r['n'],sentences=r['sentences'],supported=r['n']>=5 and r['sentences']>=3,probabilities=dict(raw=raw,balanced13=balanced,prior13=3/13,balanced_prior=.5)))
        predictions[view]=dict(rows=rows,missing_types=sorted(set(words)-set(profiles[view])),sentences=len(pub),tokens=sum(len(s['tokens']) for s in pub))
    save(OUT/'profiles.json',profiles);save(OUT/'predictions.json',predictions);save(OUT/'predictions-freeze.json',dict(inputs={str(p):digest(p) for p in [OUT/'profiles.json',OUT/'predictions.json']}))
    # Attach reference classes only after all predictions are frozen.
    summary={};details={}
    for view,p in predictions.items():
        rows=[dict(r,**{'class':anchors[r['type']]}) for r in p['rows']];details[view]=rows;strata={'all':rows,'supported':[r for r in rows if r['supported']],'unsupported':[r for r in rows if not r['supported']],'ADP':[r for r in rows if r['class']=='ADP'],'CCONJ':[r for r in rows if r['class']=='CCONJ'],'earlier_calibration8':[r for r in rows if r['type'] in split['calibration']],'earlier_evaluation8':[r for r in rows if r['type'] in split['evaluation']]};summary[view]=dict(sentences=p['sentences'],tokens=p['tokens'],missing_types=p['missing_types'],metrics={g:{a:metrics(rr,a) for a in ['raw','balanced13','prior13','balanced_prior']} for g,rr in strata.items()})
    save(OUT/'reference-details.json',details);save(OUT/'summary.json',summary);print(json.dumps(summary,indent=2),flush=True)
if __name__=='__main__':run()
