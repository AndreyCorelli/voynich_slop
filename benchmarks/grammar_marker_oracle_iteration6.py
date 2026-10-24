"""Frozen-weight marker-oracle interventions and exact reference-score audits."""
from copy import deepcopy
from dataclasses import asdict
import hashlib
import json
import math
from pathlib import Path
import time
from collections import Counter

from benchmarks.grammar_markers_iteration5 import OUT as FIVE,marker_metrics,aggregate_markers
from benchmarks.grammar_linker_iteration4 import detailed_metrics,summarize
from benchmarks.grammar_structure_iteration3_validate import FrozenAdapter
from voynich_smt.data.corpus import digest,write_json
from voynich_smt.parent_ranking import ConditionalRanker
from voynich_smt.marker_structure import MarkerModel,infer_attached_links

OUT=Path('experiments/results/grammar-restoration/iteration6-v2')
MODES=('predicted','oracle_scope','oracle_full')


class OracleMarkerProvider:
    """Benchmark-only intervention; no gold parent links enter its output."""
    def __init__(self,learned,gold_markers,mode):
        if mode not in ('oracle_scope','oracle_full'):raise ValueError('Unknown oracle intervention')
        self.learned,self.gold,self.mode=learned,{int(k):v for k,v in gold_markers.items()},mode

    def predict(self,tokens,predicates,adapter,boundaries=None):
        originals={m['position']:m for m in self.learned.predict(tokens,predicates,adapter,boundaries)}
        positions=sorted(set(originals)|(set(self.gold) if self.mode=='oracle_full' else set()))
        result=[]
        for i in positions:
            marker=self.gold.get(i)
            kinds=[marker['kind']] if self.mode=='oracle_full' and marker else originals[i]['kinds']
            targets=[None]+[p for p in predicates if i not in predicates and (boundaries is None or
                next(j for j,b in enumerate(boundaries) if p<b)==next(j for j,b in enumerate(boundaries) if i<b))]
            wanted=marker['target'] if marker else None
            chosen=wanted if wanted in targets else None
            result.append({'position':i,'surface':tokens[i],'kinds':list(kinds),'target':chosen,
                'alternatives':[{'target':p,'logit':0. if p==chosen else -30.,'probability':float(p==chosen)} for p in targets],
                'oracle_mode':self.mode,'reference_target':wanted,'blocked_reference_target':wanted is not None and wanted not in targets})
        return result


def score_audit(prediction,gold):
    actual={int(c):p for c,p in prediction['parents'].items()};relations={int(c):r for c,r in prediction['relations'].items()}
    truth={int(c):p for c,p in gold['parents'].items()};gold_rel={int(c):r for c,r in gold['relations'].items()}
    per_child=[];reference_score=0;complete=set(prediction['predicates'])==set(gold['finite'])
    if complete:
        for start in truth:
            seen=set();cursor=start
            while cursor is not None:
                assert cursor in truth and cursor not in seen
                seen.add(cursor);cursor=truth[cursor]
    for child,parent in truth.items():
        rows=prediction['arc_candidates'].get(child,prediction['arc_candidates'].get(str(child),[]))
        correct=[r for r in rows if r['parent']==parent]
        typed=[r for r in correct if r['relation']==gold_rel[child]]
        if not correct or not typed:
            complete=False;continue
        best=max(r['logit'] for r in rows);best_correct=max(r['logit'] for r in correct);gold_value=typed[0]['logit']
        reference_score+=round(gold_value*1000000)
        per_child.append({'child':child,'reference_parent':parent,'chosen_parent':actual.get(child),'reference_relation':gold_rel[child],
            'chosen_relation':relations.get(child),'best_logit':best,'best_correct_parent_logit':best_correct,'reference_typed_logit':gold_value,
            'correct_parent_margin':best_correct-best,'correct_typed_margin':gold_value-best,
            'error':'unresolved' if prediction['status']!='optimal' else 'missing' if child not in actual else 'correct_parent' if actual[child]==parent else
                'false_root' if actual[child] is None else 'false_attachment' if parent is None else 'wrong_parent'})
    optimal=prediction['status']=='optimal'
    gap=prediction['forest_score_integer']-reference_score if complete and optimal else None
    if gap is not None:assert gap>=0
    return {'reference_forest_available':complete,'reference_score_integer':reference_score if complete else None,
        'optimum_minus_reference_integer':gap,'per_child':per_child,
        'error_counts':dict(Counter(r['error'] for r in per_child)),
        'strict_local_parent_misrankings':sum(r['correct_parent_margin']< -1e-9 for r in per_child),
        'strict_local_typed_misrankings':sum(r['correct_typed_margin']< -1e-9 for r in per_child)}


