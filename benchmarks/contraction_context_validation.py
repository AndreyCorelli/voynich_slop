"""Independently reproduce saved context scores, selections and group invariance."""
from collections import Counter
import json
import math
from pathlib import Path

from benchmarks import contraction_context_ranking as study
from benchmarks.contraction_hidden_validation import independent_decode
from benchmarks.l3_conflict import verify
from voynich_smt.data.corpus import digest,write_json
from voynich_smt.experiments.hidden import HiddenRecoveryRequest


def grouping(case,result):
    required=sorted({u for w in case['held_units']['words'] for u in w})
    signature={}
    for u in required:
        outputs=[independent_decode(code,result['encoder']) for code in case['truth']['encoder']['codebook'][u]]
        signature[u]=all(x is not None and len(x)==1 for x in outputs) and outputs[0]==outputs[1]
    return signature


def independent_score(candidate,model,expansions):
    words=[''.join(expansions.get(u,u) for u in w) for w in candidate['result']['plaintext']['words'][:32]]
    assert len(words)==32
    counts=model['counts'];v=len(counts)+1;denom=sum(counts.values())+v
    pairs={(a,b):n for a,b,n in model['pairs']}
    probabilities=[(counts.get(words[0],0)+1)/denom]
    for a,b in zip(words,words[1:]):
        probabilities.append(((counts.get(b,0)+1)/denom+(pairs.get((a,b),0)+1)/(model['outgoing'].get(a,0)+v))/2)
    return sum(map(math.log,probabilities))/32


def validate():
    p=study.prepare();old=study.prior.prepare();raw=json.loads(study.prior.prior.SOURCE.read_text())
    stages={i:json.loads((study.OUT/f'iteration-{i}.json').read_text()) for i in range(1,8)}
    report=json.loads((study.OUT/'report.json').read_text())
    assert report['complete'] and report['prepared_sha256']==digest(p)
    assert digest(old)==p['prior_sha256']
    score_checks=0;witness_checks=0;group_checks=0
    for source,model in p['models'].items():
        f=old['fixtures'][source];segment=raw['sources'][source]['segments'][f['segment_index']][:f['reference_range'][1]]
        counts=Counter(w for w in segment if w is not None)
        pairs=Counter()
        for i in range(1,len(segment)):
            if segment[i-1] is not None and segment[i] is not None:pairs[segment[i-1],segment[i]]+=1
        assert dict(counts)==model['counts']
        assert [[a,b,n] for (a,b),n in sorted(pairs.items())]==model['pairs']
        outgoing=Counter()
        for (a,b),n in pairs.items():outgoing[a]+=n
        assert dict(outgoing)==model['outgoing']
    for i,stage in stages.items():
        assert stage['plan']['prepared_sha256']==digest(p)
        if i>1:assert stage['plan']['previous_sha256']==digest(stages[i-1])
        if i in (2,3,4,5):
            row=stage['rows'][0];source=row['source'];pool=p['pools'][source]
            case=old['cases'][source]['contracted'];q=HiddenRecoveryRequest.from_dict(case['request'])
            values=[];signature=grouping(case,pool['candidates'][0]['result'])
            for j,candidate in enumerate(pool['candidates']):
                verify(q,candidate['result']);witness_checks+=1
                value=independent_score(candidate,p['models'][source],p['expansions']);values.append(value)
                assert math.isclose(value,row['scores'][j],abs_tol=1e-12);score_checks+=1
                assert grouping(case,candidate['result'])==signature;group_checks+=len(signature)
            order=sorted(range(len(values)),key=lambda j:(-values[j],j))
            assert order==row['order'] and row['selected_index']==order[0]
            assert row['context_exact']==pool['evaluations'][order[0]]['exact']
            assert row['first_exact']==pool['evaluations'][0]['exact']
            assert row['unigram_exact']==pool['evaluations'][pool['selected_index']]['exact']
            assert row['selected_index']==pool['selected_index'],'Observed same selections as unigram'
        if i==6:
            for row in stage['rows']:
                source=row['source'];proof=p['proofs'][source]
                candidates=[{'result':proof['generating']}]+proof['alternatives']
                values=[];q=HiddenRecoveryRequest.from_dict(old['cases'][source]['contracted']['request'])
                for j,candidate in enumerate(candidates):
                    verify(q,candidate['result']);witness_checks+=1
                    value=independent_score(candidate,p['models'][source],p['expansions']);values.append(value)
                    assert math.isclose(value,row['scores'][j],abs_tol=1e-12);score_checks+=1
                order=sorted(range(len(values)),key=lambda j:(-values[j],j))
                assert row['order']==order and row['generating_rank']==order.index(0)+1
        if i==7:
            for row in stage['rows']:
                source=row['source'];pool=p['pools'][source];case=old['cases'][source]['contracted']
                selected=0 if row['selector']=='first' else pool['selected_index'] if row['selector']=='unigram' else stages[{'caesar':2,'aquinas':3,'einhard':4,'caroli':5}[source]]['rows'][0]['selected_index']
                signature=grouping(case,pool['candidates'][selected]['result'])
                assert row['grouped']==sum(signature.values())
                assert {r['generating_unit']:r['both_codes_grouped_as_one_unit'] for r in row['ownership']}==signature
    totals=stages[7]['assessment']
    assert totals['context_total_exact']==totals['first_total_exact']==totals['unigram_total_exact']==28
    result={'verified':True,'independent_context_scores':score_checks,'sat_witness_checks':witness_checks,
        'homophone_group_invariance_checks':group_checks,'solver_calls':0,
        'code_sha256':digest(Path(__file__).read_text()),
        'limitation':'Ranking specificity not evaluated: prior shuffles supply no candidate keys. Constructive true-key capacity check remains truth-assisted.'}
    write_json(study.OUT/'validation.json',result);print(json.dumps(result));return result


if __name__=='__main__':validate()
