"""One frozen Dante Case evaluation: four preexisting models, no refitting."""
from collections import defaultdict,Counter
import random,re
from benchmarks.grammar_within_author_ranking_iteration196 import ROOT,Path,load,save,digest,ranking_predict,topk,auc,evaluate,predict
from benchmarks.grammar_case_applicability_iteration180 import features_for
from benchmarks.grammar_case_subfamilies_iteration172 import score,CASES
from benchmarks.grammar_multi_author_review192_193 import listmetrics
OUT=ROOT/'iteration199';COVER=ROOT/'iteration198';MODELS=ROOT/'iteration196';PREVIOUS=ROOT/'iteration194'
NAMES=['point_rich','point_control','rank_rich','rank_control'];SEEDS=list(range(19900,20099))
POLICY='ONE-SHOT admitted DVE+Mon Case-only evaluation on fixed198 primary76pairs. Use saved196 Tacitus-fold point_rich/point_control/rank_rich/rank_control, identical to saved matched Palladius-fold variants, all trained Aq/Ca/Ci/Je before Dante FORM projection. No fit/source/scaling/feature/ridge/model choice or reserve-based adaptation. Copy models/prior (194 Tacitus without-Palladius), compute193/180 query-excluded features; freeze features, all model outputs and all selections before decoding any reserved Case. Fixed tied top10/top20 for all4, .5 only pointwise; prior classification/allcandidate baseline. Primary rank_rich top10 applicability; all4 required, top20/AUC/equality/joint/type coverage secondary; NLL/Brier/calibration pointwise/prior only, raw rank scores not probabilities. Decode Case FEATS only in198 admitted sentences, no POS/LEMMA/HEAD/DEPREL access; missing/multivalue/unrecognizedCase unscored. Reserve Case annotations consumed for this evaluation, not fresh in future. Further predeclared baseline:199fixedseeds19900..20098, independently shuffle Case including missing values among ALL lexical occurrences within each opaque word, preserve wordcase profiles, no POS conditioning; keep graphs/predictions/lists fixed. Report conditional equality/applicability/joint null ranges and exceedances for all fixed lists and allcandidate; no selected null/policy or confidence claim. One annotation-reserved author with prior raw exposure and unresolved provenance flag, not universal accuracy/namedcase/word identity recovery. No letters/quarantines/Seneca gold opened.'

def read_case(path,wanted):
    sid=None
    with path.open() as handle:
        for line in handle:
            if line.startswith('# sent_id ='):sid=line.split('=',1)[1].strip()
            elif line.startswith('#') or not line.strip() or sid not in wanted:continue
            else:
                tabs=[i for i,c in enumerate(line) if c=='\t'];assert len(tabs)==9
                identifier=line[:tabs[0]]
                if not identifier.isdigit():continue
                feats=line[tabs[4]+1:tabs[5]];m=re.search(r'(?:^|\|)Case=([^|]+)',feats);value=m[1] if m else ''
                yield (str(path),sid,int(identifier)),value if value in CASES else '',value

def scored_lists(rows,selections,eligible):return {n:listmetrics([rows[i] for i in ix],eligible) for n,ix in selections.items()}

