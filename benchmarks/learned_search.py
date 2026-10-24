"""Search alternative suffix keys using independently checked analytic exclusions."""
import argparse
from dataclasses import asdict, replace
import json
from pathlib import Path
from voynich_smt.cipher.base import Encoder
from voynich_smt.data.corpus import digest, write_json
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.solver.guided import recover_guided
from voynich_smt.solver.learning import learn, recover_learned, validate_rules


def run(config, output, artifacts):
    if (set(config) != {'source_report', 'timeout_ms', 'dictionary_encoding', 'candidate_count'}
            or type(config['timeout_ms']) is not int or config['timeout_ms'] <= 0
            or type(config['candidate_count']) is not int or config['candidate_count'] <= 0
            or config['dictionary_encoding'] not in {'flat', 'trie'}):
        raise ValueError('Invalid learned search configuration')
    source = json.loads(Path(config['source_report']).read_text())
    suffix_row = next(r for r in source['experiments'] if r['id'] == source['conflict']['experiment_id'])
    prefix_row = next(r for r in source['experiments'] if r['id'] == source['prefix']['experiment_id'])
    suffix = HiddenRecoveryRequest.from_dict(json.loads(Path(suffix_row['public_input']).read_text()))
    context = HiddenRecoveryRequest.from_dict(json.loads(Path(prefix_row['public_input']).read_text()))
    suffix, context = [replace(r, timeout_ms=config['timeout_ms'], dictionary_encoding=config['dictionary_encoding'])
                       for r in (suffix, context)]
    seed = Encoder({s: tuple(tuple(c) for c in cs) for s, cs in suffix_row['result']['encoder']['codebook'].items()})
    start = source['source_conflict']['start']
    rules = learn(context, seed)
    report = {'config': config, 'source_sha256': digest(source), 'experiments': [],
              'semantics': 'Only independently checked analytic exclusions; UNKNOWN creates no exclusions',
              'complete': False}
    for i in range(config['candidate_count']):
        payload = {'request': asdict(suffix), 'context': asdict(context), 'sample_start': start, 'rules': rules[:]}
        path = artifacts / 'inputs' / f'candidate-{i:02d}.json'
        write_json(path, payload)
        print(f'Candidate {i}: {len(rules)} proved exclusions', flush=True)
        result = recover_learned(suffix, context, start, rules)
        row = {'public_input': str(path), 'input_sha256': digest(payload), 'suffix': asdict(result)}
        report['experiments'].append(row)
        write_json(output, report)
        print(f'  suffix {result.status} ({result.runtime_seconds:.3f}s)', flush=True)
        if result.status != 'SAT':
            report['outcome'] = {'status': result.status, 'scope': 'suffix under proved full-context exclusions'}
            break
        used = sorted({s for w in result.plaintext.words for s in w})
        guide = {'request': asdict(context), 'guidance': {'encoder': asdict(result.encoder),
            'pinned_symbols': used, 'rotate': True, 'hint_symbols': [], 'word_hints': {}}}
        guide_path = artifacts / 'inputs' / f'extension-{i:02d}.json'
        write_json(guide_path, guide)
        extension = recover_guided(context, result.encoder, used, rotate=True)
        row.update(extension_input=str(guide_path), extension=asdict(extension))
        print(f'  extension {extension.status} ({extension.runtime_seconds:.3f}s)', flush=True)
        discovered = learn(context, result.encoder)
        added = [r for r in discovered if r not in rules]
        if extension.status == 'UNSAT':
            core = extension.capacity.get('pinned_unsat_core', [])
            if core:
                rule = {'kind': 'pin_core', 'mappings': {s: [list(c) for c in result.encoder.codebook[s]] for s in core},
                        'proof_encoder': asdict(result.encoder)}
                try:
                    validate_rules(context, [rule])
                except ValueError as error:
                    row['unlearned_core_reason'] = str(error)
                else:
                    added.append(rule)
        row['new_proved_exclusions'] = added
        rules.extend(added)
        write_json(output, report)
        if extension.status == 'SAT':
            report['outcome'] = {'status': 'SAT', 'scope': 'full prefix', 'verified': extension.verified}
            break
        if extension.status == 'UNKNOWN' or not added:
            report['outcome'] = {'status': extension.status, 'scope': 'conditional extension',
                'reason': 'No unproved candidate blocking; unresolved extension or no new analytic exclusion'}
            break
    else:
        report['outcome'] = {'status': 'budget exhausted', 'scope': 'candidate search'}
    report.update(complete=True, learned_rules=rules)
    write_json(output, report)
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', default='experiments/configs/learned-search.json')
    parser.add_argument('--output', default='experiments/results/learned-search.json')
    parser.add_argument('--artifacts', default='data/generated/learned-search')
    parser.add_argument('--replay')
    args = parser.parse_args()
    if args.replay:
        p = json.loads(Path(args.replay).read_text())
        result = recover_learned(HiddenRecoveryRequest.from_dict(p['request']),
            HiddenRecoveryRequest.from_dict(p['context']), p['sample_start'], p['rules'])
        print(json.dumps(asdict(result)))
    else:
        run(json.loads(Path(args.config).read_text()), Path(args.output), Path(args.artifacts))


if __name__ == '__main__':
    main()
