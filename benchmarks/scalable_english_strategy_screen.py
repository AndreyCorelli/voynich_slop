"""Predeclared one-factor strategy screens on the fixed Wells development prefix."""
import argparse
import json
from pathlib import Path

from benchmarks.scalable_english_run import run
from benchmarks.scalable_english_evaluate import evaluate
from benchmarks.scalable_english_diagnostics import analyze
from benchmarks.scalable_english_diagnostics_validate import validate
from benchmarks.scalable_english_consensus import collect, evaluate as evaluate_consensus
from voynich_smt.word_mapping.scalable.retrieval import RetrievalConfig
from voynich_smt.word_mapping.scalable.search import SearchConfig

BASE=Path('experiments/results/scalable-english')
OLD=BASE/'independent-resources-v1'
RESOURCE=BASE/'strategy-resources-v1'
FIXTURE=BASE/'independent-wells-35k-v1'
ROOT=BASE/'strategy-screen-v1'
VARIANTS=('baseline','pooled','joint','trigram','corpus_control','corpus_expanded')


def resources_for(name):
    return RESOURCE/name if name in ('trigram','corpus_control','corpus_expanded') else OLD


def search(name,root=ROOT,*,proposals=4000,seeds=(3,5),budget_seconds=None,fixture=FIXTURE):
    if name not in VARIANTS: raise ValueError('Unknown strategy')
    if budget_seconds is None:
        design=json.loads((ROOT/'design.json').read_text())
        budget_seconds=design.get('variant_budget_seconds',{}).get(name,design['per_chain_budget_seconds'])
    config=SearchConfig(initialization='frequency',proposals=proposals,budget_seconds=budget_seconds,reserve_seconds=10,
                        joint_probability=.1 if name=='joint' else 0.)
    retrieval=RetrievalConfig(total_entries=10000,context_strategy='pooled' if name=='pooled' else 'sampled')
    return run(resources_for(name),fixture/'public/cipher.json',root/name,
               config=config,retrieval=retrieval,seeds=seeds,trace=True)


def measure(name,root=ROOT,*,fixture=FIXTURE):
    resources=resources_for(name); output=root/name
    truth=fixture/'evaluation-only/truth.json'
    evaluated=evaluate(resources,output,truth)
    diagnostics=analyze(resources,output,truth,output/'traces',output/'analysis')
    validated=validate(resources,output,truth,output/'traces',output/'analysis')
    collect(output,output/'consensus-public.json')
    consensus=evaluate_consensus(resources,output,truth,output/'consensus-evaluation.json')
    return evaluated,diagnostics,validated,consensus