def run():
    if OUT.exists():raise ValueError('Preserve existing diagnostic output')
    start=time.monotonic();load=lambda name:json.loads((FIVE/name).read_text())
    previous_manifest=load('manifest.json');models=load('models.json')
    adapter=FrozenAdapter(load('morphology-lattice.json'))
    learned=MarkerModel(previous_manifest['marker_vocabulary'],ConditionalRanker(**models['marker']))
    rankers={n:ConditionalRanker(**models[n]) for n in ['marker_only','marker_interactions']}
    target_truth={r['id']:r for r in load('target-evaluation-only-truth.json')}
    source_truth=load('confirmation-truth.json')
    baselines=[]
    for row in load('target-predictions.json'):baselines.append({'dataset':'target',**row})
    for row in load('source-predictions.json'):
        if (row['split'],row['evidence'],row['boundaries'])==('confirmation','oracle_predicates','hidden') and row['model'] in rankers:
            baselines.append({'dataset':'source_confirmation',**row})
    input_names=['manifest.json','models.json','morphology-lattice.json','target-evaluation-only-truth.json',
        'confirmation-truth.json','target-predictions.json','source-predictions.json','validation.json']
    manifest={'version':1,'weights':'frozen iteration5-v2; no fitting','marker_modes':MODES,
        'scope':'explicit gold marker interventions; no new predicate or parent supplied by marker provider; target excerpts already inspected',
        'input_sha256':{str(FIVE/n):hashlib.sha256((FIVE/n).read_bytes()).hexdigest() for n in input_names},
        'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    write_json(OUT/'manifest.json',manifest)
    rows=[]
    for base in baselines:
        gold=target_truth[base['id']] if base['dataset']=='target' else source_truth[base['stream']]
        for mode in MODES:
            if mode=='predicted':prediction=deepcopy(base['prediction'])
            else:
                provider=OracleMarkerProvider(learned,gold['markers'],mode)
                prediction=infer_attached_links(gold['tokens'],base['prediction']['predicates'],adapter,rankers[base['model']],provider,
                    interactions=base['model']=='marker_interactions',boundaries=gold['boundaries'] if base['boundaries']=='supplied' else None)
            rows.append({'dataset':base['dataset'],'id':base.get('id'),'stream':base.get('stream'),'author':base.get('author'),
                'model':base['model'],'evidence':base['evidence'],'boundaries':base['boundaries'],'marker_mode':mode,
                'prediction':prediction,'metrics':detailed_metrics(prediction,gold),
                'marker_metrics':marker_metrics(prediction,gold,learned.vocabulary),'score_audit':score_audit(prediction,gold)})
        if len(rows)%60==0:print('conditions',len(rows),flush=True)
    write_json(OUT/'predictions.json',rows)
    summaries=[]
    keys=sorted({(r['dataset'],r['author'] or '',r['model'],r['evidence'],r['boundaries'],r['marker_mode']) for r in rows})
    for key in keys:
        selected=[r for r in rows if (r['dataset'],r['author'] or '',r['model'],r['evidence'],r['boundaries'],r['marker_mode'])==key]
        audited=[r['score_audit'] for r in selected]
        summaries.append(dict(zip(['dataset','author','model','evidence','boundaries','marker_mode'],key))|{
            'metrics':summarize([r['metrics'] for r in selected]),'markers':aggregate_markers([r['marker_metrics'] for r in selected]),
            'reference_forests_available':sum(a['reference_forest_available'] for a in audited),
            'reference_forests_scored':sum(a['optimum_minus_reference_integer'] is not None for a in audited),
            'reference_forests_strictly_outscored':sum(a['optimum_minus_reference_integer'] is not None and a['optimum_minus_reference_integer']>0 for a in audited),
            'error_counts':dict(sum((Counter(a['error_counts']) for a in audited),Counter())),
            'strict_local_parent_misrankings':sum(a['strict_local_parent_misrankings'] for a in audited)})
    report={'manifest_sha256':digest(manifest),'conditions':len(rows),'reused_baselines':len(baselines),
        'new_forests':len(rows)-len(baselines),'summary':summaries,'elapsed_seconds':time.monotonic()-start,
        'decision':'diagnose marker versus parent evidence; frozen weights and no dictionary optimization'}
    write_json(OUT/'report.json',report)
    for s in summaries:
        if s['dataset']=='target' and s['model']=='marker_only' and s['boundaries']=='hidden' and s['evidence']=='oracle_predicates':
            print(s['author'],s['marker_mode'],'edge F1',round(s['metrics']['edges']['f1'],3),'strictly outscored',s['reference_forests_strictly_outscored'],flush=True)
    print('completed',len(rows),'conditions in',round(report['elapsed_seconds'],2),'seconds',flush=True)


if __name__=='__main__':run()
