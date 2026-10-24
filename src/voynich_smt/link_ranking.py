"""Observable one-cue link ranking, with explicit ties and no gold inference."""
CUES=('verbal','subordinator','coordinator')
WEIGHTS=(0.,.5,1.,2.,4.,8.,16.)


def features(tokens,subject,predicate):
    between=tokens[min(subject,predicate)+1:max(subject,predicate)]
    return dict(distance=abs(subject-predicate),verbal=sum(t['pos'] in ('VERB','AUX') for t in between),subordinator=sum(t['pos']=='SCONJ' for t in between),coordinator=sum(t['pos']=='CCONJ' for t in between))


def best(pairs,observations,cue=None,weight=0.):
    if not pairs:return []
    scores={tuple(p): -observations[tuple(p)]['distance']-weight*observations[tuple(p)].get(cue,0) for p in pairs}
    maximum=max(scores.values())
    return sorted(p for p,score in scores.items() if score==maximum)


def anchored_utility(rows,cue,weight):
    total=0.;n=0
    for r in rows:
        s,v=r['reference'];pairs=r['pairs'];obs=r['observations'];valid=set(map(tuple,r['valid']))
        for index,anchor in ((0,s),(1,v)):
            winners=best([p for p in pairs if p[index]==anchor],obs,cue,weight)
            total+=sum(p in valid for p in winners)/len(winners) if winners else 0.
            n+=1
    return total/n if n else 0.


def select(fit_rows,calibration_rows):
    # Pick one cue using fit only, then its weight on the disjoint calibration set.
    # Fixed iteration order breaks ties conservatively: baseline then smaller weights.
    candidates=[(None,0.)]+[(cue,w) for cue in CUES for w in WEIGHTS[1:]]
    fit_scores=[anchored_utility(fit_rows,cue,w) for cue,w in candidates]
    chosen=max(range(len(candidates)),key=lambda i:fit_scores[i]);cue=candidates[chosen][0]
    weights=WEIGHTS if cue is not None else (0.,)
    calibration_scores=[anchored_utility(calibration_rows,cue,w) for w in weights]
    weight=weights[max(range(len(weights)),key=lambda i:calibration_scores[i])]
    return dict(cue=cue,weight=weight,fit_scores=[dict(cue=c,weight=w,utility=u) for (c,w),u in zip(candidates,fit_scores)],calibration_scores=[dict(weight=w,utility=u) for w,u in zip(weights,calibration_scores)])