def run():
    assert not OUT.exists();OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    rawpaths=sorted({r['path'] for r in load(COVER/'admitted-sentences.json')})
    paths=[Path(__file__),Path('benchmarks/grammar_case_applicability_iteration180.py'),Path('benchmarks/grammar_case_subfamilies_iteration172.py'),Path('benchmarks/grammar_within_author_ranking_iteration196.py')]+[COVER/n for n in ['verification-manifest.json','graphs.json','admitted-sentences.json','provenance-status.json']]+[MODELS/n for n in ['verification-manifest.json','models.json','trials.json']]+[PREVIOUS/n for n in ['verification-manifest.json','models.json']]+[Path(p) for p in rawpaths]
    save(OUT/'design-freeze.json',dict(policy=POLICY,seeds=SEEDS,inputs={str(p):digest(p) for p in paths}))
    for folder in [COVER,MODELS,PREVIOUS]:
        for p,h in load(folder/'verification-manifest.json').items():assert digest(Path(p))==h
    frozen=load(MODELS/'models.json');trials=load(MODELS/'trials.json');assert trials['Tacitus']['eligible_authors']==['Aquinas','Caesar','Cicero','Jerome'];models={n:frozen['Tacitus'][n] for n in NAMES};assert all(models[n]==frozen['Palladius'][n] for n in NAMES)
    prior=load(PREVIOUS/'models.json')['Tacitus']['without-Palladius']['prior']['probability'];save(OUT/'models.json',dict(models=models,prior_probability=prior,source_authors=trials['Tacitus']['eligible_authors']))
    graph=load(COVER/'graphs.json')['primary'];dd=graph['descriptors'];assert len(dd)==76;ff=features_for(graph['ids'],dd);save(OUT/'features.json',ff)
    outputs={n:ranking_predict(ff,m['model']) if m['kind']=='ranking_score' else predict(ff,m['model']) for n,m in models.items()};outputs['prior']=[prior]*len(dd)
    selections={'all_candidates':list(range(len(dd)))}
    for n in NAMES:
        for k in [10,20]:selections[n+'/top'+str(k)]=topk(outputs[n],k)
        if models[n]['kind']=='probability':selections[n+'/threshold']=[i for i,p in enumerate(outputs[n]) if p>=.5]
    save(OUT/'outputs.json',outputs);save(OUT/'selections.json',selections);save(OUT/'prediction-freeze.json',{n:digest(OUT/n) for n in ['models.json','features.json','outputs.json','selections.json']})
    # First reserved Case decoding occurs after the prediction/selection freeze above.
    admitted=load(COVER/'admitted-sentences.json');wanted=defaultdict(set)
    for r in admitted:wanted[r['path']].add(r['sent_id'])
    case={};rawcase=Counter()
    for path,sids in wanted.items():
        for key,c,raw in read_case(Path(path),sids):case[key]=c;rawcase[raw]+=1
    cc=[case[tuple(p)] if p else '' for p in graph['positions']];save(OUT/'case-references.json',dict(case_by_stream_position=cc,admitted_integer_rows=len(case),raw_case_values=dict(rawcase),pos_fields_decoded=False))
    rows=score(dd,cc,['X']*len(cc))['all'];save(OUT/'case-details.json',rows);y=[int(r['case_occurrence_pairs']>0) for r in rows];eligible=len({e[k] for e in dd for k in ['a','b']});metrics=scored_lists(rows,selections,eligible)
    classification={n:evaluate(y,v) for n,v in outputs.items() if n=='prior' or models[n]['kind']=='probability'};aucs={n:auc(y,v) for n,v in outputs.items()};save(OUT/'classification.json',classification);save(OUT/'summary.json',dict(eligible_candidate_endpoint_types=eligible,candidate_pairs=len(dd),case_applicable_pairs=sum(y),classification=classification,auc=aucs,lists=metrics))
    save(OUT/'selected-details.json',{name:[dict(edge=i,**rows[i]) for i in ix] for name,ix in selections.items()})
    groups=defaultdict(list)
    for i,p in enumerate(graph['positions']):
        if p:groups[graph['ids'][i]].append(i)
    nulls={}
    for seed in SEEDS:
        rng=random.Random(seed);permuted=cc.copy()
        for word in sorted(groups):
            positions=groups[word];values=[cc[i] for i in positions];rng.shuffle(values)
            for i,c in zip(positions,values):permuted[i]=c
        nr=score(dd,permuted,['X']*len(cc))['all'];nulls[str(seed)]=scored_lists(nr,selections,eligible)
    save(OUT/'word-profile-nulls.json',nulls)
    comparisons={}
    for name,actual in metrics.items():
        comparisons[name]={}
        for key in ['edge_applicability','edge_macro_frame_case_agreement','edge_joint_yield']:
            values=[v[name][key] for v in nulls.values() if v[name][key] is not None];a=actual[key];comparisons[name][key]=dict(actual=a,nonempty_nulls=len(values),min=min(values) if values else None,max=max(values) if values else None,mean=sum(values)/len(values) if values else None,at_least_actual=sum(v>=a for v in values) if a is not None else None)
    save(OUT/'null-comparisons.json',comparisons)
    print('case-applicable',sum(y),'of',len(y),flush=True)
    for name,v in metrics.items():print(name,{k:v[k] for k in ['edges','case_edges','case_types_involved','edge_macro_frame_case_agreement','edge_joint_yield']},flush=True)
    print('AUC',aucs,flush=True);print('classification',{n:{k:m[k] for k in ['nll','brier','predicted_positive','precision','recall']} for n,m in classification.items()},flush=True)
    print('rank rich top10 word-profile null',comparisons['rank_rich/top10'],flush=True)
if __name__=='__main__':run()
