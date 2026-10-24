"""Paired context-versus-random comparison; no settings selected."""
import numpy as np
from benchmarks.grammar_candidate_expansion_iteration36 import OUT,load,save
from benchmarks.grammar_candidate_expansion_iteration36_evaluate import bootstrap


def run():
    if (OUT/'comparisons.json').exists():raise ValueError('Preserve comparisons')
    e=load(OUT/'evaluation.json');output=[]
    for arm in ('word','ending'):
        for rate in (.1,.5):
            context=sorted([r for r in e['cells'] if r['arm']==arm and r['rate']==rate and r['strategy']=='context' and r['k']==2],key=lambda r:r['mask_seed'])
            random=sorted([r for r in e['cells'] if r['arm']==arm and r['rate']==rate and r['strategy']=='random' and r['k']==2],key=lambda r:r['mask_seed'])
            differences=[dict(sentence_tokens=a['sentence_tokens'],sentence_delta=(np.array(a['sentence_delta'])-np.array(b['sentence_delta'])).tolist()) for a,b in zip(context,random)]
            net=sum(sum(r['sentence_delta']) for r in differences);row=dict(arm=arm,rate=rate,net_query_tags_context_minus_random=net,accuracy_difference=net/(5*473),bootstrap=bootstrap(differences));output.append(row);print(row)
    save(OUT/'comparisons.json',output)

if __name__=='__main__':run()
