"""Frozen word-context ranking and separate ownership audit on saved keys."""
from collections import Counter
import json
import math
from pathlib import Path

from benchmarks import contraction_coverage_calibration as prior
from benchmarks.contraction_coverage_validation import ownership
from voynich_smt.data.corpus import digest, write_json

OUT=Path('experiments/results/contraction-context-ranking')


def model_for(words):
    counts=Counter(w for w in words if w is not None)
    pairs=Counter((a,b) for a,b in zip(words,words[1:]) if a is not None and b is not None)
    outgoing=Counter()
    for (a,b),n in pairs.items():outgoing[a]+=n
    return {'counts':dict(counts),'tokens':sum(counts.values()),'outgoing':dict(outgoing),
            'pairs':[[a,b,n] for (a,b),n in sorted(pairs.items())],'weight':0.5,'alpha':1}


def context_score(words,model):
    if not words:raise ValueError('Empty score sequence')
    v=len(model['counts'])+1;denom=model['tokens']+v
    pairs={(a,b):n for a,b,n in model['pairs']}
    value=0
    for i,w in enumerate(words):
        unigram=(model['counts'].get(w,0)+1)/denom
        probability=unigram
        if i:
            a=words[i-1]
            conditional=(pairs.get((a,w),0)+1)/(model['outgoing'].get(a,0)+v)
            probability=(1-model['weight'])*unigram+model['weight']*conditional
        value+=math.log(probability)
    return value/len(words)


def select(candidates,model,expansions):
    # No truth, key ownership, carriers or continuation enter ranking.
    scores=[context_score([prior.prior.expand(w,expansions) for w in c['result']['plaintext']['words'][:32]],model) for c in candidates]
    order=sorted(range(len(scores)),key=lambda i:(-scores[i],i))
    return scores,order


def prepare():
    p=prior.prepare();raw=json.loads(prior.prior.SOURCE.read_text())
    models={}
    for source,f in p['fixtures'].items():
        stream=raw['sources'][source]['segments'][f['segment_index']]
        models[source]=model_for(stream[:f['reference_range'][1]])
    pools={};proofs={}
    for source,stage in [('caesar',2),('aquinas',3),('einhard',4),('caroli',7)]:
        r=json.loads((prior.OUT/f'iteration-{stage}.json').read_text())
        first=next(x for x in r['rows'] if x['name']=='contracted-positive')['result']
        # Reuse exact frequency candidate pools; no proposal expansion.
        ranking_stage=7 if source=='caroli' else 6
        ranked=json.loads((prior.OUT/f'iteration-{ranking_stage}.json').read_text())
        pool=next(x for x in ranked['ranked'] if x['source']==source)
        assert pool['candidates'][0]['result']==first
        pools[source]=pool
    proof_stage=json.loads((prior.OUT/'iteration-5.json').read_text())
    for row in proof_stage['proofs']:proofs[row['source']]=row
    result={'prior_sha256':digest(p),'prior_report_sha256':digest(json.loads((prior.OUT/'report.json').read_text())),
        'models':models,'pools':pools,'proofs':proofs,'expansions':p['expansions'],
        'code_sha256':digest(Path(__file__).read_text()),
        'protocol':'Seven stages: freeze actual adjacent reference words, barrier-aware interpolated add-one bigram/unigram weight0.5 without tuning; stages2-5 rerank identical recovered pools on Caesar/Aquinas/Einhard/Caroli;6 separately rank truth-assisted proof pools to diagnose scorer capacity, never inject into recovery;7 audit all true homophone alternatives and control specificity limit. Score original32 natural training words, exclude carriers and holdout. Stable first ties; no solver calls, new keys, grouping oracle, vocabulary/rule/budget changes. Retrospective three prior passages plus already-examined Caroli; not new blind validation. Four prior shuffle UNSATs supply no fitted keys, so ranking specificity not evaluated.'}
    result=json.loads(json.dumps(result));path=OUT/'prepared.json'
    if path.exists():assert json.loads(path.read_text())==result,'Frozen source/code changed'
    else:write_json(path,result)
    return result


