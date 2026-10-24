"""Public-only confidence features and held-out synthetic calibration.

No word identities/spelling, POS, original boundaries or topic labels are features.
Probability claims require independent confirmation, not just a fitted model.
"""
from collections import Counter
import gzip
import json
import math
import numpy as np

from voynich_smt.data.corpus import digest
from .data import CipherStream
from .inventory import Inventory
from .trigram import load_model
from .sparse_lm import BOS

FEATURES=('agreement','log_public_frequency','log_rank_fraction','changed_fraction',
          'archive_stability','log_source_frequency','absolute_frequency_gap',
          'context_log_lift','context_log_probability')


def signature(inference):
    p=inference['protocol'];retrieval=dict(p['retrieval']);retrieval.setdefault('attested_mix',0.)
    return {'model':p['model_sha256'],'inventory':p['inventory_sha256'],'search':p['search'],
            'retrieval':retrieval,'runs':len(inference['runs']),'features':FEATURES}


def extract(resources,root):
    inference=json.loads((root/'inference.json').read_text());stream=CipherStream.load(root/'public/cipher.json')
    assert stream.identity==inference['protocol']['cipher_sha256']
    counts=Counter(c for d in stream.documents for c in d);total=sum(counts.values())
    order=sorted(counts,key=lambda c:(-counts[c],c));rank={c:i+1 for i,c in enumerate(order)}
    keys=[r['joint_archive'][0]['assignments'] for r in inference['runs']];initial=[]
    for run in inference['runs']:
        with gzip.open(root/f"traces/seed-{run['seed']}.jsonl.gz",'rt') as handle:first=json.loads(next(handle))
        assert first['kind']=='initial';initial.append(first['assignments'])
    inventory=Inventory(resources/'inventory.sqlite')
    try:
        model=load_model(resources/'model.sqlite',inventory)
        assert model.identity==inference['protocol']['model_sha256'] and inventory.identity==inference['protocol']['inventory_sha256']
        chosen={};supporters={}
        for c in counts:
            votes=Counter(k[c] for k in keys);word,n=min(votes.items(),key=lambda p:(-p[1],p[0]))
            if n>len(keys)/2 and n>=2:
                chosen[c]=(word,n);supporters[c]=[i for i,k in enumerate(keys) if k[c]==word]
        lifts=Counter();logps=Counter();observations=Counter()
        for i,key in enumerate(keys):
            for doc in stream.documents:
                for pos,c in enumerate(doc):
                    if c not in chosen or i not in supporters[c]:continue
                    word=key[c];left=BOS if pos==0 else key[doc[pos-1]]
                    right=model.eos if pos+1==len(doc) else key[doc[pos+1]]
                    a=math.log(model.probability(left,word));b=math.log(model.probability(word,right))
                    lifts[c]+=a-math.log(model.base_probability(word))+b-math.log(model.base_probability(right))
                    logps[c]+=a+b;observations[c]+=2
        rows=[]
        for c,(word,n) in chosen.items():
            public=math.log(counts[c]/total);source=math.log(model.base_probability(word))
            stability=sum(sum(e['assignments'][c]==word for e in r['joint_archive'])/len(r['joint_archive']) for r in inference['runs'])/len(keys)
            features=[n/len(keys),public,math.log(rank[c]/len(counts)),
                      sum(initial[i][c]!=word for i in supporters[c])/len(supporters[c]),stability,source,
                      abs(public-source),lifts[c]/observations[c],logps[c]/observations[c]]
            rows.append({'cipher':c,'word_id':word,'votes':n,'count':counts[c],'features':features})
        return {'scope':'Public-only majority candidates; no truth/word identities in features',
                'cipher_sha256':stream.identity,'inference_sha256':digest(inference),'signature':signature(inference),
                'feature_names':FEATURES,'rows':rows,'total_tokens':total,'total_types':stream.type_count}
    finally:inventory.close()


def truth_labels(public,truth,inventory):
    if public['cipher_sha256']!=truth['public_sha256']:raise ValueError('Confidence truth mismatch')
    return np.asarray([inventory.word(r['word_id'])==truth['decoding'][r['cipher']] for r in public['rows']],dtype=float)


