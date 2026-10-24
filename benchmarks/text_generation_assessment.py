"""Provenance validation and predeclared conditional-order diagnostic."""
from collections import Counter
from itertools import product
import json
from pathlib import Path
import random
from statistics import mean
from benchmarks import text_generation_comparison as experiment
from voynich_smt.data.corpus import digest, write_json

ROOT=experiment.OUT


def plan():
    p=experiment.prepare()
    value={'prepared_sha256':digest(p),'selected_sha256':digest(json.loads((ROOT/'iteration-6.json').read_text())),
           'seeds':list(experiment.SEEDS),'scope':'Within-heldout-block word permutation, conditioned on exact word multiset. Oracle diagnostic of ordering only, not a generative competitor or replacement selection. Frozen before stage7 evaluation.'}
    path=ROOT/'conditional-order-plan.json'
    if path.exists(): assert json.loads(path.read_text())==value
    else: write_json(path,value)
    return value


def validate():
    p=experiment.prepare(); frozen=json.loads((ROOT/'conditional-order-plan.json').read_text())
    assert frozen['prepared_sha256']==digest(p)
    assert set(b['folio'] for b in p['development']).isdisjoint(b['folio'] for b in p['heldout'])
    previous=None
    for index in range(1,8):
        report=json.loads((ROOT/f'iteration-{index}.json').read_text()); savedplan=json.loads((ROOT/f'plan-{index}.json').read_text())
        assert report['plan']==savedplan and savedplan['prepared_sha256']==digest(p)
        assert savedplan['previous_sha256']==(digest(previous) if previous else None)
        assert savedplan['holdout_access']==(index==7)
        if 'models' in report:
            assert report['models']==experiment.evaluate(p,savedplan['models'],index==7)
        previous=report
    assert frozen['selected_sha256']==digest(json.loads((ROOT/'iteration-6.json').read_text()))
    selected=json.loads((ROOT/'iteration-6.json').read_text())['selected_generator']
    assert previous['selected_generator']==selected
    rows=[]; norm=experiment.normalization(p)
    for i,b in enumerate(p['heldout']):
        words=[tuple(w) for w in b['words']]; target=experiment.metrics(words)
        for seed in frozen['seeds']:
            shuffled=list(words); random.Random(seed+1000*i).shuffle(shuffled)
            assert Counter(shuffled)==Counter(words)
            measured=experiment.metrics(shuffled)
            for k in ('mean_length','unique_ratio','one_edit_pair_fraction'): assert measured[k]==target[k]
            rows.append({'block':i,'seed':seed,'target':target,'shuffled':measured,
                         'ordering_distance':mean(abs(measured[k]-target[k])/norm[k]['scale'] for k in ('adjacent_repeat','repeat_local_excess','one_edit_local_excess'))})
    write_json(ROOT/'conditional-order-result.json',{'plan_sha256':digest(frozen),'rows':rows,'mean_ordering_distance':mean(r['ordering_distance'] for r in rows),
        'target_ordering_means':{k:mean(r['target'][k] for r in rows) for k in ('adjacent_repeat','repeat_local_excess','one_edit_local_excess')},
        'shuffled_ordering_means':{k:mean(r['shuffled'][k] for r in rows) for k in ('adjacent_repeat','repeat_local_excess','one_edit_local_excess')}})
    write_json(ROOT/'validation.json',{'verified':True,'iterations':7,'models':len(experiment.MODELS),'heldout_blocks':len(p['heldout']),
        'development_blocks':len(p['development']),'seeds':len(experiment.SEEDS),'source_split':'disjoint folios','solver_calls':0})


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(); parser.add_argument('--plan',action='store_true'); args=parser.parse_args()
    if args.plan: plan()
    else: validate()
