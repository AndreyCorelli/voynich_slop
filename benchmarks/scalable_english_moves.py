"""Exercise dictionary transactions on modern corpus streams; no recovery search."""
import argparse
import json
from pathlib import Path
import random
import resource
import sys
import time

from benchmarks.scalable_english_build import documents
from voynich_smt.word_mapping.scalable.data import generate
from voynich_smt.word_mapping.scalable.incremental import DictionaryScorer
from voynich_smt.word_mapping.scalable.inventory import Inventory
from voynich_smt.word_mapping.scalable.sparse_lm import SparseBigram
from voynich_smt.word_mapping.scalable.state import DictionaryState


def run(resources, raw, output, *, tokens=35000, proposals=2000):
    if type(tokens) is not int or tokens < 1 or type(proposals) is not int or proposals < 1:
        raise ValueError('Token and proposal budgets must be positive')
    output.mkdir(parents=True, exist_ok=False)
    inventory = Inventory(resources / 'inventory.sqlite')
    try:
        model = SparseBigram.load(resources / 'model.sqlite', inventory)
        remaining, selected = tokens, []
        for doc in documents(raw):
            selected.append(doc.words[:remaining])
            remaining -= len(selected[-1])
            if not remaining:
                break
        if remaining:
            raise ValueError('Source does not meet requested token budget')
        # Preparation only. Do not retain truth in the inference exercise.
        stream, _truth = generate(selected, seed=83)
        del _truth, selected
        stream.save(output / 'public' / 'cipher.json')
        state = DictionaryState.random(stream, model, seed=19)
        started = time.perf_counter()
        scorer = DictionaryScorer(model, stream, state)
        index_seconds = time.perf_counter() - started
        initial_score = scorer.score
        rng = random.Random(23)
        accepted, swaps, replacements, noops, checks, touched = 0, 0, 0, 0, 0, 0
        propose_seconds, commit_seconds, validate_seconds = 0., 0., 0.
        for index in range(proposals):
            cipher, word = rng.randrange(stream.type_count), rng.randrange(model.size)
            start = time.perf_counter()
            move = scorer.assign_or_swap(cipher, word)
            propose_seconds += time.perf_counter() - start
            touched += len(move.event_scores)
            if len(move.changes) == 2:
                swaps += 1
            elif move.changes:
                replacements += 1
            else:
                noops += 1
            if rng.random() < .5:  # Exercise transactions, not objective optimization.
                start = time.perf_counter()
                scorer.commit(move)
                commit_seconds += time.perf_counter() - start
                accepted += 1
            if (index + 1) % 100 == 0 or index + 1 == proposals:
                start = time.perf_counter()
                scorer.validate()
                validate_seconds += time.perf_counter() - start
                checks += 1
        state = scorer.state
        report = {'format_version': 1, 'scope': 'transaction engineering exercise; no decipherment result',
                  'cipher_sha256': stream.identity, 'model_sha256': model.identity,
                  'inventory_sha256': inventory.identity, 'inventory_forms': inventory.size,
                  'tokens': tokens, 'documents': len(stream.documents), 'cipher_types': stream.type_count,
                  'aggregated_events': len(scorer.index.events),
                  'scoring_event_occurrences': sum(n for _, _, n in scorer.index.events),
                  'requested_proposals': proposals, 'accepted': accepted, 'swaps': swaps,
                  'replacements': replacements, 'noops': noops, 'event_updates_evaluated': touched,
                  'full_validation_checks': checks, 'index_and_initial_score_seconds': index_seconds,
                  'proposal_seconds': propose_seconds, 'commit_seconds': commit_seconds,
                  'validation_seconds': validate_seconds, 'exercise_seconds': time.perf_counter()-started,
                  'initial_score': initial_score, 'final_score': scorer.score,
                  'final_assignments': state.assignments,
                  'peak_rss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (1 if sys.platform == 'darwin' else 1024),
                  'limitations': ['35k tokens span original EWT documents, not one long work.',
                                  'Fixture text also appears in LM training: engineering only.',
                                  'Uniform proposals with random accept/reject; no retrieval or optimization.',
                                  'Timing excludes resource loading and fixture generation.']}
        (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
        return report
    finally:
        inventory.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--resources', type=Path, default=Path('experiments/results/scalable-english/foundations-ewt-v1'))
    parser.add_argument('--raw', type=Path, default=Path('data/raw/scalable-english/en_ewt-r2.17-train.conllu'))
    parser.add_argument('--output', type=Path, default=Path('experiments/results/scalable-english/dictionary-moves-ewt-v1'))
    parser.add_argument('--tokens', type=int, default=35000)
    parser.add_argument('--proposals', type=int, default=2000)
    args = parser.parse_args()
    report = run(args.resources, args.raw, args.output, tokens=args.tokens, proposals=args.proposals)
    print(json.dumps({k:v for k,v in report.items() if k != 'final_assignments'}, indent=2))
