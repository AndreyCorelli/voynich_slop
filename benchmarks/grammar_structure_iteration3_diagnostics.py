"""Audit root collapse, ambiguity proxies, source independence and robustness."""
from collections import Counter
from dataclasses import asdict
import hashlib
import json
import math
from pathlib import Path
import random
from statistics import mean

from benchmarks.grammar_structure_iteration3 import OUT,read_conllu,combine,TREEBANKS
from voynich_smt.data.corpus import write_json,digest


def prf_counts(rows,key):
    tp=sum(r[key]['tp'] for r in rows);den=sum(r[key]['predicted']+r[key]['gold'] for r in rows)
    return 2*tp/den if den else 0


def bootstrap(rows,seed=20261021):
    rng=random.Random(seed);values=[]
    for _ in range(1000):values.append(prf_counts(rng.choices(rows,k=len(rows)),'predicates'))
    values.sort();return [values[24],values[974]]


def uncertainty(prediction):
    probabilities=prediction['predicate_probabilities']
    entropy=mean(-p*math.log(max(p,1e-12))-(1-p)*math.log(max(1-p,1e-12)) for p in probabilities)
    candidates=[probabilities[i] for i in prediction['finite_candidates']]
    candidate_entropy=mean(-p*math.log(max(p,1e-12))-(1-p)*math.log(max(1-p,1e-12)) for p in candidates) if candidates else None
    margins=[]
    for rows in prediction['arc_candidates'].values():
        ordered=sorted([r['logit'] for r in rows],reverse=True)
        if len(ordered)>1:margins.append(ordered[0]-ordered[1])
    return {'mean_binary_entropy':entropy,'finite_candidate_entropy':candidate_entropy,
            'mean_arc_logit_margin':mean(margins) if margins else None}


def run():
    load=lambda name:json.loads((OUT/name).read_text())
    rows=load('predictions.json');truth={r['id']:r for r in load('evaluation-only-truth.json')};corrupt=load('corruption.json')
    source,_=read_conllu(TREEBANKS/'proiel-r2.17/la_proiel-ud-train.conllu','proiel')
    selected=[]
    for author in ['Jerome','Palladius']:selected += [s for s in source if s['author']==author][:400]
    training=[combine(selected[i:i+3]) for i in range(0,len(selected),3) if len({s['author'] for s in selected[i:i+3]})==1]
    source_shingles={tuple(s['tokens'][i:i+12]) for s in training for i in range(max(0,len(s['tokens'])-11))}
    output=[]
    for author in ['Cicero','Sallust','Suetonius']:
        chosen=[r for r in rows if r['author']==author and r['mode']=='latent'];gold=[truth[r['id']] for r in chosen]
        pred=[r['prediction'] for r in chosen]
        denominator=sum(len(g['finite']) for g in gold)
        candidate_hits=sum(len(set(g['finite'])&set(p['finite_candidates'])) for g,p in zip(gold,pred))
        selected_hits=sum(len(set(g['finite'])&set(p['predicates'])) for g,p in zip(gold,pred))
        candidate_parent_hits=0;gold_edges=0
        root_scores=[];alternative_scores=[]
        for g,p in zip(gold,pred):
            for c,parent in {int(c):v for c,v in g['parents'].items()}.items():
                if parent is None:continue
                gold_edges+=1
                if c in p['predicates'] and parent in p['predicates']:
                    if parent in [row['parent'] for row in p['arc_candidates'][str(c)]]:candidate_parent_hits+=1
            for alternatives in p['arc_candidates'].values():
                root=next(a['logit'] for a in alternatives if a['parent'] is None)
                others=[a['logit'] for a in alternatives if a['parent'] is not None]
                root_scores.append(root)
                if others:alternative_scores.append(max(others)-root)
        overlaps=sum(tuple(g['tokens'][i:i+12]) in source_shingles for g in gold for i in range(max(0,len(g['tokens'])-11)))
        output.append({'author':author,'gold_predicates':denominator,'finite_candidate_hits':candidate_hits,
            'finite_candidate_recall_ceiling':candidate_hits/max(1,denominator),'selected_gold_predicates':selected_hits,
            'gold_nonroot_edges':gold_edges,'correct_edge_available_in_candidate_pool':candidate_parent_hits,
            'predicted_nonroot_edges':sum(parent is not None for p in pred for parent in p['parents'].values()),
            'mean_root_arc_logit':mean(root_scores),
            'mean_best_nonroot_minus_root_logit':mean(alternative_scores),
            'predicate_f1_stream_cluster_95_interval':bootstrap([r['metrics'] for r in chosen]),
            'exact_12_token_source_overlaps':overlaps,
            'uncertainty':{k:mean(v[k] for v in map(uncertainty,pred) if v[k] is not None) for k in uncertainty(pred[0])}})
    robustness=[]
    for author in ['Cicero','Sallust','Suetonius']:
        for rate in [0,.05,.10,.25,.50]:
            group=[r for r in corrupt if r['author']==author and r['rate']==rate]
            us=[uncertainty(r['prediction']) for r in group]
            robustness.append({'author':author,'rate':rate,'runs':len(group),
                'actual_type_rate':mean(r['changed_types']/r['total_types'] for r in group),
                'actual_token_rate':sum(r['changed_tokens'] for r in group)/sum(r['metrics']['tokens'] for r in group),
                'mean_binary_entropy':mean(u['mean_binary_entropy'] for u in us),
                'mean_arc_logit_margin':mean(u['mean_arc_logit_margin'] for u in us if u['mean_arc_logit_margin'] is not None),
                'morphology_coverage':sum(r['metrics']['known_tokens'] for r in group)/sum(r['metrics']['tokens'] for r in group)})
    report={'authors':output,'robustness':robustness,
        'source_gold_root_rate':sum(p is None for s in training for p in s['parents'].values())/sum(len(s['finite']) for s in training),
        'source_training_sentences':sum(len(s['sentences']) for s in training),'source_training_streams':len(training),
        'source_training_ids':[{'author':s['author'],'work':s['work'],'sent_id':s['sent_id']} for s in selected],
        'scope':'Entropy and score margins are descriptive proxies, not calibrated uncertainty or posterior probabilities.',
        'report_sha256':digest(load('report.json')),'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    write_json(OUT/'diagnostics.json',report)
    print(json.dumps(output,indent=2))


if __name__=='__main__':run()
