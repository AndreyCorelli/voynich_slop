"""Oracle lexical identifiability and repeated-type grammatical pooling."""
from benchmarks.grammar_normalized_readings_iteration73 import *
PREVIOUS=ROOT/'iteration75';OUT=ROOT/'iteration76'
INVENTORY=Path('experiments/results/latin-large-dictionary/forms-100000.jsonl')

def strict_compatible(g,r):
    return g[0]==r[0] and all(not a or a==b for a,b in zip(g[1:],r[1:]))

def credible(p,mass=.9):
    order=sorted(range(len(p)),key=lambda i:(-p[i],i));chosen=[];s=0.
    for i in order:
        chosen.append(i);s+=p[i]
        if s>=mass-1e-12:break
    return chosen

def pooling_metrics(groups,profiles,prior):
    index={p:i for i,p in enumerate(profiles)};repeated=[g for g in groups if len(g['occurrences'])>=2];result={}
    for task in ('profile','pos'):
        pos=sorted({p[0] for p in profiles})
        def project(p):return np.array(p) if task=='profile' else np.array([sum(v for pr,v in zip(profiles,p) if pr[0]==x) for x in pos])
        arms=defaultdict(list)
        for g in repeated:
            occ=g['occurrences'];n=len(occ)
            for i,r in enumerate(occ):
                target=index[tuple(r['gold_profile'])] if task=='profile' else pos.index(r['gold_profile'][0])
                for arm in ('context','shuffle','prior'):
                    vectors=[np.array(o[arm]) for o in occ];pooled=sum(vectors)/n;loo=(sum(vectors)-vectors[i])/(n-1)
                    for mode,p in [('local',vectors[i]),('pooled',pooled),('other_occurrences',loo)]:
                        q=project(p);cs=credible(q);arms[arm+'/'+mode].append(dict(word=g['word'],loss=-math.log(max(1e-12,float(q[target]))),correct=int(np.argmax(q)==target),covered=int(target in cs),size=len(cs)))
        result[task]={}
        for name,rows in arms.items():
            bytype=defaultdict(list)
            for r in rows:bytype[r['word']].append(r)
            result[task][name]=dict(tokens=len(rows),types=len(bytype),nll=float(np.mean([r['loss'] for r in rows])),accuracy=float(np.mean([r['correct'] for r in rows])),credible90_coverage=float(np.mean([r['covered'] for r in rows])),credible90_size=float(np.mean([r['size'] for r in rows])),macro_type_nll=float(np.mean([np.mean([r['loss'] for r in rr]) for rr in bytype.values()])))
    return result

def oracle_summary(rows):
    result={}
    for subset,rr in [('all',rows),('repeated',[r for r in rows if r['tokens']>=2])]:
        result[subset]=dict(types=len(rr),tokens=sum(r['tokens'] for r in rr),inventory_present=sum(r['inventory_present'] for r in rr),distinct_reference_profiles_gt1=sum(r['distinct_profiles']>1 for r in rr),modes={})
        for mode in ('tolerant','strict'):
            z=[r[mode] for r in rr];result[subset]['modes'][mode]=dict(gold_survives=sum(r['gold_survives'] for r in z),unique_correct=sum(r['size']==1 and r['gold_survives'] for r in z),unique_wrong=sum(r['size']==1 and not r['gold_survives'] for r in z),empty=sum(r['size']==0 for r in z),median_pool=float(np.median([r['size'] for r in z])),median_first_pool=float(np.median([r['first_size'] for r in z])),repetition_reduces_pool=sum(r['size']<r['first_size'] for r in z),frequency_top1=sum(r['gold_rank']==1 for r in z),frequency_top10=sum(r['gold_rank'] is not None and r['gold_rank']<=10 for r in z))
    return result

