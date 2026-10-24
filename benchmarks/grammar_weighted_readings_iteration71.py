"""Fixed-pair ablation of candidate-conditioned POS weights; no search."""
from benchmarks.grammar_role_compatibility_iteration70 import *
from voynich_smt.grammar_lexical_bridge import pos_model
PREVIOUS=ROOT/'iteration70';OUT=ROOT/'iteration71'
def weights(word,rr,pm):
    # Source word POS counts with one pseudo-observation distributed according
    # to source POS priors. Divide POS mass over its distinct joint readings.
    observed=Counter()
    for p,n in pm['words'].get(word,{}).items():observed[coarse(p)]+=n
    prior=Counter()
    for p,n in pm['prior'].items():prior[coarse(p)]+=n
    total=sum(prior.values());n=sum(observed.values());multiplicity=Counter(r[0] for r in rr)
    return [(observed[r[0]]+prior[r[0]]/total)/(n+1)/multiplicity[r[0]] for r in rr]
def weighted_mass(model,p,rr,ww):
    return float(sum(q*sum(w for r,w in zip(rr,ww) if compatible(g,r)) for (_,g),q in zip(model['labels'],p)))
def evaluate71(rows):
    arms={}
    for name in rows[0]['scores']:
        ds=[r['scores'][name][0]-r['scores'][name][1] for r in rows]
        arms[name]=dict(win=sum(d>1e-10 for d in ds),loss=sum(d< -1e-10 for d in ds),tie=sum(abs(d)<=1e-10 for d in ds))
        arms[name]['strict_accuracy']=arms[name]['win']/len(rows)
    c=arms['weighted_context']['strict_accuracy'];passed=c>=.65 and c>=arms['frequency']['strict_accuracy']+.10 and c>=arms['weighted_shuffle']['strict_accuracy']+.05 and c>=arms['weighted_prior']['strict_accuracy']+.10
    return dict(n=len(rows),arms=arms,gate_passed=passed,search_run=False,nuclei_measured=False)
def run():
    assert not OUT.exists();OUT.mkdir()
    for p,h in load(PREVIOUS/'verification-manifest.json')['inputs'].items():assert digest(p)==h,p
    paths=[Path(__file__),Path('benchmarks/grammar_role_compatibility_iteration70.py'),Path('src/voynich_smt/grammar_lexical_bridge.py'),PREVIOUS/'predictions.json',PREVIOUS/'model.json',ROOT/'iteration44/annotations-truth.json',ROOT/'iteration49/manifest.json',PREVIOUS/'verification-manifest.json',Path('experiments/holdouts/grammar-construction-next.json')]
    (OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='Hold all1273iteration70pairs, sourcefold0 and contextual model fixed. Candidate reading weights: sourceword coarsePOS count plus one pseudo-observation distributed over global sourcePOS prior; divide each POS probability equally across distinct joint readings of that POS. Unseen word uses global POS prior; unknown dictionary remains zero. Do not renormalize over dictionary-supportedPOS: rare supported readings cannot absorb mass of a common unsupportedPOS. Case/Number weights within POS are uniform, not learned token-analysis probabilities. Primary weighted contextual expected compatibility vs weighted prior/shuffle, original union and frequency. No tuning. Same70privileged pair construction and perfect surroundingplaintext retained. Gate strictwin>=65%, >=frequency+10pp, >=weightedprior+10pp, >=weightedshuffle+5pp; iffails stop before corruption/search.'))
    data=load(ROOT/'iteration44/annotations-truth.json');ids=load(ROOT/'iteration49/manifest.json')['partitions']['0']['fit'];pm=pos_model(data[i]['tokens'] for i in ids);save(OUT/'word-pos-model.json',pm);save(OUT/'model-freeze.json',dict(word_pos=digest(OUT/'word-pos-model.json')))
    model=load(PREVIOUS/'model.json');rows=[];audit=Counter()
    for old in load(PREVIOUS/'predictions.json'):
        rr=old['readings'];ww=[weights(w,r,pm) for w,r in zip((old['word'],old['other']),rr)];scores={k:old['scores'][k] for k in ('context','shuffle','prior','frequency')}
        for name,p in [('context',posterior(model,old['context'])),('shuffle',posterior(model,old['shuffled_context'])),('prior',model['prior'])]:scores['weighted_'+name]=[weighted_mass(model,p,r,w) for r,w in zip(rr,ww)]
        if old['other']=='non':
            audit['non_pairs']+=1
            audit['non_union_losses']+=old['scores']['context'][0]<old['scores']['context'][1]-1e-10
            audit['non_weighted_losses']+=scores['weighted_context'][0]<scores['weighted_context'][1]-1e-10
        rows.append(dict(**{k:v for k,v in old.items() if k!='scores'},weights=ww,scores=scores))
    save(OUT/'predictions.json',rows);save(OUT/'prediction-freeze.json',dict(predictions=digest(OUT/'predictions.json')));result=evaluate71(rows);result['non_attribution']=dict(audit);save(OUT/'evaluation.json',result);print(json.dumps(result,indent=2))
if __name__=='__main__':run()