def compare(root=ROOT):
    reports={}; inference={}
    for name in VARIANTS:
        output=root/name
        inference[name]=json.loads((output/'inference.json').read_text())
        ev=json.loads((output/'evaluation.json').read_text())
        diag=json.loads((output/'analysis/diagnostics.json').read_text())
        assert json.loads((output/'analysis/validation.json').read_text())['status']=='validated'
        assert all(r['step']==4000 and r['stop_reason']=='proposal_limit' for r in inference[name]['runs'])
        reports[name]={'mean_token_accuracy':ev['mean_score_selected_token_accuracy'],
                       'selected_seed':ev['selected_seed'],'selected_token_accuracy':ev['selected_token_accuracy'],
                       'coverage':ev['inventory_coverage'],
                       'candidate_support_scope':('Pools and selected moves; unselected internal cycle trials are not logged.'
                                                  if name=='joint' else 'Recorded pools, implied swap rows and selected exploration moves.'),
                       'runs':[{'seed':r['seed'],'initial_literal':r['initial'],'literal':r['score_selected_best'],
                                'visited_types':diag['attribution'][str(r['seed'])]['visited_types'],
                                'true_offered_types':sum(row['offered'] for row in diag['attribution'][str(r['seed'])]['rows']),
                                'offered_evaluations':diag['attribution'][str(r['seed'])]['offered_evaluations'],
                                'accepted_by_source':diag['attribution'][str(r['seed'])]['accepted_by_source'],
                                'failure_categories':diag['attribution'][str(r['seed'])]['categories']}
                               for r in ev['runs']],
                       'consensus':json.loads((output/'consensus-evaluation.json').read_text())}
        for measured,saved in zip(reports[name]['runs'],inference[name]['runs']):
            assert measured['seed']==saved['seed']
            measured['elapsed_seconds']=saved['elapsed_seconds']
            measured['source_counts']=saved['source_counts']
    def normalized(name,allowed):
        protocol=json.loads(json.dumps(inference[name]['protocol']))
        for section,key in allowed:
            protocol[section].pop(key,None)
        return protocol
    assert normalized('baseline',[('retrieval','context_strategy')])==normalized('pooled',[('retrieval','context_strategy')])
    assert normalized('baseline',[('search','joint_probability')])==normalized('joint',[('search','joint_probability')])
    assert normalized('baseline',[('search','budget_seconds')])['search']==normalized('trigram',[('search','budget_seconds')])['search']
    assert normalized('baseline',[])['retrieval']==normalized('trigram',[])['retrieval']
    assert inference['baseline']['protocol']['inventory_sha256']==inference['trigram']['protocol']['inventory_sha256']
    control=normalized('corpus_control',[]); expanded=normalized('corpus_expanded',[])
    control.pop('model_sha256'); expanded.pop('model_sha256')
    assert control==expanded
    # Trigram bigram projection must be identical to the baseline.
    from voynich_smt.word_mapping.scalable.inventory import Inventory
    from voynich_smt.word_mapping.scalable.trigram import load_model
    inventory=Inventory(OLD/'inventory.sqlite')
    try:
        trigram=load_model(RESOURCE/'trigram/model.sqlite',inventory)
        assert trigram.bigram.identity==inference['baseline']['protocol']['model_sha256']
    finally: inventory.close()
    comparisons={}
    for candidate,control in (('pooled','baseline'),('joint','baseline'),('trigram','baseline'),('corpus_expanded','corpus_control')):
        changes=[{'seed':a['seed'],'token_accuracy_change':b['literal']['token_accuracy']-a['literal']['token_accuracy']}
                 for a,b in zip(reports[control]['runs'],reports[candidate]['runs'])]
        assert [r['seed'] for r in reports[control]['runs']]==[r['seed'] for r in reports[candidate]['runs']]
        comparisons[candidate]={'control':control,'mean_change':reports[candidate]['mean_token_accuracy']-reports[control]['mean_token_accuracy'],
                                'paired_changes':changes}
    result={'scope':'Development screening on one previously inspected work, not independent confirmation',
            'design':json.loads((root/'design.json').read_text()),'methods':reports,'comparisons':comparisons,
            'grammar':'not_evaluated','semantics':'not_evaluated',
            'limits':['Two seeds, one reused work; selection bias and considerable variance.',
                      'Equal proposal counts do not equal candidate scoring cost.',
                      'More varied corpus remains dominated by older fiction.',
                      'Search scores from different models must not be compared as recovery scores.',
                      'Consensus is evaluated, never used to freeze mappings.']}
    with (root/'comparison.json').open('x') as handle: json.dump(result,handle,indent=2); handle.write('\n')
    return result


def select_replication(root=ROOT):
    from voynich_smt.data.corpus import digest
    comparison=json.loads((root/'comparison.json').read_text())
    positive=[(name,data) for name,data in comparison['comparisons'].items() if data['mean_change']>0]
    winner=min(positive,key=lambda item:(-item[1]['mean_change'],item[0])) if positive else None
    result={'comparison_sha256':digest(comparison),
            'candidate':winner[0] if winner else None,
            'control':winner[1]['control'] if winner else None,
            'plan':comparison['design']['replication_plan']}
    with (root/'replication-selection.json').open('x') as handle:
        json.dump(result,handle,indent=2); handle.write('\n')
    return result


