"""Independent checkpoint audit and aligned previous-model role comparison."""
import json
from pathlib import Path
import numpy as np
from benchmarks.latin_sentence_role import OUT,SOURCE
from benchmarks.latin_context_role import Model,role,POS
from benchmarks.latin_relative_search import grammatical_metrics
from benchmarks.latin_adversarial_objective import quality
from voynich_smt.data.corpus import write_json


def run():
    report=json.loads((OUT/'report.json').read_text());fixtures={f['id']:f for f in json.loads((SOURCE/'dataset.json').read_text())};entries=json.loads((OUT/'morphology.json').read_text())['entries'];checked=0
    for r in report['runs']:
        f=fixtures[r['fixture']];previous=-float('inf')
        for s in r['snapshots']:
            mapping=s['mapping'];assert len(set(mapping.values()))==len(mapping)
            assert all(mapping[t]==f['truth'][t] for t in f['truth'] if t not in f['active'])
            assert s['score']>=previous-1e-8;previous=s['score']
            assert grammatical_metrics(f['sentences'],mapping,f['truth'],entries)==s['grammar'];checked+=1
    budgets={}
    for budget in (100,1000):
        rr=[{**r,'snapshots':[r['snapshots'][0],next(s for s in r['snapshots'] if s['budget']==budget)]} for r in report['runs']]
        budgets[str(budget)]=quality(rr)
    corrupt=[r for r in report['runs'] if r['start'].startswith('corrupt')]
    valid=[r for r in report['runs'] if not r['start'].startswith('corrupt')]
    restored=sum(min(r['snapshots'][-1]['grammar']['gold_edge_accuracy'],r['snapshots'][-1]['grammar']['role_inflection_accuracy'])==1 for r in corrupt)
    monotone=sum(all(r['snapshots'][-1]['grammar'][k]>=r['snapshots'][1]['grammar'][k] for k in ('satisfied_gold_edges','role_inflection_compatible_tokens')) for r in report['runs'])/len(report['runs'])
    pairs={}
    for split in ('calibration','test'):
        cc=[c for c in report['comparisons'] if c['split']==split]
        pairs[split]={'original_correct':sum(c['scores']['truth']>c['scores'][k] for c in cc for k in ('corrupt_low','corrupt_high')),'alternative_correct':sum(c['scores']['control_high']>c['scores'][k] for c in cc for k in ('corrupt_low','corrupt_high')),'pairs':2*len(cc)}
    baseline=Path('experiments/results/latin-context-role');v=json.loads((baseline/'model-vocabulary.json').read_text());m=Model.__new__(Model);m.labels=[tuple(x) for x in v['labels']];m.vocabulary=v['vocabulary'];m.weights=np.load(baseline/'model-weights.npy');unique={}
    for f in fixtures.values():
        if f['split']=='test':
            for s in f['sentences']:unique[(f['document'],s['id'])]=s
    correct=n=0
    for s in unique.values():
        p=m.predict(tuple(t['word'] for t in s['tokens']))
        for i,t in enumerate(s['tokens']):
            if t['pos'] in POS:n+=1;correct+=m.labels[int(p[i].argmax())]==role(t)
    audit={'independent_grammar_injectivity_fixed_mappings_and_score_checks':checked,'budgets':budgets,'valid_runs':len(valid),'corrupt_runs':len(corrupt),'corrupt_fully_restored':restored,'100_to_1000_structural_nonregression':monotone,'pairs':pairs,'previous_model_aligned_unique_content_role_accuracy':correct/n,'aligned_unique_content_tokens':n,'palladius_quality':quality([r for r in report['runs'] if r['document']=='palladius.opus_agriculturae'])}
    write_json(OUT/'audit.json',audit);print(json.dumps(audit,indent=2))
if __name__=='__main__':run()
