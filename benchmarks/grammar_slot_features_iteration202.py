"""Fixed slot-feature block x applicability/surplus objective on development only."""
import math
from collections import Counter,defaultdict
import numpy as np
from benchmarks.grammar_contextual_surplus_iteration201 import ROOT,Path,load,save,digest,AUTHORS,fit_surplus,predict_surplus,summarize
from benchmarks.grammar_multi_author_iteration193 import weighted_fit,predict
from benchmarks.grammar_within_author_ranking_iteration196 import topk
OUT=ROOT/'iteration202';BASE=ROOT/'iteration193';RESIDUAL=ROOT/'iteration201';OLD=ROOT/'iteration196'
SLOT_COLS=['mean_log_left_frequency','mean_log_right_frequency','mean_abs_anchor_log_frequency_difference','mean_log1p_slot_count','mean_log_slot_types','mean_normalized_slot_entropy','mean_pair_slot_fraction','mean_pair_imbalance','mean_log1p_pair_comparisons','log1p_query_occurrences','log_distinct_left_anchors','log_distinct_right_anchors','context_jaccard','context_cosine']
POLICY='Development-only fixed four193 authorgraphs, 201surplus labels,196sourcepolicy. Freeze14query-localfeatures before label load: means over sharedframes of logglobal left/right anchor counts, absolute loganchor difference, log1p total slotcenter count, log distinct slotcenters, normalized center entropy H/logN, pair countfraction, absolute pair countimbalance/(a+b), log1p(a_count*b_count); log1p total queried endpointoccurrences; log distinctleft/right anchors; full valid lexical-context Jaccard/cosine between endpoint context-count distributions. All slotcounts include ALL lexical centers, no frequencyfilter, same sentence/nonlex boundaries; no POS/Case inputs. Augment old19 with full14 block, no subset/tuning. Factorial old19vs33 x Case-applicability logistic(meanNLL+.1/2slopeL2) vs201surplus ridge(.5weightedMSE+.1/2slopeL2), interceptfree/unpenalized. Same other3authors, equal authorweight, recomputed source-only scaling on33; old19 exactcopies of196/201. Keep3featurepoint/surplus controls. Freeze allfeatures/models/scores/tiedtop10/20 before metrics; primary augmentedsurplus vs19surplus mean/positive>1e-12counts, applicability/type/equality/joint costs and classification featurecontrast required. No new gold/raw/reserve data, no targetselectedobjective/block/winner or freshvalidation/POS/Caseidentity claim.'

def slot_features(g):
    ids=g['ids'];pos=g['positions'];counts=Counter(ids);slots=defaultdict(Counter);contexts=defaultdict(Counter)
    for i in range(1,len(ids)-1):
        if pos[i] and pos[i-1] and pos[i+1]:f=(ids[i-1],ids[i+1]);slots[f][ids[i]]+=1;contexts[ids[i]][f]+=1
    result=[]
    for e in g['descriptors']:
        framevalues=[];queried=0;left=set();right=set()
        for f in e['frames']:
            l,r=f['frame'];slot=slots[(l,r)];n=sum(slot.values());a=slot[e['a']];b=slot[e['b']];assert a==len(f['a_positions']) and b==len(f['b_positions']);queried+=a+b;left.add(l);right.add(r);ent=-sum((v/n)*math.log(v/n) for v in slot.values())/math.log(n) if n>1 else 0.
            framevalues.append([math.log(counts[l]),math.log(counts[r]),abs(math.log(counts[l])-math.log(counts[r])),math.log1p(n),math.log(len(slot)),ent,(a+b)/n,abs(a-b)/(a+b),math.log1p(a*b)])
        ca=contexts[e['a']];cb=contexts[e['b']];common=set(ca)&set(cb);union=set(ca)|set(cb);assert len(common)==e['shared_frames'];cosine=sum(ca[k]*cb[k] for k in common)/math.sqrt(sum(v*v for v in ca.values())*sum(v*v for v in cb.values()));values=np.mean(framevalues,axis=0).tolist()+[math.log1p(queried),math.log(len(left)),math.log(len(right)),len(common)/len(union),cosine];assert len(values)==14
        result.append(dict(a=e['a'],b=e['b'],values=values))
    return result