def run():
    p=prepare();old=prior.prepare();stages={}
    for i in range(1,8):
        path=OUT/f'iteration-{i}.json'
        if path.exists():stages[i]=json.loads(path.read_text());continue
        plan={'iteration':i,'prepared_sha256':digest(p),'previous_sha256':digest(stages[i-1]) if i>1 else None}
        rows=[]
        if i==1:
            plan['purpose']='Freeze barrier-preserving full-vocabulary adjacent-word priors; no outcome-based weight tuning'
            assessment={'sources':{s:{'tokens':m['tokens'],'pairs':sum(x[2] for x in m['pairs'])} for s,m in p['models'].items()},'decision':'Test exact existing recovered-key pools'}
        elif i in (2,3,4,5):
            source={2:'caesar',3:'aquinas',4:'einhard',5:'caroli'}[i];plan['source']=source
            plan['purpose']='Context versus unigram versus first key; candidate pool unchanged'
            pool=p['pools'][source];scores,order=select(pool['candidates'],p['models'][source],p['expansions']);selected=order[0]
            # Selection frozen before evaluation metadata inspected.
            ev=pool['evaluations']
            rows=[{'source':source,'scores':scores,'order':order,'selected_index':selected,
                'first_exact':ev[0]['exact'],'unigram_exact':ev[pool['selected_index']]['exact'],
                'context_exact':ev[selected]['exact'],'novel_exact':ev[selected]['novel_plaintext_exact'],
                'selected_swap':pool['candidates'][selected]['swap'], 'candidate_count':len(scores)}]
            assessment={'result':rows[0],'decision':'Keep model fixed; evaluate next source; do not tune to missed words'}
        elif i==6:
            plan['purpose']='Truth-assisted score-capacity check on constructive ownership alternatives, separate from recovery'
            for source,proof in p['proofs'].items():
                candidates=[{'result':proof['generating']}]+proof['alternatives']
                scores,order=select(candidates,p['models'][source],p['expansions'])
                rows.append({'source':source,'scores':scores,'order':order,'generating_rank':order.index(0)+1,
                    'candidate_count':len(candidates),'scope':'Injected generating key capacity diagnostic, not hidden recovery'})
            assessment={'rows':rows,'decision':'Separate candidate availability and score discrimination; inspect grouping without supplying oracle constraints'}
        else:
            plan['purpose']='Independent grouping audit and final decision; assess unavailable ranking controls explicitly'
            for source,pool in p['pools'].items():
                context_row=stages[{ 'caesar':2,'aquinas':3,'einhard':4,'caroli':5}[source]]['rows'][0]
                for label,index in [('first',0),('unigram',pool['selected_index']),('context',context_row['selected_index'])]:
                    result=pool['candidates'][index]['result'];owners=ownership(old['cases'][source]['contracted'],result)
                    rows.append({'source':source,'selector':label,'grouped':sum(r['both_codes_grouped_as_one_unit'] for r in owners),
                        'correct':sum(r['correct_ownership'] for r in owners),'target_units':len(owners),
                        'ownership':owners,'exact':pool['evaluations'][index]['exact']})
            assessment={'context_total_exact':sum(stages[j]['rows'][0]['context_exact'] for j in range(2,6)),
                'first_total_exact':sum(stages[j]['rows'][0]['first_exact'] for j in range(2,6)),
                'unigram_total_exact':sum(stages[j]['rows'][0]['unigram_exact'] for j in range(2,6)),
                'control_specificity':'NOT_EVALUATED_NO_FITTED_SHUFFLE_KEYS',
                'decision':'Stop7. Interpret word-context discrimination and grouping separately; no manuscript inference or timeout escalation.'}
        write_json(OUT/f'plan-{i}.json',plan)
        row={'plan':plan,'rows':rows,'assessment':assessment};write_json(path,row);stages[i]=json.loads(path.read_text())
        print('Stage',i,json.dumps(assessment),flush=True)
    write_json(OUT/'report.json',{'prepared_sha256':digest(p),'complete':True,'solver_calls':0,
        'assessment':stages[7]['assessment'],'iterations':7})
    return stages


if __name__=='__main__':run()
