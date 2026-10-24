"""Public-input-only, budgeted sparse dictionary search with resumable restarts."""
import gzip
from contextlib import nullcontext
import argparse
from dataclasses import asdict, replace
import json
from pathlib import Path

from voynich_smt.word_mapping.scalable.data import CipherStream
from voynich_smt.word_mapping.scalable.inventory import Inventory
from voynich_smt.word_mapping.scalable.retrieval import RetrievalConfig
from voynich_smt.word_mapping.scalable.search import DictionarySearch, SearchConfig
from voynich_smt.word_mapping.scalable.trigram import load_model


def allocate_budget(config, restart_count):
    """Divide the CLI invocation budget/reserve across sequential restarts.

    The library SearchConfig is per chain; the CLI budget is for the bundle.
    Resource loading and external evaluation are outside the search clock.
    """
    if type(restart_count) is not int or restart_count < 1:
        raise ValueError('Expected a positive restart count')
    return replace(config, budget_seconds=config.budget_seconds / restart_count,
                   reserve_seconds=config.reserve_seconds / restart_count)


def run(resources, public, output, *, seeds=(3, 5, 7), config=None, retrieval=None, resume=False, steps=None, trace=False):
    if trace and resume:
        raise ValueError("Live tracing requires a fresh run")
    config = config or SearchConfig()
    retrieval = retrieval or RetrievalConfig(total_entries=10000)
    seeds = tuple(seeds)
    if not seeds or len(set(seeds)) != len(seeds) or any(type(s) is not int for s in seeds):
        raise ValueError('Expected distinct integer seeds')
    inventory = Inventory(resources / 'inventory.sqlite')
    try:
        model = load_model(resources / 'model.sqlite', inventory)
        stream = CipherStream.load(public)
        protocol = {'format_version': 1, 'scope': 'heuristic source-LM dictionary search; recovery evaluated separately',
                    'model_sha256': model.identity, 'inventory_sha256': inventory.identity,
                    'cipher_sha256': stream.identity, 'seeds': list(seeds),
                    'search': asdict(config), 'retrieval': asdict(retrieval)}
        if getattr(model, 'objective_kind', None) == 'association':
            protocol['scope'] = 'heuristic skip-association alignment; unnormalized score, not likelihood'
        if getattr(model, 'objective_kind', None) == 'shuffle_contrast':
            protocol['scope'] = 'heuristic frequency-matched ordering contrast; unnormalized score, not likelihood'
        if resume:
            previous = json.loads((output / 'protocol.json').read_text())
            previous['search'].setdefault('scheduler', 'mixed')
            previous['search'].setdefault('initialization', 'random')
            previous['search'].setdefault('joint_probability', 0.0)
            previous['retrieval'].setdefault('context_strategy', 'sampled')
            previous['retrieval'].setdefault('attested_mix', 0.0)
            if previous != protocol:
                raise ValueError('Resume protocol differs')
        else:
            output.mkdir(parents=True, exist_ok=False)
            (output / 'protocol.json').write_text(json.dumps(protocol, indent=2) + '\n')
            stream.save(output / 'public/cipher.json')
        results = []
        trace_reports = []
        if trace:
            (output / "traces").mkdir()
        for seed in seeds:
            checkpoint = output / f'seed-{seed}/checkpoint.json'
            if resume and checkpoint.exists():
                search = DictionarySearch.load(checkpoint, model, stream)
            else:
                search = DictionarySearch(model, stream, seed=seed, config=config, retrieval_config=retrieval)
            from benchmarks.scalable_english_trace import observe
            trace_path = output / 'traces' / f'seed-{seed}.jsonl.gz'
            with gzip.open(trace_path, 'wt', encoding='utf-8') if trace else nullcontext() as handle:
                with observe(search, lambda event: handle.write(json.dumps(event, separators=(',', ':')) + '\n')) if trace else nullcontext():
                    result = search.run(steps=steps, checkpoint=checkpoint,
                                        progress=lambda event: print(json.dumps({'seed': seed, **event}), flush=True))
            if trace:
                trace_reports.append({'seed': seed, 'steps': search.step, 'trace': trace_path.name})

            result['seed'] = seed
            (checkpoint.parent / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
            results.append(result)
            print(json.dumps({'seed': seed, **{k:result[k] for k in ('step','stop_reason','initial_score','best_score','elapsed_seconds')}}), flush=True)
        # Selection is score-only, across complete archived keys; no truth access.
        selected = max(results, key=lambda r: (r['best_score'], -r['seed']))
        summary = {'protocol': protocol, 'selected_seed': selected['seed'],
                   'selection_rule': 'highest archived source-model score, then lowest seed ID; uncalibrated',
                   'runs': results}
        if trace:
            (output / 'traces/trace-report.json').write_text(json.dumps(
                {'scope': 'live observational trace', 'protocol': protocol, 'runs': trace_reports}, indent=2) + '\n')
        (output / 'inference.json').write_text(json.dumps(summary, indent=2) + '\n')
        return summary
    finally:
        inventory.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--resources', type=Path, default=Path('experiments/results/scalable-english/foundations-ewt-v1'))
    parser.add_argument('--public', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--seeds', type=int, nargs='+', default=[3,5,7])
    parser.add_argument('--initialization', choices=['random', 'frequency', 'profile', 'classes'], default='random')
    parser.add_argument('--scheduler', choices=['mixed', 'coverage_first'], default='mixed')
    parser.add_argument('--context-strategy', choices=['sampled','pooled'], default='sampled')
    parser.add_argument('--joint-probability', type=float, default=0.)
    parser.add_argument('--trace', action='store_true', help='Stream public-only pool/move diagnostics during a fresh run')
    parser.add_argument('--proposals', type=int, default=20000)
    parser.add_argument('--budget-seconds', type=float, default=3600., help='Total search budget divided across restarts')
    parser.add_argument('--reserve-seconds', type=float, default=10.)
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--steps', type=int, help='Partial invocation; preserve original full annealing schedule')
    args = parser.parse_args()
    run(args.resources, args.public, args.output, seeds=args.seeds,
        config=allocate_budget(SearchConfig(joint_probability=args.joint_probability, initialization=args.initialization, scheduler=args.scheduler, proposals=args.proposals, budget_seconds=args.budget_seconds, reserve_seconds=args.reserve_seconds), len(args.seeds)),
        retrieval=RetrievalConfig(total_entries=10000, context_strategy=args.context_strategy),
        resume=args.resume, steps=args.steps, trace=args.trace)
