"""Frozen balanced-training model transfer on exactly the cached119 author contexts."""
from benchmarks.grammar_class_validation_iteration118 import *
OUT=ROOT/'iteration125'
INPUTS={'Jerome':{'base':ROOT/'iteration112/public-base.json','expanded':ROOT/'iteration112/public-expanded.json'},'Caesar':{'base':ROOT/'iteration107/public-base.json','expanded':ROOT/'iteration107/public-expanded.json'}}


def run():
    assert not OUT.exists();OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),ROOT/'iteration124/models.json',ROOT/'iteration116/type-split.json',ROOT/'iteration124/calibrator.json',ROOT/'iteration124/verification-manifest.json',ROOT/'iteration119/predictions.json',ROOT/'iteration118/verification-manifest.json',ROOT/'iteration112/context-selection.json',ROOT/'iteration107/initial-changes.json',ROOT/'iteration93/types.json',ROOT/'iteration85/anchor-budgets.json',Path('experiments/holdouts/grammar-construction-next.json')]+[p for vv in INPUTS.values() for p in vv.values()]
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='Frozen125 transfer of124balanced-loss model+13OOFbalancedoffset, exact119cachedJerome/Caesar base and expanded. No model/calibrator/threshold refit; all16cataloguetypes excluded from training and globally masked; supplied otheranchors/cataloguemembership remain. Primary expanded allpresent type accuracy/NLL/AUC vs119previous and balancedprior; report100views, support5occ3sent onlysecondary, allclass strata, common-type volume transitions. Predictions frozen before references/metrics. Same reuseddevelopment authors, no newannotations/PP/repair/reserve/sealedlexicaltest/defaultchange or nucleusclaim. Preserve transferable grammatical input independently of hardPP integration failure124.'))
    words=load(ROOT/'iteration93/types.json')['candidates'];anchors=load(ROOT/'iteration85/anchor-budgets.json')['195'];split=load(ROOT/'iteration116/type-split.json');assert not set(words)&set(split['training']);model=load(ROOT/'iteration124/models.json')['final'];calibrator=load(ROOT/'iteration124/calibrator.json');previous=load(ROOT/'iteration119/predictions.json');reserved={r['sent_id'] for rr in load('experiments/holdouts/grammar-construction-next.json')['authors'].values() for r in rr};selection={};predictions={};profiles={}
    for author,paths in INPUTS.items():
        publics={v:load(p) for v,p in paths.items()};assert len(publics['base'])==100 and publics['expanded'][:100]==publics['base'];lookup={}
        for public in publics.values():
            assert not {s['sent_id'] for s in public}&reserved
            for s in public:
                for t in s['tokens']:
                    if t['anchor'] in words:
                        w=t['anchor'];assert t['tag']==anchors[w];assert w not in lookup or lookup[w]==t['id'];lookup[w]=t['id']
        hidden=set(lookup.values());selection[author]=dict(lookup=lookup,views={v:dict(sentences=len(p),tokens=sum(len(s['tokens']) for s in p),sids=[s['sent_id'] for s in p]) for v,p in publics.items()})
        for v,public in publics.items():
            key=author+'/'+v;profiles[key]=grouped_profile(public,sorted(lookup),lookup,hidden,model);rows=[]
            for w,r in profiles[key].items():
                raw=r['mean'];rows.append(dict(type=w,opaque=lookup[w],n=r['n'],sentences=r['sentences'],supported=r['n']>=5 and r['sentences']>=3,probabilities=dict(raw=raw,balanced124=float(apply_offset([raw],calibrator)[0]),previous=next(z['probabilities']['balanced13'] for z in previous[key]['rows'] if z['type']==w),prior13=3/13,balanced_prior=.5)))
            predictions[key]=dict(rows=rows,missing_types=sorted(set(words)-set(profiles[key])),sentences=len(public),tokens=sum(len(s['tokens']) for s in public))
    save(OUT/'selection.json',selection);save(OUT/'profiles.json',profiles);save(OUT/'predictions.json',predictions);save(OUT/'predictions-freeze.json',dict(inputs={str(p):digest(p) for p in [OUT/'selection.json',OUT/'profiles.json',OUT/'predictions.json']}))
    summary={};details={};volume={}
    for view,p in predictions.items():
        rows=[dict(r,**{'class':anchors[r['type']]}) for r in p['rows']];details[view]=rows;strata={'all':rows,'supported':[r for r in rows if r['supported']],'unsupported':[r for r in rows if not r['supported']],'ADP':[r for r in rows if r['class']=='ADP'],'CCONJ':[r for r in rows if r['class']=='CCONJ'],'earlier_calibration8':[r for r in rows if r['type'] in split['calibration']],'earlier_evaluation8':[r for r in rows if r['type'] in split['evaluation']]};summary[view]=dict(sentences=p['sentences'],tokens=p['tokens'],missing_types=p['missing_types'],metrics={g:{a:metrics(rr,a) for a in ['raw','balanced124','previous','prior13','balanced_prior']} for g,rr in strata.items()})
    for author in INPUTS:
        before={r['type']:r for r in details[author+'/base']};after={r['type']:r for r in details[author+'/expanded']};common=sorted(set(before)&set(after));new=sorted(set(after)-set(before));volume[author]=dict(common_types=common,new_types=new,lost_types=sorted(set(before)-set(after)),common_metrics={a:{phase:metrics([rows[w] for w in common],a) for phase,rows in [('before',before),('after',after)]} for a in ['raw','balanced124','previous','prior13','balanced_prior']},transitions={})
        for a in ['raw','balanced124','previous']:
            correct=lambda r:(r['probabilities'][a]>.5)==(r['class']=='CCONJ');volume[author]['transitions'][a]=dict(gained=[w for w in common if not correct(before[w]) and correct(after[w])],lost=[w for w in common if correct(before[w]) and not correct(after[w])],new_correct=[w for w in new if correct(after[w])],new_wrong=[w for w in new if not correct(after[w])])
    save(OUT/'reference-details.json',details);save(OUT/'summary.json',summary);save(OUT/'volume-comparison.json',volume);print(json.dumps(summary,indent=2),flush=True);print('VOLUME',volume,flush=True)
if __name__=='__main__':run()