def replicate(source,root=ROOT):
    from benchmarks.scalable_english_independent import prepare
    from voynich_smt.data.corpus import digest
    selection=json.loads((root/'replication-selection.json').read_text())
    assert selection['comparison_sha256']==digest(json.loads((root/'comparison.json').read_text()))
    if selection['candidate'] is None:
        return {'status':'skipped; no positive screening mean'}
    plan=selection['plan']
    destination=root/'replication'; destination.mkdir()
    audits={}
    for role in ('control','candidate'):
        name=selection[role]
        audits[role]=prepare(resources_for(name),source,destination/f'fixture-{role}',
                            tokens=plan['prefix_tokens'],incipit=plan['incipit'])
    assert audits['control']['public_sha256']==audits['candidate']['public_sha256']
    assert audits['control']['inventory_sha256']==audits['candidate']['inventory_sha256']
    fixture=destination/'fixture-control'
    for role in ('control','candidate'):
        search(selection[role],destination,fixture=fixture,
               proposals=plan['proposals'],seeds=tuple(plan['seeds']))
    results={}
    for role in ('control','candidate'):
        measured,*_=measure(selection[role],destination,fixture=fixture)
        results[role]={'variant':selection[role],'evaluation':measured}
    result={'scope':'One new work/seed after development selection; not a generalization estimate',
            'selection':selection,'results':results,
            'token_accuracy_change':results['candidate']['evaluation']['selected_token_accuracy']-
                                    results['control']['evaluation']['selected_token_accuracy'],
            'grammar':'not_evaluated','semantics':'not_evaluated'}
    assert all(r['steps']==plan['proposals'] and r['stop_reason']=='proposal_limit'
               for measured in results.values() for r in measured['evaluation']['runs'])
    with (destination/'comparison.json').open('x') as handle:
        json.dump(result,handle,indent=2); handle.write('\n')
    return result


def consensus_check(root=ROOT):
    design=json.loads((root/'consensus-replication-design.json').read_text())
    assert design['initialization']=='random'
    fixture=root/'replication/fixture-control'
    output=root/'replication/random-consensus'
    run(OLD,fixture/'public/cipher.json',output,seeds=tuple(design['seeds']),
        config=SearchConfig(initialization='random',proposals=design['proposals'],
                            budget_seconds=400,reserve_seconds=10),trace=True)
    measured=evaluate(OLD,output,fixture/'evaluation-only/truth.json')
    collect(output,output/'consensus-public.json')
    calibrated=evaluate_consensus(OLD,output,fixture/'evaluation-only/truth.json',output/'consensus-evaluation.json')
    assert all(r['steps']==design['proposals'] and r['stop_reason']=='proposal_limit' for r in measured['runs'])
    result={'design':design,'evaluation':measured,'consensus':calibrated}
    with (root/'replication/consensus-check.json').open('x') as handle:
        json.dump(result,handle,indent=2); handle.write('\n')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['search','measure','compare','select-replication','replicate','consensus-check'])
    parser.add_argument('--variants',nargs='+',choices=VARIANTS,default=list(VARIANTS))
    parser.add_argument('--source',type=Path)
    args=parser.parse_args()
    if args.action=='consensus-check':
        result=consensus_check()
        print(json.dumps(result['consensus'],indent=2),flush=True)
    elif args.action=='select-replication':
        print(json.dumps(select_replication(),indent=2),flush=True)
    elif args.action=='replicate':
        if args.source is None:
            parser.error('--source is required for replication')
        print(json.dumps(replicate(args.source),indent=2),flush=True)
    elif args.action=='compare':
        result=compare()
        print(json.dumps(result['comparisons'],indent=2),flush=True)
    else:
        for name in args.variants:
            result=search(name) if args.action=='search' else measure(name)
            print(json.dumps({'variant':name,'action':args.action,'status':'complete'}),flush=True)
