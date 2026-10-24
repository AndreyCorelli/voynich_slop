"""Frozen fresh-test evaluation of distributional classes and partial forests."""
from collections import Counter
import hashlib
import numpy as np
from benchmarks.grammar_distributional_skeleton_iteration24 import OUT,ARMS,load,save,phase_views,relation_matrix,property_label,readout_key
from benchmarks.grammar_cipher_relations_iteration23_evaluate import prf,fingerprint
from voynich_smt.cipher_relations import probabilities,LABELS,RADIUS
from voynich_smt.distributional_grammar import attach_profiles,consensus,skeleton


def fragments(edges):
    subjects={};objects={}
    for c,p,label,*_ in edges:
        if label==1:subjects.setdefault(p,set()).add(c)
        if label==2:objects.setdefault(p,set()).add(c)
    return {(s,h,o) for h,ss in subjects.items() for s in ss for o in objects.get(h,()) if s!=o}


def counts(rows,sentences):
    output=[]
    for r,s in zip(rows,sentences):
        pred={tuple(e[:3]) for e in r};gold=set(map(tuple,s['edges']));output.append([len(pred&gold),len(pred),len(gold)])
    return np.asarray(output,dtype=int)


def metrics(rows,sentences):
    total=counts(rows,sentences).sum(axis=0);result={'micro':prf(*total),'per_relation':{}}
    if not total[1]:result['micro']['precision']=None
    for label in range(1,len(LABELS)):
        p=[[e for e in r if e[2]==label] for r in rows];g=[{**s,'edges':[e for e in s['edges'] if e[2]==label]} for s in sentences]
        a=counts(p,g).sum(axis=0);score=prf(*a)
        if not a[1]:score['precision']=None
        result['per_relation'][LABELS[label]]=score
    tp=pred=gold=0
    for r,s in zip(rows,sentences):
        p=fragments(r);g=fragments(s['edges']);tp+=len(p&g);pred+=len(p);gold+=len(g)
    result['shared_head_subject_object']=prf(tp,pred,gold)
    if not pred:result['shared_head_subject_object']['precision']=None
    result['dependent_token_coverage']=sum(len(r) for r in rows)/sum(len(s['tokens']) for s in sentences)
    result['radius_reachable_gold']=sum(abs(c-p)<=RADIUS for s in sentences for c,p,label in s['edges'])
    result['sentences_with_cycle']=0
    for row in rows:
        heads={e[0]:e[1] for e in row};cyclic=False
        for start in heads:
            seen=set();current=start
            while current in heads:
                if current in seen:cyclic=True;break
                seen.add(current);current=heads[current]
        result['sentences_with_cycle']+=cyclic
    return result


def readout_metrics(sentences,vv,arm,model):
    result={}
    for property,readout in model.items():
        true=[];pred=[]
        for s,v in zip(sentences,vv):
            for pos in range(len(s['tokens'])):
                label=property_label(s,pos,property)
                if label is None:continue
                true.append(label);pred.append(readout['mapping'].get(readout_key(v,pos,arm),readout['majority']))
        labels=sorted(set(true));result[property]=dict(queries=len(true),accuracy=sum(a==b for a,b in zip(true,pred))/len(true),
            balanced_accuracy=float(np.mean([sum(a==b for a,b in zip(true,pred) if a==label)/true.count(label) for label in labels])),
            majority_accuracy=true.count(readout['majority'])/len(true),majority_balanced_accuracy=1/len(labels),
            source_class_counts=dict(Counter(true)))
    return result


def comparison(first,second,sentences):
    a=counts(first,sentences);b=counts(second,sentences);rng=np.random.default_rng(24024);differences=[]
    f1=lambda x:2*x[0]/max(1,x[1]+x[2])
    for _ in range(1000):
        chosen=rng.integers(len(sentences),size=len(sentences));differences.append(f1(a[chosen].sum(axis=0))-f1(b[chosen].sum(axis=0)))
    return dict(delta_f1=float(f1(a.sum(axis=0))-f1(b.sum(axis=0))),sentence_bootstrap_95=[float(x) for x in np.quantile(differences,[.025,.975])],replicates=1000)


def score_phase(data,split,lattice,models,prototypes,readouts,key=None):
    raw,offset=phase_views(data,split,lattice,key=key);results={};predictions=[];matrices={};scored={}
    for arm in ARMS:
        vv=attach_profiles(raw,prototypes[arm],shuffle=arm=='shuffled_profiles')[offset:] if arm in prototypes else raw[offset:]
        x,_,slices,pairs=relation_matrix(data[split],vv,arm);matrices[arm]=fingerprint(x)
        probs=[probabilities(x,m) for m in models[arm]['members']]
        agreed=[consensus(pair,[p[a:b] for p in probs]) for (a,b),pair in zip(slices,pairs)]
        result={}
        for mode,policy in models[arm]['operating'].items():
            rows=[skeleton(r,policy['threshold'],policy['margin']) for r in agreed] if policy['enabled'] else [[] for r in agreed]
            scored[arm,mode]=rows;result[mode]=dict(calibration_enabled=policy['enabled'],**metrics(rows,data[split]))
            for s,r in zip(data[split],rows):predictions.append(dict(split=split,arm=arm,mode=mode,sent_id=s['sent_id'],edges=r))
        if arm!='dictionary':result['class_readout']=readout_metrics(data[split],vv,arm,readouts[arm])
        results[arm]=result
    results['paired_f1_comparisons']={f'{a}-minus-{b}':comparison(scored[a,'f1'],scored[b,'f1'],data[split]) for a,b in [('profiles','baseline'),('profiles','shuffled_profiles'),('dictionary','profiles')]}
    return results,predictions,matrices


def run():
    if (OUT/'evaluation.json').exists():raise ValueError('Preserve fresh-test scores')
    for p,h in load(OUT/'fit-freeze.json')['inputs'].items():assert hashlib.sha256(open(p,'rb').read()).hexdigest()==h,p
    data=load(OUT/'datasets.json');lattice=load(OUT/'morphology-lattice.json');models=load(OUT/'models.json');prototypes=load(OUT/'prototypes.json');readouts=load(OUT/'readouts.json')
    output={};predictions=[];rekeys=[]
    for split in ('test_jerome','test_caesar'):
        scores,rows,hashes=score_phase(data,split,lattice,models,prototypes,readouts);output[split]=scores;predictions.extend(rows)
        # Rebuild all anonymous profiles under a fresh key, including the
        # within-sentence shuffled control. Keys are not extra test samples.
        _,newrows,newhashes=score_phase(data,split,lattice,models,prototypes,readouts,key=607)
        assert hashes==newhashes and rows==newrows
        rekeys.append(dict(split=split,key=607,matrices=hashes,identical_predictions=True))
        print(split,{a:round(scores[a]['f1']['micro']['f1'],4) for a in ARMS},flush=True)
        print('precision .7',{a:(scores[a]['precision_0.7']['micro']['predicted'],scores[a]['precision_0.7']['micro']['precision']) for a in ARMS},flush=True)
    save(OUT/'evaluation.json',output);save(OUT/'predictions.json',predictions);save(OUT/'rekey-checks.json',rekeys)

if __name__=='__main__':run()
