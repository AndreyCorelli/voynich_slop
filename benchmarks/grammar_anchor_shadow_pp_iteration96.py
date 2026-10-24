"""Apply every frozen pair recommendation, then measure fixed-policy PP effects."""
from benchmarks.grammar_paired_anchor_class_iteration95 import *
from voynich_smt.paired_anchor_class import recommend
from voynich_smt.anchor_shadow_repair import swap_assignments
OUT=ROOT/'iteration96';PAIR_SOURCE=ROOT/'iteration95'
PP_SETTINGS={'original':{'fixed80':.8},'augmented':{'selected89':.71,'fixed80':.8}}

def effect(rows,before,clean,cut):
    return dict(before=counts(before,'pp','pooled_pos',cut),after=counts(rows,'pp','pooled_pos',cut),clean=counts(clean,'pp','pooled_pos',cut),changes=transitions(rows,before,cut),hidden_after=counts([r for r in rows if not r['visible']],'pp','pooled_pos',cut),different_from_clean=sum((r['scores']['pooled_pos']['pp']>=cut)!=(c['scores']['pooled_pos']['pp']>=cut) for r,c in zip(rows,clean)))

def run():
    assert not OUT.exists();OUT.mkdir();data=load(ROOT/'iteration44/annotations-truth.json');part=load(ROOT/'iteration49/manifest.json')['partitions']['0'];source=lambda split:[dict(sent_id=sid,**data[sid]) for sid in part[split]];anchors=load(ROOT/'iteration85/anchor-budgets.json')['195'];patterns=load(ROOT/'iteration93/patterns.json');policies=load(PAIR_SOURCE/'policies.json');models={'original':load(BASE/'models.json'),'augmented':load(ROOT/'iteration89/models.json')};(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text());paths=[Path(__file__),Path('src/voynich_smt/anchor_shadow_repair.py'),Path('src/voynich_smt/paired_anchor_class.py'),Path('benchmarks/grammar_anchor_budget_iteration85.py'),ROOT/'iteration44/annotations-truth.json',ROOT/'iteration49/manifest.json',ROOT/'iteration85/anchor-budgets.json',ROOT/'iteration93/patterns.json',PAIR_SOURCE/'verification-manifest.json',PAIR_SOURCE/'policies.json',BASE/'models.json',BASE/'policies.json',ROOT/'iteration89/models.json',ROOT/'iteration89/policies.json',CACHE,DECLARATION]+list(PAIR_SOURCE.glob('*/predictions.json'))+list(ROOT.glob('iteration90/*/predictions.json'))
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='Frozen95recommendations, ALL6pairarms includingindependentunsafecontrol. Recompute atmostonepair fromcachedscores+frozencutoff ONLY, no referencepair/correctnessgate. Use95salts toalignopaqueIDs. SwapBOTHpublic anchornameandtag assignments betweenrecommendedIDs atALLoccurrences; IDs/privatePPtruth unchanged. Abstentions unchanged. For eachuniqueintervention rerun fixed85originalPP(.80primary) and89augmentedPP(.71selected,.80secondary); nofit/cal/thresholdchanges. Source/Jerome/CaesarALL8patterns93, cleannocorruptionandsameclasscontrols. ReportTP/FP/precision/recall, hiddenafter,newTP/newFP/lostTP/removedFP vsuncorrected, comparisoncleanreference (evaluationONLY), nearestleftF1. Preservealltransforms/predictionfreezes beforemetrics. Prior90uncorrected/clean scores are replaycontrols, never usedtoselectrepair. These reusedknownsynthetic singlebijectiveswap developmentprobes, notfreshconfirmation/generalblindrestoration. No mutationpriorartifacts/newannotations/reserve/sealedtest.'))
    cache=load(CACHE);decl=load(DECLARATION)['split_ids'];datasets={'source':source('test')};datasets.update({a:cached_sentences(cache,decl[a]) for a in AUTHORS});summary={};oldpol=load(BASE/'policies.json')
    for name,sentences in datasets.items():
        public,labels=transfer_rows(sentences,anchors,'eval95-'+name,models['original']['pos_classes']);clean={a:load(ROOT/'iteration90'/(name.lower()+'-'+a+'-correct')/'predictions.json') for a in models}
        for pattern,replacements in patterns.items():
            folder=OUT/(name.lower()+'-'+pattern);folder.mkdir();corrupted=perturb(public,replacements,anchors);save(folder/'public-before.json',corrupted);pairpred=load(PAIR_SOURCE/(name.lower()+'-'+pattern)/'predictions.json');interventions={'none':corrupted};arms={}
            for arm,policy in policies.items():
                cut=float('inf') if policy['threshold'] is None else policy['threshold'];pair=recommend(pairpred['scores'][arm],cut);key='none' if pair is None else '|'.join(sorted(pair));arms[arm]=dict(pair=pair,intervention=key)
                if key not in interventions:interventions[key]=swap_assignments(corrupted,pair)
            predictions={};actions={}
            for i,(key,repaired) in enumerate(interventions.items()):
                tag='intervention-'+str(i);actions[key]=dict(folder=tag,changed_tokens=sum(x!=y for s,t in zip(corrupted,repaired) for x,y in zip(s['tokens'],t['tokens'])));sub=folder/tag;sub.mkdir();save(sub/'public.json',repaired);predictions[key]={}
                for pp,model in models.items():
                    rows=infer85(query_rows(repaired,labels),model);predictions[key][pp]=rows;save(sub/(pp+'-predictions.json'),rows)
                save(sub/'prediction-freeze.json',dict(inputs={str(p):digest(p) for p in sub.glob('*.json')}))
            save(folder/'transforms.json',dict(arms=arms,actions=actions));result={}
            for arm,info in arms.items():
                key=info['intervention'];result[arm]=dict(recommended_pair=info['pair'],changed_tokens=actions[key]['changed_tokens'],pp={pp:{policy:effect(predictions[key][pp],predictions['none'][pp],clean[pp],cut) for policy,cut in cuts.items()} for pp,cuts in PP_SETTINGS.items()},nearest_f1=counts(predictions[key]['original'],'pp','left',oldpol['left']['standard']['f1']['threshold']))
            save(folder/'evaluation.json',result);summary[name+'/'+pattern]=result
        print('evaluated',name,flush=True)
    save(OUT/'evaluation.json',summary)
if __name__=='__main__':run()