def run():
    assert not OUT.exists();OUT.mkdir()
    for p,h in load(PREVIOUS/'verification-manifest.json')['inputs'].items():assert digest(p)==h,p
    paths=[Path(__file__),Path('benchmarks/grammar_normalized_readings_iteration73.py'),Path('benchmarks/grammar_role_compatibility_iteration70.py'),ROOT/'iteration70/model.json',ROOT/'iteration71/predictions.json',INVENTORY,PREVIOUS/'verification-manifest.json',Path('experiments/holdouts/grammar-construction-next.json')]
    (OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='Two fixed phases on1273contentpositions/844types of already declared100Caesar sentences. A:100kfixedinventory, offer allforms, no content/truth filtering or goldappend. For eachtype intersect compatible candidates across referencejointPOS/Case/Number profiles. Tolerant missingfeatures wildcard and strict requiredreferencefeatures mustbeexplicit controls; jointreadings preserved. Compare firstoccurrence vs all, inventorycoverage, truecandidate survival, empty/uniquecorrect/uniquewrong, source70frequency ranks withlexicalties. Explicit oracle not recovery. B: frozen70posterior pooled arithmeticmean per repeatedwordtype (grouping only opaque equality; correct surroundingplaintext stillsupplied). Compare peroccurrence, pooledall and leaveoneoutotheroccurrences vs savedshuffle/prior. POS and jointprofile NLL/accuracy, fixed90%credible setsize/coverage, typebalancedloss. No candidate rankings/search inB, no goldlabels inferpooledposteriors. Bothphases alwaysrun, no tunedthresholds. Repeatedword surfaces as cipheridentity surrogate; no keys/wordidentity features added. No refits/reserve/sealedtest scoring.'))
    model=load(ROOT/'iteration70/model.json');profiles,prior=profile_space(model);byword=defaultdict(list)
    for r in load(ROOT/'iteration71/predictions.json'):
        assert tuple(r['gold_profile']) in profiles
        byword[r['word']].append(dict(sid=r['sid'],index=r['index'],gold_profile=r['gold_profile'],context=collapse(model,posterior(model,r['context']),profiles).tolist(),shuffle=collapse(model,posterior(model,r['shuffled_context']),profiles).tolist(),prior=prior.tolist()))
    groups=[dict(word=w,occurrences=oo) for w,oo in sorted(byword.items())];save(OUT/'pooled-inputs.json',dict(profiles=profiles,groups=groups))
    records=[json.loads(line) for line in INVENTORY.open()];forms=[r['surface'] for r in records];assert len(forms)==len(set(forms))==100000;formindex={w:i for i,w in enumerate(forms)}
    dictionary=[readings([dict(pos=p,features=f) for p,_,f in r['signatures']]) for r in records]
    queries=sorted({tuple(o['gold_profile']) for g in groups for o in g['occurrences']});support={}
    for mode,fn in [('tolerant',compatible),('strict',strict_compatible)]:
        for q in queries:support[mode,q]={i for i,rr in enumerate(dictionary) if any(fn(q,r) for r in rr)}
    rows=[]
    for g in groups:
        w=g['word'];occ=g['occurrences'];qs=[tuple(o['gold_profile']) for o in occ];r=dict(word=w,tokens=len(occ),distinct_profiles=len(set(qs)),inventory_present=w in formindex)
        for mode in ('tolerant','strict'):
            first=support[mode,qs[0]];pool=set(first)
            for q in qs[1:]:pool.intersection_update(support[mode,q])
            gold=formindex.get(w);ranked=sorted(pool,key=lambda i:(-model['frequency'].get(forms[i],0),forms[i]));survives=gold in pool
            r[mode]=dict(first_size=len(first),size=len(pool),gold_survives=survives,gold_rank=ranked.index(gold)+1 if survives else None,unique_candidate=forms[next(iter(pool))] if len(pool)==1 else None)
        rows.append(r)
    save(OUT/'oracle-pools.json',rows);save(OUT/'prediction-freeze.json',dict(inputs={str(p):digest(p) for p in (OUT/'oracle-pools.json',OUT/'pooled-inputs.json')}))
    result=dict(oracle=oracle_summary(rows),inferred_pooling=pooling_metrics(groups,profiles,prior),search_run=False,nuclei_measured=False,scope='Oracle identifiability plus contextual grammaticalclasses only; not blind wordrestoration.');save(OUT/'evaluation.json',result);print(json.dumps(result,indent=2))
if __name__=='__main__':run()