def run():
    assert not OUT.exists();OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text());paths=[Path(__file__),Path('benchmarks/grammar_contextual_surplus_iteration201.py'),Path('benchmarks/grammar_multi_author_iteration193.py')]+[BASE/n for n in ['graphs.json','features.json','development-references.json','finalized-sizes.json']]+[RESIDUAL/n for n in ['verification-manifest.json','labels.json','models.json','outputs.json']]+[OLD/n for n in ['verification-manifest.json','models.json','scores.json','trials.json']]
    save(OUT/'design-freeze.json',dict(policy=POLICY,slot_columns=SLOT_COLS,inputs={str(p):digest(p) for p in paths}))
    for folder in [RESIDUAL,OLD]:
        for p,h in load(folder/'verification-manifest.json').items():assert digest(Path(p))==h
    graphs=load(BASE/'graphs.json');original=load(BASE/'features.json');slots={a:slot_features(graphs[a]) for a in AUTHORS};ff={a:[dict(a=r['a'],b=r['b'],values=r['values']+s['values']) for r,s in zip(original[a],slots[a],strict=True)] for a in AUTHORS};save(OUT/'slot-features.json',slots);save(OUT/'features.json',ff);save(OUT/'feature-freeze.json',{n:digest(OUT/n) for n in ['slot-features.json','features.json']})
    labels=load(RESIDUAL/'labels.json');case=load(BASE/'development-references.json');sizes=load(BASE/'finalized-sizes.json');oldoutputs=load(RESIDUAL/'outputs.json');models={};outputs={};selections={}
    for target in AUTHORS:
        train=[a for a in AUTHORS if a!=target];raw=[r['values'] for a in train for r in ff[a]];w=[1/len(ff[a]) for a in train for _ in ff[a]];y=[int(r['case_occurrence_pairs']>0) for a in train for r in case[a]];residual=[r['surplus'] for a in train for r in labels[a]];point=weighted_fit(raw,y,w,list(range(33)));surplus=fit_surplus(raw,residual,w,list(range(33)),point);models[target]=dict(point_augmented=point,surplus_augmented=surplus);outputs[target]=dict(point_augmented=predict(ff[target],point),surplus_augmented=predict_surplus(ff[target],surplus),point_original=oldoutputs[target]['point_rich'],surplus_original=oldoutputs[target]['surplus_rich'],point_control=oldoutputs[target]['point_control'],surplus_control=oldoutputs[target]['surplus_control']);selections[target]={name+'/top'+str(k):topk(v,k) for name,v in outputs[target].items() for k in [10,20]}
    for n,obj in [('models',models),('outputs',outputs),('selections',selections)]:save(OUT/(n+'.json'),obj)
    save(OUT/'prediction-freeze.json',{n:digest(OUT/n) for n in ['models.json','outputs.json','selections.json']});summary={};contrasts={}
    for a in AUTHORS:
        summary[a]={name:summarize(ix,labels[a],case[a],sizes[a]['types']) for name,ix in selections[a].items()};contrasts[a]={}
        for objective in ['point','surplus']:
            new=summary[a][objective+'_augmented/top10'];old=summary[a][objective+'_original/top10'];contrasts[a][objective]=dict(mean_surplus_change=new['mean_surplus']-old['mean_surplus'],positive_pair_change=new['positive_surplus_pairs']-old['positive_surplus_pairs'],applicable_pair_change=new['case_metrics']['case_edges']-old['case_metrics']['case_edges'])
    save(OUT/'summary.json',summary);save(OUT/'contrasts.json',contrasts)
    for a,ss in summary.items():print(a,{n:(round(s['mean_surplus'],6),s['positive_surplus_pairs'],s['case_metrics']['case_edges'],s['selected']) for n,s in ss.items()},flush=True)
if __name__=='__main__':run()
