"""Annotation-dependent sampling utilities for diagnostic decoder confusions."""
from collections import defaultdict
import math


def pair_record(stream,index,child,parent,author):
    left,right=sorted((child,parent));distance=right-left
    return {'stream':index,'child':child,'parent':parent,'left':left,'right':right,'author':author,
        'token_distance':distance,'predicate_gap':abs(stream['finite'].index(child)-stream['finite'].index(parent)),
        'distance_bucket':distance.bit_length()-1}


def matched_pairs(positives,negatives):
    """One-to-one author/exact-gap/log-distance-bin matching; no label features."""
    pools=defaultdict(list)
    key=lambda r:(r['author'],r['predicate_gap'],r['distance_bucket'])
    for i,p in enumerate(positives):pools[key(p)].append(i)
    used=set();matches=[];unmatched=[]
    for j,n in sorted(enumerate(negatives),key=lambda x:(key(x[1]),x[1]['stream'],x[1]['child'],x[1]['parent'])):
        candidates=[i for i in pools[key(n)] if i not in used]
        if not candidates:unmatched.append(j);continue
        def order(i):
            p=positives[i]
            return (abs(math.log(p['token_distance']/n['token_distance'])),p['stream'],p['left'],p['right'])
        i=min(candidates,key=order);used.add(i)
        matches.append({'positive_index':i,'negative_index':j,'positive':positives[i],'negative':n,
            'log_distance_difference':abs(math.log(positives[i]['token_distance']/n['token_distance']))})
    return {'matches':matches,'unmatched_negative_indices':unmatched,'unused_positive_indices':[i for i in range(len(positives)) if i not in used]}


def same_child_contrasts(positives,negatives):
    positive={(r['stream'],r['child']):r for r in positives};result=[]
    for n in negatives:
        p=positive.get((n['stream'],n['child']))
        if p is None:continue
        result.append({'positive':p,'negative':n,
            'distance_matched':p['predicate_gap']==n['predicate_gap'] and p['distance_bucket']==n['distance_bucket'],
            'factor_two_caliper':p['predicate_gap']==n['predicate_gap'] and abs(math.log(p['token_distance']/n['token_distance']))<=math.log(2)})
    return result
