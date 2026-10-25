"""Source-only context-volume stability of held-type class probabilities."""
from benchmarks.grammar_balanced_training_iteration124 import *
OUT=ROOT/'iteration126'
SIZES=[100,200,400,800,1600,2471]
SEEDS=[12600,12601,12602]

def run():
    assert not OUT.exists();OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),ROOT/'iteration124/models.json',ROOT/'iteration124/calibrator.json',ROOT/'iteration124/oof-profiles.json',ROOT/'iteration124/verification-manifest.json',ROOT/'iteration116/type-split.json',ROOT/'iteration49/manifest.json',ROOT/'iteration44/annotations-truth.json',ROOT/'iteration85/anchor-budgets.json',ROOT/'iteration93/types.json',Path('experiments/holdouts/grammar-construction-next.json')]
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='SOURCE-ONLY volume diagnostic, no fitting/policy/author evaluation. Fixed124threeOOFmodels andbalancedoffset. Existing13trainingtypes eachpredictedonlybyfoldmodel excludingitsclasslabels andidentities; all16catalogue globallymasked/neverqueried/evaluated. Samefit2471wordonly projection, no newannotations/reserve/sealedlexicaltest. FixedSHAorders seeds12600/1/2 nested100/200/400/800/1600/full2471. Allpresent13types included, missing/support>=5occ3sent reportonly. Freeze views before profiles, predictions before labelmetrics. Currentoffset was fitted on these13full-context OOF profiles => calibration robustness diagnostic NOT independent validation. Raw/currentoffset/balancedprior, allpresent and pairedcommon-to-full metrics including AUC, drift, correct/wrong flips and cutcrossings. Full identical acrossseeds reportonce/neverpool asindependent. No newoffset fit, no targetthresholds. Primary ask whether smallercontexts shift absolute pooled probabilities versus full, retain perseed/class behavior; notcausal purevolume since composition alsochanges. No nextmodel chosen fromauthoranswers.'))
    part=load(ROOT/'iteration49/manifest.json')['partitions']['0'];ids=part['fit'];assert len(ids)==2471;reserved={r['sent_id'] for rr in load('experiments/holdouts/grammar-construction-next.json')['authors'].values() for r in rr};assert not set(ids)&reserved
    data=load(ROOT/'iteration44/annotations-truth.json');anchors=load(ROOT/'iteration85/anchor-budgets.json')['195'];fit=ag.public_sentences([dict(sent_id=i,tokens=[dict(word=t['word']) for t in data[i]['tokens']]) for i in ids],anchors,'fit116');byid={s['sent_id']:s for s in fit};lookup={t['anchor']:t['id'] for s in fit for t in s['tokens'] if t['anchor'] is not None};split=load(ROOT/'iteration116/type-split.json');train=split['training'];catalogue=load(ROOT/'iteration93/types.json')['candidates'];assert not set(train)&set(catalogue);models=load(ROOT/'iteration124/models.json');cal=load(ROOT/'iteration124/calibrator.json');selection={}
    for seed in SEEDS:
        order=sorted(ids,key=lambda sid:hashlib.sha256((str(seed)+'|'+sid).encode()).hexdigest())
        for n in SIZES:
            key='full' if n==len(ids) else str(seed)+'/'+str(n)
            if key not in selection:selection[key]=list(ids) if key=='full' else order[:n]
    save(OUT/'selection.json',selection);save(OUT/'selection-freeze.json',dict(inputs={str(OUT/'selection.json'):digest(OUT/'selection.json')}));profiles={};predictions={}
    for key,sids in selection.items():
        public=[byid[i] for i in sids];profiles[key]={}
        for fold in range(3):
            held=[w for w in train if split['oof_folds'][w]==fold];hidden={lookup[w] for w in catalogue+held};profiles[key].update(grouped_profile(public,held,lookup,hidden,models[str(fold)]))
        predictions[key]=[dict(type=w,n=p['n'],sentences=p['sentences'],supported=p['n']>=5 and p['sentences']>=3,probabilities=dict(raw=p['mean'],balanced124=float(apply_offset([p['mean']],cal)[0]),prior=.5)) for w,p in sorted(profiles[key].items())];print('predicted',key,len(predictions[key]),flush=True)
    save(OUT/'profiles.json',profiles);save(OUT/'predictions.json',predictions);save(OUT/'predictions-freeze.json',dict(inputs={str(OUT/name):digest(OUT/name) for name in ['profiles.json','predictions.json']}));details={k:[dict(r,**{'class':anchors[r['type']]}) for r in rows] for k,rows in predictions.items()};full={r['type']:r for r in details['full']};summary={};drift={}
    for key,rows in details.items():
        strata=dict(all=rows,supported=[r for r in rows if r['supported']],ADP=[r for r in rows if r['class']=='ADP'],CCONJ=[r for r in rows if r['class']=='CCONJ']);summary[key]=dict(sentences=len(selection[key]),missing_types=sorted(set(train)-{r['type'] for r in rows}),metrics={g:{a:metrics(rr,a) for a in ['raw','balanced124','prior']} for g,rr in strata.items()});common=[r['type'] for r in rows];transitions=[]
        for r in rows:
            w=r['type'];before=r['probabilities']['balanced124'];after=full[w]['probabilities']['balanced124'];transitions.append(dict(type=w,reference=r['class'],n=r['n'],full_n=full[w]['n'],probability=before,full_probability=after,delta_to_full=after-before,crossed_cutoff=(before>.5)!=(after>.5),correct_here=(before>.5)==(r['class']=='CCONJ'),correct_full=(after>.5)==(r['class']=='CCONJ')))
        drift[key]=dict(common_types=common,full_common_metrics={a:metrics([full[w] for w in common],a) for a in ['raw','balanced124','prior']},transitions=transitions,mean_absolute_probability_shift=float(np.mean([abs(r['delta_to_full']) for r in transitions])),cutoff_crossings=sum(r['crossed_cutoff'] for r in transitions),by_class={c:dict(n=sum(r['reference']==c for r in transitions),mean_delta_to_full=float(np.mean([r['delta_to_full'] for r in transitions if r['reference']==c])) if any(r['reference']==c for r in transitions) else None) for c in CLASSES})
    save(OUT/'reference-details.json',details);save(OUT/'summary.json',summary);save(OUT/'drift.json',drift)
    for key,v in summary.items():print('RESULT',key,v['metrics']['all']['balanced124'],drift[key]['mean_absolute_probability_shift'],drift[key]['cutoff_crossings'],flush=True)
if __name__=='__main__':run()
