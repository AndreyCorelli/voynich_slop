"""Occurrence floor two versus five with shared-frame support unchanged."""
from benchmarks.grammar_case_frames_iteration166 import *
from itertools import combinations
OUT=ROOT/'iteration167';FLOORS=[2,5]

def descriptors_for(ids,floor):
    counts=Counter(ids);eligible={w for w,n in counts.items() if n>=floor};frames={}
    for j in range(1,len(ids)-1):
        if ids[j] in eligible:frames.setdefault((ids[j-1],ids[j+1]),{}).setdefault(ids[j],[]).append(j)
    pairs={}
    for frame,ww in frames.items():
        for a,b in combinations(sorted(ww),2):pairs.setdefault((a,b),[]).append(dict(frame=list(frame),a_positions=ww[a],b_positions=ww[b]))
    return [dict(a=a,b=b,shared_frames=len(ff),frames=sorted(ff,key=lambda r:r['frame'])) for (a,b),ff in sorted(pairs.items())],len(eligible)

def run():
    assert not OUT.exists();OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),ROOT/'iteration166/verification-manifest.json',ROOT/'iteration166/case-inputs.json',ROOT/'iteration166/summary.json',ROOT/'iteration164/streams.json',ROOT/'iteration164/transforms.json',ROOT/'iteration165/descriptors.json']
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='ONLYoccurrencefloorchange:2vs5, same4originalstreams/16shuffleindices/recognizedcases/scoreweighting166. Twoisthelogicalminimum for2distinctframes. Primary>=2distinctsharedframes unchanged, secondary>=1 remainsallreported. ALLeligibletypes/noPOS/purity/catalogueinputs; floorsfixednocutoffsearch. Freezeallframe/occurrence descriptorsBEFOREcaseinputs/scoring, allscoresBEFOREaggregatecase/nullmetrics. Compareperauthor/floor support/coverage/applicability/casemacroagreement/pooled/conflictfree, exactfloor5replay166. Decomposefloor2primaryinto oldpairs(bothcounts>=5) vs newpairs(atleastonecount2..4), explicitnewonlymetrics no selectingcasesbylabel. Same recognizedcaseinventory andconditionalcoverage caveat, missingneveragreement. No newannotations/reserve/sealedworks/fitting/namedcases/nuclei/deploymentclaim. Allauthor/floor resultsretained no favorableselection.'))
    streams=load(ROOT/'iteration164/streams.json');transforms=load(ROOT/'iteration164/transforms.json');descriptors={};eligibility={}
    for author,seq in streams.items():
        descriptors[author]={};eligibility[author]={}
        for floor in FLOORS:
            key=str(floor);descriptors[author][key]={};eligibility[author][key]=sum(n>=floor for n in Counter(seq).values())
            for view,ix in transforms[author].items():
                ids=seq if ix is None else [seq[k] for k in ix];dd,n=descriptors_for(ids,floor);assert n==eligibility[author][key];descriptors[author][key][view]=dd
    save(OUT/'descriptors.json',descriptors);save(OUT/'eligibility.json',eligibility);save(OUT/'descriptors-freeze.json',dict(inputs={str(OUT/n):digest(OUT/n) for n in ['descriptors.json','eligibility.json']}));case_inputs=load(ROOT/'iteration166/case-inputs.json');details={}
    for author,ff in descriptors.items():
        details[author]={}
        for floor,vv in ff.items():
            details[author][floor]={}
            for view,dd in vv.items():
                ix=transforms[author][view];cases=case_inputs[author] if ix is None else [case_inputs[author][k] for k in ix];details[author][floor][view]=score_cases(dd,cases)
    save(OUT/'details.json',details);save(OUT/'scores-freeze.json',dict(inputs={str(OUT/'details.json'):digest(OUT/'details.json')}));summary={a:{floor:{view:summarize_cases(dd,eligibility[a][floor]) for view,dd in vv.items()} for floor,vv in ff.items()} for a,ff in details.items()};contrasts={};increment={}
    for author,ff in summary.items():
        contrasts[author]={};counts=Counter(streams[author]);increment[author]={}
        for view,rr in details[author]['2'].items():
            increment[author][view]={group:summarize_cases([r for r in rr if (counts[r['a']]>=5 and counts[r['b']]>=5)==(group=='old')],eligibility[author]['2']) for group in ['old','new']}
        for floor,vv in ff.items():
            contrasts[author][floor]={}
            for threshold in ['1','2']:
                actual=vv['original'][threshold];pp=[vv['word'+str(k)][threshold]['edge_macro_frame_case_agreement'] for k in SEEDS if vv['word'+str(k)][threshold]['case_edges']];value=actual['edge_macro_frame_case_agreement'];contrasts[author][floor][threshold]=dict(actual=actual,null_with_case=len(pp),null_mean=float(np.mean(pp)) if pp else None,null_max=max(pp) if pp else None,null_at_least_actual=sum(p>=value for p in pp) if value is not None else None)
        print(author,{f:vv['2'] for f,vv in contrasts[author].items()},'NEW',increment[author]['original']['new']['2'],flush=True)
    assert {a:ff['5'] for a,ff in summary.items()}==load(ROOT/'iteration166/summary.json');save(OUT/'summary.json',summary);save(OUT/'contrasts.json',contrasts);save(OUT/'incremental.json',increment)
if __name__=='__main__':run()
