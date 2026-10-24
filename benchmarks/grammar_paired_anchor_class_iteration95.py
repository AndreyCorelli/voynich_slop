"""Blind paired class-consistency challenge, fixed93 classifier and source calibration."""
from benchmarks.grammar_fixed_anchor_detector_iteration93 import *
from voynich_smt.paired_anchor_class import pair_scores,pair_metrics,calibrate_pair,ARMS as PAIR_ARMS
OUT=ROOT/'iteration95';PREVIOUS=ROOT/'iteration93'

def prepare95(sentences,anchors,words,replacements,salt,models,independent):
    public=ag.public_sentences(sentences,anchors,salt);lookup={t['anchor']:t['id'] for s in public for t in s['tokens'] if t['anchor'] in words};changed=perturb(public,replacements,anchors)
    # Independent scores rekeyed by publicly associated occurrence identity for comparison.
    records=[]
    for r in independent['records']['context']:
        word=independent['identities'][r['anchor_id']];records.append(dict(r,anchor_id=lookup[word]))
    scores=pair_scores(changed,records,models)
    error=bool(replacements) and len({anchors[w] for w in replacements})>1
    reference=dict(error=error,pair=sorted(lookup[w] for w in replacements) if error and all(w in lookup for w in replacements) else None)
    return dict(scores=scores,reference=reference,identities={v:k for k,v in lookup.items()})

def run():
    assert not OUT.exists();OUT.mkdir();data=load(ROOT/'iteration44/annotations-truth.json');part=load(ROOT/'iteration49/manifest.json')['partitions']['0'];source=lambda split:[dict(sent_id=sid,**data[sid]) for sid in part[split]];anchors=load(ROOT/'iteration85/anchor-budgets.json')['195'];words=load(PREVIOUS/'types.json')['candidates'];models=load(PREVIOUS/'models.json');patterns=load(PREVIOUS/'patterns.json');(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text());paths=[Path(__file__),Path('src/voynich_smt/paired_anchor_class.py'),ROOT/'iteration44/annotations-truth.json',ROOT/'iteration49/manifest.json',ROOT/'iteration85/anchor-budgets.json',PREVIOUS/'models.json',PREVIOUS/'types.json',PREVIOUS/'patterns.json',ROOT/'iteration94/verification-manifest.json',CACHE,DECLARATION]+list(PREVIOUS.glob('calibration-*.json'))+list(PREVIOUS.glob('*/predictions.json'))
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='EnumerateALLpresentproposedADPxCCONJpairs among16commoncandidates, no referencepairorclasses inpairscorer. JOINTprimary:hideBOTHtypes everywhere, recompute fixed93binaryprobabilities, sumlogopposite/proposed meanprobability, equaltypeweights. Bothendpoints require5occ/3sentences; atmostONEpairrecommended withpositive/nonnegativegain threshold. Topgain tiesabstain (IDrekeyinvariant). Controls independent93sum,prior,3fixedpermutationmodels jointmasked. ReferencepairattachedAFTERscores; absent/unsupportedtruepaircountsmiss, sameclassswapclassnegative. Cal ONLYsourceclean+knownin/et. ALLattainablenonnegativegains+0/OFF; cleanfalsepairmust0 (pairchanges2types, henceoriginal<=1false-typeguard implies0pairs), maximizeknownexactpairhit,minwrongcorruptproposal,tiehigherthreshold. FreezeALL6policies before sourceTEST,cachedJerome/Caesarall8patterns. Reportexactpairtop1,wrongpairs,referenceavailability/ranks andcontrols; notoraclepairgiven. No correction/PPintegration/retraining/newannotations/reserve/sealedtest. Restrictedsinglebijectiveclassswap hypothesis; notgeneral lexicalmappingrecovery. Adaptive reuseddevelopmentsets.'))
    cal={}
    for pattern in ('correct','rehearsed_in_et'):
        independent=load(PREVIOUS/('calibration-'+pattern+'.json'));pred=prepare95(source('calibration'),anchors,words,patterns[pattern],'cal95',models,independent);save(OUT/('calibration-'+pattern+'.json'),pred);cal[pattern]=pred
    policies={}
    for arm in PAIR_ARMS:
        chosen,curve=calibrate_pair(cal['correct']['scores'][arm],cal['rehearsed_in_et']['scores'][arm],cal['correct']['reference'],cal['rehearsed_in_et']['reference']);policies[arm]=chosen;save(OUT/('calibration-curve-'+arm+'.json'),curve);print('policy',arm,chosen,flush=True)
    save(OUT/'policies.json',policies);save(OUT/'policy-freeze.json',dict(inputs={str(p):digest(p) for p in [OUT/'policies.json']+list(OUT.glob('calibration-*.json'))}));cache=load(CACHE);decl=load(DECLARATION)['split_ids'];datasets={'source':source('test')};datasets.update({a:cached_sentences(cache,decl[a]) for a in AUTHORS});summary={}
    for name,sentences in datasets.items():
        for pattern,replacements in patterns.items():
            folder=OUT/(name.lower()+'-'+pattern);folder.mkdir();independent=load(PREVIOUS/(name.lower()+'-'+pattern)/'predictions.json');pred=prepare95(sentences,anchors,words,replacements,'eval95-'+name,models,independent);save(folder/'predictions.json',pred);save(folder/'prediction-freeze.json',dict(inputs={str(folder/'predictions.json'):digest(folder/'predictions.json')}));result={a:pair_metrics(pred['scores'][a],float('inf') if p['threshold'] is None else p['threshold'],pred['reference']) for a,p in policies.items()};save(folder/'evaluation.json',result);summary[name+'/'+pattern]=result
        print('evaluated',name,flush=True)
    save(OUT/'evaluation.json',summary)
if __name__=='__main__':run()