def fit(public,labels):
    from scipy.optimize import minimize
    from scipy.special import expit
    x=np.asarray([r['features'] for r in public['rows']],dtype=float);y=np.asarray(labels,dtype=float)
    if len(y)!=len(x) or not len(x) or not np.isin(y,[0,1]).all():raise ValueError('Invalid calibration labels')
    mean=x.mean(axis=0);scale=x.std(axis=0);scale[scale<1e-10]=1
    z=(x-mean)/scale;design=np.column_stack((np.ones(len(z)),z))
    start=np.zeros(design.shape[1]);start[0]=math.log((y.sum()+.5)/(len(y)-y.sum()+.5))
    def objective(beta):
        logits=design@beta
        loss=np.logaddexp(0,logits).sum()-y@logits+.5*(beta[1:]@beta[1:])
        grad=design.T@(expit(logits)-y);grad[1:]+=beta[1:]
        return float(loss),grad
    result=minimize(objective,start,jac=True,method='L-BFGS-B',bounds=[(-20,20)]*len(start),options={'maxiter':500,'ftol':1e-12})
    if not result.success:raise ValueError(f'Calibration fit failed: {result.message}')
    return {'format':'confidence-logistic-v1','signature':public['signature'],'feature_names':FEATURES,
            'mean':mean.tolist(),'scale':scale.tolist(),'coefficients':result.x.tolist(),
            'training_public_sha256':digest(public),'training_types':len(y),'positive_types':int(y.sum()),
            'l2':1.,'training_scope':'Synthetic calibration work only; no confirmation or Caesar labels',
            'base_prevalence':float(y.mean())}


def predict(calibrator,public):
    from scipy.special import expit
    if digest(calibrator['signature'])!=digest(public['signature']):raise ValueError('Confidence method signature differs')
    if not public['rows']:return np.asarray([])
    x=np.asarray([r['features'] for r in public['rows']],dtype=float)
    z=(x-np.asarray(calibrator['mean']))/np.asarray(calibrator['scale']);coef=np.asarray(calibrator['coefficients'])
    return expit(coef[0]+z@coef[1:])


def wilson(hits,n,z=1.959963984540054):
    if not n:return [None,None]
    p=hits/n;den=1+z*z/n;middle=(p+z*z/(2*n))/den
    half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return [max(0.,middle-half),min(1.,middle+half)]


def evaluate(public,labels,probabilities):
    y=np.asarray(labels,dtype=float);p=np.asarray(probabilities,dtype=float)
    if len(y)!=len(public['rows']) or len(p)!=len(y):raise ValueError('Calibration evaluation size mismatch')
    def measured(indices):
        indices=list(indices);hits=int(y[indices].sum());tokens=sum(public['rows'][i]['count'] for i in indices)
        return {'types':len(indices),'correct_types':hits,'type_precision':hits/len(indices) if indices else None,
                'precision_wilson_95':wilson(hits,len(indices)),'tokens':tokens,'token_coverage':tokens/public['total_tokens'],
                'correct_token_coverage':sum(public['rows'][i]['count'] for i in indices if y[i])/public['total_tokens']}
    order=sorted(range(len(p)),key=lambda i:(-p[i],-public['rows'][i]['count'],public['rows'][i]['cipher']))
    usual=sorted(range(len(p)),key=lambda i:(-public['rows'][i]['votes'],-public['rows'][i]['count'],public['rows'][i]['cipher']))
    clipped=np.clip(p,1e-12,1-1e-12)
    return {'scope':'Literal type precision among majority-only candidates; confidence requires held-out validation',
            'candidate_types':len(y),'positive_types':int(y.sum()),
            'brier':float(np.mean((p-y)**2)) if len(y) else None,
            'log_loss':float(-np.mean(y*np.log(clipped)+(1-y)*np.log1p(-clipped))) if len(y) else None,
            'top':{str(k):measured(order[:k]) for k in (10,20,50)},
            'usual_top':{str(k):measured(usual[:k]) for k in (10,20,50)},
            'thresholds':{str(t):measured(np.flatnonzero(p>=t)) for t in (.5,.8,.95)},
            'rows':[{'cipher':public['rows'][i]['cipher'],'word_id':public['rows'][i]['word_id'],
                     'probability':float(p[i]),'correct':bool(y[i])} for i in order]}
