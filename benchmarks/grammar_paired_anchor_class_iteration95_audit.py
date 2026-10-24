"""Replay blind pair scores, exact-pair policies and all evaluation decisions."""
from benchmarks.grammar_paired_anchor_class_iteration95 import *

def compare_predictions(a,b):
    assert a['reference']==b['reference'] and a['identities']==b['identities']
    for arm in PAIR_ARMS:
        aa={tuple(r['pair']):r for r in a['scores'][arm]};bb={tuple(r['pair']):r for r in b['scores'][arm]};assert aa.keys()==bb.keys()
        for pair,r in aa.items():assert r['supported']==bb[pair]['supported'];assert math.isclose(r['gain'],bb[pair]['gain'],rel_tol=1e-10,abs_tol=1e-12)

def run():
    for freeze in ('design-freeze.json','policy-freeze.json'):
        for p,h in load(OUT/freeze)['inputs'].items():assert digest(p)==h,p
    data=load(ROOT/'iteration44/annotations-truth.json');part=load(ROOT/'iteration49/manifest.json')['partitions']['0'];source=lambda split:[dict(sent_id=sid,**data[sid]) for sid in part[split]];anchors=load(ROOT/'iteration85/anchor-budgets.json')['195'];words=load(PREVIOUS/'types.json')['candidates'];models=load(PREVIOUS/'models.json');patterns=load(PREVIOUS/'patterns.json');policies=load(OUT/'policies.json');cal={};summary={};cache=load(CACHE);decl=load(DECLARATION)['split_ids'];datasets={'calibration':source('calibration'),'source':source('test')};datasets.update({a:cached_sentences(cache,decl[a]) for a in AUTHORS})
    for name,sentences in datasets.items():
        for pattern in (('correct','rehearsed_in_et') if name=='calibration' else patterns):
            salt='cal95' if name=='calibration' else 'eval95-'+name;independent=load(PREVIOUS/('calibration-'+pattern+'.json')) if name=='calibration' else load(PREVIOUS/(name.lower()+'-'+pattern)/'predictions.json');pred=prepare95(sentences,anchors,words,patterns[pattern],salt,models,independent)
            if name=='calibration':stored=load(OUT/('calibration-'+pattern+'.json'));cal[pattern]=stored
            else:
                folder=OUT/(name.lower()+'-'+pattern)
                for p,h in load(folder/'prediction-freeze.json')['inputs'].items():assert digest(p)==h,p
                stored=load(folder/'predictions.json');result={a:pair_metrics(stored['scores'][a],float('inf') if p['threshold'] is None else p['threshold'],stored['reference']) for a,p in policies.items()};assert result==load(folder/'evaluation.json');summary[name+'/'+pattern]=result
            compare_predictions(pred,stored)
        # Strip private annotation and evaluation truth flags; independently rekeying IDs
        # must not influence scores, pair selection or the semantic chosen word pair.
        stripped=[dict(sent_id=s['sent_id'],tokens=[dict(word=t['word']) for t in s['tokens']]) for s in sentences];ind=load(PREVIOUS/'calibration-correct.json') if name=='calibration' else load(PREVIOUS/(name.lower()+'-correct')/'predictions.json');ind2=dict(ind,records={arm:[{k:v for k,v in r.items() if k!='class_wrong'} for r in rows] for arm,rows in ind['records'].items()});a=prepare95(sentences,anchors,words,{},'invariantA',models,ind);b=prepare95(stripped,anchors,words,{},'invariantB',models,ind2)
        for arm in PAIR_ARMS:
            def semantic(pred):return {tuple(sorted(pred['identities'][opaque] for opaque in r['pair'])):r['gain'] for r in pred['scores'][arm]}
            x=semantic(a);y=semantic(b);assert x.keys()==y.keys();assert all(math.isclose(x[k],y[k],rel_tol=1e-10,abs_tol=1e-12) for k in x)
        print('replayed',name,flush=True)
    for arm in PAIR_ARMS:
        chosen,curve=calibrate_pair(cal['correct']['scores'][arm],cal['rehearsed_in_et']['scores'][arm],cal['correct']['reference'],cal['rehearsed_in_et']['reference']);assert chosen==policies[arm] and curve==load(OUT/('calibration-curve-'+arm+'.json'))
    assert summary==load(OUT/'evaluation.json');checked=0
    for path in ROOT.glob('iteration*/verification-manifest.json'):
        if path.parent==OUT:continue
        for p,h in load(path).get('inputs',{}).items():assert digest(p)==h,(path,p);checked+=1
    ranks={}
    for key in summary:
        name,pattern=key.split('/');pred=load(OUT/(name.lower()+'-'+pattern)/'predictions.json');truth=pred['reference']['pair'];ranks[key]={}
        for arm,rows in pred['scores'].items():
            available=[r for r in rows if r['supported']];target=next((r for r in rows if r['pair']==truth),None)
            ranks[key][arm]=dict(reference_gain=target['gain'] if target else None,reference_supported=bool(target and target['supported']),supported_rank=1+sum(r['gain']>target['gain']+1e-12 for r in available) if target and target['supported'] else None,max_supported_gain=max((r['gain'] for r in available),default=None))
    assert ranks==load(OUT/'rank-summary.json')
    save(OUT/'audit.json',dict(rank_diagnostics_verified=True,all26scenarios_and6arms_replayed=True,no_reference_pair_used_by_scorer=True,private_annotation_truth_flag_and_rekey_invariance=True,policies_source_calibrated=True,prior_input_hashes_verified=checked,reserve_unscored=True));print('audit passed',checked,'prior hashes')
if __name__=='__main__':run()
