"""Frequency-penalty screen; public-only inference, separate literal evaluation."""
import json
import shutil
from pathlib import Path
from benchmarks.scalable_english_run import run
from benchmarks.scalable_english_evaluate import evaluate
from benchmarks.scalable_english_objective_reference import reference
from voynich_smt.word_mapping.scalable.inventory import Inventory
from voynich_smt.word_mapping.scalable.trigram import load_model
from voynich_smt.word_mapping.scalable.tempered import FrequencyTempered
from voynich_smt.word_mapping.scalable.search import SearchConfig

BASE = Path('experiments/results/scalable-english')
ROOT = BASE/'frequency-tempering-v1'
OLD = BASE/'independent-resources-v1'
WELLS = BASE/'independent-wells-35k-v1'
HOUND = BASE/'strategy-screen-v1/replication/fixture-control'


def dump(path, value):
    path.write_text(json.dumps(value, indent=2)+'\n')


def trial(resources, fixture, output, seeds):
    run(resources, fixture/'public/cipher.json', output, seeds=seeds,
        config=SearchConfig(initialization='frequency', proposals=4000, budget_seconds=400, reserve_seconds=10))
    result = evaluate(resources, output, fixture/'evaluation-only/truth.json')
    ref = reference(resources, fixture/'public/cipher.json', fixture/'evaluation-only/truth.json')
    dump(output/'objective-reference.json', ref)
    return {'mean': result['mean_score_selected_token_accuracy'],
            'selected': result['selected_token_accuracy'], 'runs': result['runs'], 'reference': ref}


def main():
    ROOT.mkdir(exist_ok=False)
    dump(ROOT/'design.json', {'alphas':[.75,.5,.25], 'development':'Wells, seeds 3 and 5',
         'confirmation':'Previously inspected Hound, seed 7; no fresh held-out work claim',
         'selection':'Largest development mean literal accuracy; ties prefer alpha nearer 1',
         'proposals':4000,'initialization':'frequency','baseline':'strategy-screen-v1/baseline',
         'objective':'LM score + (alpha-1) sum token log unigram probability; EOS excluded',
         'limits':'Unnormalized heuristic; grammar and meaning unmeasured; alpha selected with development truth only'})
    inventory = Inventory(OLD/'inventory.sqlite')
    try:
        model = load_model(OLD/'model.sqlite', inventory)
        for alpha in (.75,.5,.25):
            resources = ROOT/f'resources-{alpha}'; resources.mkdir()
            shutil.copyfile(OLD/'inventory.sqlite', resources/'inventory.sqlite')
            # Preserve evaluation provenance, with the actual objective identity.
            for name in ('report.json',):
                if (OLD/name).exists(): shutil.copyfile(OLD/name, resources/name)
            tempered = FrequencyTempered(model, alpha)
            tempered.save(resources/'model.sqlite')
            provenance = json.loads((OLD/'report.json').read_text())
            provenance.update(model_sha256=tempered.identity, parent_model_sha256=model.identity,
                              objective='frequency-tempered-v1', frequency_weight=alpha)
            dump(resources/'report.json', provenance)
    finally: inventory.close()
    results = {}
    for alpha in (.75,.5,.25):
        results[str(alpha)] = trial(ROOT/f'resources-{alpha}', WELLS, ROOT/f'wells-{alpha}', (3,5))
        dump(ROOT/'development.json', results)
        print('DEVELOPMENT', alpha, results[str(alpha)]['mean'], flush=True)
    winner = max((.75,.5,.25), key=lambda a:(results[str(a)]['mean'],a))
    dump(ROOT/'selection.json', {'alpha':winner, 'criterion':'development mean literal token accuracy'})
    confirmation = trial(ROOT/f'resources-{winner}', HOUND, ROOT/'hound-confirmation', (7,))
    dump(ROOT/'comparison.json', {'development':results, 'selected_alpha':winner, 'confirmation':confirmation})
    print('CONFIRMATION', winner, confirmation['mean'], flush=True)


def summarize(root=ROOT):
    """Bind reused controls and report paired recovery, score gaps, and cost."""
    result = json.loads((root/'comparison.json').read_text())
    screen = BASE/'strategy-screen-v1'
    comparisons = {}
    pairs = [('Wells', screen/'baseline', [(a,root/f'wells-{a}') for a in (.75,.5,.25)]),
             ('Hound', screen/'replication/baseline', [(result['selected_alpha'],root/'hound-confirmation')])]
    for fixture, baseline, trials in pairs:
        control = json.loads((baseline/'evaluation.json').read_text())
        control_run = json.loads((baseline/'inference.json').read_text())
        comparisons[fixture] = {'baseline_mean':control['mean_score_selected_token_accuracy'],
                               'baseline_selected':control['selected_token_accuracy'], 'weights':{}}
        for alpha, path in trials:
            report = json.loads((path/'evaluation.json').read_text())
            inference = json.loads((path/'inference.json').read_text())
            left = json.loads(json.dumps(control_run['protocol']))
            right = json.loads(json.dumps(inference['protocol']))
            for protocol in (left,right): protocol.pop('model_sha256')
            assert left == right, 'Control protocol differs beyond objective identity'
            assert all(r['steps']==4000 and r['stop_reason']=='proposal_limit' for r in report['runs'])
            ref = json.loads((path/'objective-reference.json').read_text())
            comparisons[fixture]['weights'][str(alpha)] = {
                'mean':report['mean_score_selected_token_accuracy'],
                'selected':report['selected_token_accuracy'],
                'mean_change':report['mean_score_selected_token_accuracy']-control['mean_score_selected_token_accuracy'],
                'paired_changes':[{'seed':b['seed'],'change':b['score_selected_best']['token_accuracy']-a['score_selected_best']['token_accuracy']}
                                  for a,b in zip(control['runs'],report['runs'])],
                'reference_minus_selected_score':ref['source_score']-max(r['best_score'] for r in inference['runs']),
                'elapsed_seconds':sum(r['elapsed_seconds'] for r in inference['runs']),
                'baseline_elapsed_seconds':sum(r['elapsed_seconds'] for r in control_run['runs'])}
    result['comparisons'] = comparisons
    dump(root/'summary.json',result)
    return comparisons


if __name__ == '__main__':
    main()
    summarize()
