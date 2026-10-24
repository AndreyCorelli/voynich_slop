"""Replay sparse calibration probabilities, abstention search and frozen PP effects."""
from benchmarks.grammar_repair_abstention_iteration98 import *

def joint_only(public,words,models):
    byid={}
    for s in public:
        for t in s['tokens']:
            if t['anchor'] in words:byid.setdefault(t['id'],dict(proposed=t['tag'],n=0,sids=set()));byid[t['id']]['n']+=1;byid[t['id']]['sids'].add(s['sent_id'])
    adps=[i for i,r in byid.items() if r['proposed']=='ADP'];conjs=[i for i,r in byid.items() if r['proposed']=='CCONJ'];result=[]
    for a in adps:
        for c in conjs:
            rows=target_features(public,{a,c});q=ag.predict([r['features'] for r in rows],models['context']);gain=0.
            for opaque in (a,c):
                mean=q[[j for j,r in enumerate(rows) if r['word']==opaque]].mean(axis=0).tolist();margin,_=disagreement(mean,list(BINARY_CLASSES),byid[opaque]['proposed']);gain+=margin
            supported=all(byid[i]['n']>=5 and len(byid[i]['sids'])>=3 for i in (a,c));result.append(dict(pair=sorted((a,c)),gain=float(gain),supported=supported))
    return result

def run():
    for freeze in ('design-freeze.json','policy-freeze.json'):
        for p,h in load(OUT/freeze)['inputs'].items():assert digest(p)==h,p
    data=load(ROOT/'iteration44/annotations-truth.json');part=load(ROOT/'iteration49/manifest.json')['partitions']['0'];cat=load(ROOT/'iteration85/anchor-budgets.json');anchors=cat['195'];words=load(ROOT/'iteration93/types.json')['candidates'];models=load(ROOT/'iteration93/models.json');bank=load(OUT/'calibration-bank.json');assert bank==calibration_bank(cat['20'],load(ROOT/'iteration93/patterns.json'));blocks=load(OUT/'blocks.json');ordered=sorted(part['calibration'],key=lambda sid:__import__('hashlib').sha256(('cal98|'+sid).encode()).hexdigest());assert blocks['not_in_sparse']==ordered[800:];assert blocks['scored']['full']==part['calibration'];assert all(blocks['scored']['sparse'+str(i)]==ordered[100*i:100*(i+1)] for i in range(8));cases=[]
    for block,ids in blocks['scored'].items():
        public=ag.public_sentences([dict(sent_id=sid,**data[sid]) for sid in ids],anchors,'cal98-'+block);cache={}
        for case,replacements in bank.items():
            path=OUT/block/(case+'.json')
            for p,h in load(OUT/block/(case+'.freeze.json'))['inputs'].items():assert digest(p)==h,p
            changed=perturb(public,replacements,anchors);sig=signature(changed)
            if sig not in cache:cache[sig]=joint_only(changed,words,models)
            replay=cache[sig];stored=load(path)['scores'];aa={tuple(r['pair']):r for r in replay};bb={tuple(r['pair']):r for r in stored};assert aa.keys()==bb.keys()
            for pair,r in aa.items():assert r['supported']==bb[pair]['supported'];assert math.isclose(r['gain'],bb[pair]['gain'],rel_tol=1e-10,abs_tol=1e-12)
            ref=reference_for(public,replacements,case.startswith('swap_'),stored,words);cases.append(dict(block=block,case=case,regime='full' if block=='full' else 'sparse',features=pair_features(stored),reference=ref))
        print('replayed calibration',block,flush=True)
    assert len(cases)==603 and cases==load(OUT/'calibration-cases.json');policies=load(OUT/'policies.json')
    for arm,gap in (('absolute',False),('margin',True)):
        chosen,curve=calibrate(cases,gap);assert chosen==policies[arm] and curve==load(OUT/('calibration-curve-'+arm+'.json'))
    ppmodels={'original':load(BASE/'models.json'),'augmented':load(ROOT/'iteration89/models.json')};summary={};new_inferences=0
    for name in ('source','Jerome','Caesar'):
        previous=EVAL/name.lower();dataset=OUT/('eval-'+name.lower());public=load(previous/'public-clean.json');reference=load(previous/'reference-rows.json');labels=[dict(sid=r['sid'],index=r['index'],labels=r['labels']) for r in reference];payloads={}
        for path in (dataset/'new-pp-cache').glob('*.json'):
            if path.name.endswith('.freeze.json'):continue
            for p,h in load(path.with_suffix('.freeze.json'))['inputs'].items():assert digest(p)==h,p
            payload=load(path);view=apply_delta(public,payload['delta']);assert signature(view)==path.stem
            for a,m in ppmodels.items():
                replay=compact(infer85(query_rows(view,labels),m))
                for score in ('pooled_pos','left'):assert np.allclose(replay[score],payload['scores'][a][score],rtol=1e-10,atol=1e-12)
                assert replay['prior']==payload['scores'][a]['prior'];new_inferences+=1
            payloads[path.stem]=payload
        def get(sig):
            if sig not in payloads:payloads[sig]=load(previous/'pp-cache'/(sig+'.json'))
            return payloads[sig]
        clean=get(signature(public))['scores']
        for case in load(EVAL/'bank.json'):
            oldcase=previous/case;actions=load(oldcase/'actions.json');scores=load(oldcase/'detector.json')['joint_context'];features=pair_features(scores);view=apply_delta(public,get(actions['before'])['delta']);before=get(actions['before'])['scores'];ref=actions['reference'];result={};traces={}
            for arm,policy in policies.items():
                pair=select(features,policy['threshold'],policy['gap']);repaired=swap_assignments(view,pair);sig=signature(repaired);after=get(sig)['scores'];assert apply_delta(public,get(sig)['delta'])==repaired;hit=pair is not None and ref['pair'] is not None and pair==ref['pair'];p=dict(hit=int(hit),wrong=int(pair is not None and not hit),abstain=pair is None,reference_present=ref['pair'] is not None,reference_supported=any(r['supported'] and r['pair']==ref['pair'] for r in scores));result[arm]=dict(pair=p,pp={a:{policy:effect(expand(reference,after[a]),expand(reference,before[a]),expand(reference,clean[a]),cut) for policy,cut in cuts.items()} for a,cuts in PP_SETTINGS.items()});traces[arm]=dict(pair=pair,after=sig)
                if arm=='frozen95':assert pair==actions['selected']['joint_context']
            folder=dataset/case;assert load(folder/'actions.json')==dict(features=features,before=actions['before'],arms=traces);assert result==load(folder/'evaluation.json');summary[name+'/'+case]=result
        print('replayed evaluation',name,flush=True)
    assert summary==load(OUT/'evaluation.json');checked=0
    for path in ROOT.glob('iteration*/verification-manifest.json'):
        if path.parent==OUT:continue
        for p,h in load(path).get('inputs',{}).items():assert digest(p)==h,(path,p);checked+=1
    save(OUT/'audit.json',dict(all603calibration_cases_replayed=True,all186evaluation_cases_replayed=True,all_calibration_searches_and_blind_pp_effects_replayed=True,source_only_blocking_verified=True,new_pp_inferences_replayed=new_inferences,prior_input_hashes_verified=checked,reserve_unscored=True));print('audit passed',checked,'prior hashes')
if __name__=='__main__':run()
