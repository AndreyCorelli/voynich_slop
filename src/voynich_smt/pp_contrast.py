"""Source-trained, smoothed PP contrast scores over explicit candidate analyses.

Oracle POS/morphology and plaintext preposition identity are inputs here. No
reference attachment or reference boundary enters the scoring API.
"""
from collections import Counter,defaultdict
import math


def features(tokens,candidate):
    p,h,left,right=candidate['prep'],candidate['head'],candidate['left'],candidate['right']
    case=candidate.get('case',tokens[h]['case']) or '_'
    modifiers=[t for i,t in enumerate(tokens[left:right+1],left) if i not in (p,h) and t['pos'] in ('ADJ','DET')]
    agreement=[]
    for t in modifiers:
        for key in ('case','number','gender'):
            head=case if key=='case' else tokens[h][key]
            if head and t[key]:agreement.append(head==t[key])
    return dict(prep=tokens[p]['word'],case=case,distance=str(min(8,abs(p-h))),
                boundary=' '.join('P' if i==p else 'H' if i==h else t['pos'] for i,t in enumerate(tokens[left:right+1],left)),
                agreement='none' if not agreement else ('match' if all(agreement) else 'mismatch'))


def train(examples):
    counts={k:Counter() for k in ('case','distance','boundary','agreement')};government=defaultdict(Counter)
    for tokens,candidate in examples:
        f=features(tokens,candidate)
        for k in counts:counts[k][f[k]]+=1
        government[f['prep']][f['case']]+=1
    return dict(counts={k:dict(v) for k,v in counts.items()},government={k:dict(v) for k,v in government.items()})


def logp(counts,value):
    # An explicit OTHER bucket makes this a normalized categorical model.
    return math.log((counts.get(value,0)+.5)/(sum(counts.values())+.5*(len(counts)+1)))


def score(model,tokens,candidate):
    f=features(tokens,candidate);c=model['counts'];gov=model['government'].get(f['prep'],{})
    # Government uses a fixed case vocabulary, including unseen cases.
    cases=('Nom','Acc','Gen','Dat','Abl','Loc','Voc','_')
    government=math.log((gov.get(f['case'],0)+.5)/(sum(gov.values())+.5*len(cases)))
    parts=dict(government=government,distance=logp(c['distance'],f['distance']),boundary=logp(c['boundary'],f['boundary']),agreement=logp(c['agreement'],f['agreement']))
    return dict(components=parts,structural=sum(parts.values()),local=logp(c['case'],f['case'])+parts['distance'])
