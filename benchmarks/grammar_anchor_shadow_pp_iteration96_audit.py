"""Replay blind actions and PP predictions; verify all uncorrected/clean controls."""
from benchmarks.grammar_anchor_shadow_pp_iteration96 import *
from benchmarks.grammar_anchor_augmentation_iteration89_audit import compare

def compare_rekeyed(rows,reference):
    assert len(rows)==len(reference)
    for r,t in zip(rows,reference):
        assert (r['sid'],r['index'],r['labels'])==(t['sid'],t['index'],t['labels'])
        for arm in ARMS:assert math.isclose(r['scores'][arm]['pp'],t['scores'][arm]['pp'],rel_tol=1e-10,abs_tol=1e-12)

def run():
    for p,h in load(OUT/'design-freeze.json')['inputs'].items():assert digest(p)==h,p
    data=load(ROOT/'iteration44/annotations-truth.json');part=load(ROOT/'iteration49/manifest.json')['partitions']['0'];source=lambda split:[dict(sent_id=sid,**data[sid]) for sid in part[split]];anchors=load(ROOT/'iteration85/anchor-budgets.json')['195'];patterns=load(ROOT/'iteration93/patterns.json');policies=load(PAIR_SOURCE/'policies.json');models={'original':load(BASE/'models.json'),'augmented':load(ROOT/'iteration89/models.json')};cache=load(CACHE);decl=load(DECLARATION)['split_ids'];datasets={'source':source('test')};datasets.update({a:cached_sentences(cache,decl[a]) for a in AUTHORS});summary={};oldpol=load(BASE/'policies.json');perfect_repairs=0;inferences=0
    for name,sentences in datasets.items():
        public,labels=transfer_rows(sentences,anchors,'eval95-'+name,models['original']['pos_classes']);clean={a:load(ROOT/'iteration90'/(name.lower()+'-'+a+'-correct')/'predictions.json') for a in models}
        for pattern,replacements in patterns.items():
            folder=OUT/(name.lower()+'-'+pattern);corrupted=perturb(public,replacements,anchors);assert corrupted==load(folder/'public-before.json');pairpred=load(PAIR_SOURCE/(name.lower()+'-'+pattern)/'predictions.json');transforms=load(folder/'transforms.json');actions={};arms={};interventions={'none':corrupted}
            for arm,policy in policies.items():
                cut=float('inf') if policy['threshold'] is None else policy['threshold'];pair=recommend(pairpred['scores'][arm],cut);key='none' if pair is None else '|'.join(sorted(pair));arms[arm]=dict(pair=pair,intervention=key)
                if key not in interventions:interventions[key]=swap_assignments(corrupted,pair)
            assert arms==transforms['arms'];predictions={}
            for i,(key,repaired) in enumerate(interventions.items()):
                tag='intervention-'+str(i);actions[key]=dict(folder=tag,changed_tokens=sum(x!=y for s,t in zip(corrupted,repaired) for x,y in zip(s['tokens'],t['tokens'])));sub=folder/tag;assert repaired==load(sub/'public.json');assert [t['id'] for s in repaired for t in s['tokens']]==[t['id'] for s in corrupted for t in s['tokens']]
                for p,h in load(sub/'prediction-freeze.json')['inputs'].items():assert digest(p)==h,p
                predictions[key]={}
                for pp,model in models.items():
                    rows=load(sub/(pp+'-predictions.json'));compare(infer85(query_rows(repaired,labels),model),rows);predictions[key][pp]=rows;inferences+=1
                    if key=='none':compare_rekeyed(rows,load(ROOT/'iteration90'/(name.lower()+'-'+pp+'-'+pattern)/'predictions.json'))
                    if repaired==public:compare_rekeyed(rows,clean[pp])
                if key!='none' and repaired==public:perfect_repairs+=1
            assert actions==transforms['actions'];result={}
            for arm,info in arms.items():
                key=info['intervention'];result[arm]=dict(recommended_pair=info['pair'],changed_tokens=actions[key]['changed_tokens'],pp={pp:{policy:effect(predictions[key][pp],predictions['none'][pp],clean[pp],cut) for policy,cut in cuts.items()} for pp,cuts in PP_SETTINGS.items()},nearest_f1=counts(predictions[key]['original'],'pp','left',oldpol['left']['standard']['f1']['threshold']))
            assert result==load(folder/'evaluation.json');summary[name+'/'+pattern]=result
        print('replayed',name,flush=True)
    assert summary==load(OUT/'evaluation.json');checked=0
    for path in ROOT.glob('iteration*/verification-manifest.json'):
        if path.parent==OUT:continue
        for p,h in load(path).get('inputs',{}).items():assert digest(p)==h,(path,p);checked+=1
    save(OUT/'audit.json',dict(all24scenarios_and6pairarms_replayed=True,pp_inferences_replayed=inferences,unique_exact_clean_repairs=perfect_repairs,blind_public_actions_verified=True,uncorrected_scores_reproduce90=True,exact_public_repairs_reproduce_clean_scores=True,prior_input_hashes_verified=checked,reserve_unscored=True));print('audit passed',checked,'prior hashes')
if __name__=='__main__':run()
