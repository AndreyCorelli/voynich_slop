"""Summarize a bounded development smoothing sweep and independent source loss."""
import argparse
import json
from pathlib import Path
from statistics import mean

from voynich_smt.word_mapping.ravi_knight.english import extract, prefix_segments, source_loss
from voynich_smt.word_mapping.ravi_knight.lm import SourceModel


def summarize(paths, raw_file):
    segments = extract(raw_file.read_text(encoding='utf-8-sig'), '11')
    excluded = prefix_segments(segments, 2000)
    development = prefix_segments(segments[len(excluded):], 2000)
    results = [json.loads(p.read_text()) for p in paths]
    assert len({r['public_sha256'] for r in results}) == 1
    rows = []
    for path, result in zip(paths, results):
        finals = [r['stages'][-1] for r in result['runs']]
        assert finals and all(s['source'] == finals[0]['source'] for s in finals)
        score = source_loss(SourceModel(**finals[0]['source']), development)
        if 'lm_development' in result:
            assert result['lm_development'] == score
        rows.append({'result': str(path), 'smoothing': result['protocol']['smoothing'],
                     'seeds': [r['seed'] for r in result['runs']],
                     'accuracies': [s['token_accuracy'] for s in finals],
                     'mean_accuracy': mean(s['token_accuracy'] for s in finals),
                     'lm_development': score})
    return {'scope': 'bounded reused-development smoothing diagnostic; no automatic default change',
            'lm_policy': 'After whole-segment 2000-token prefix, next whole-segment prefix fitting 2000 tokens. BOS/EOS included. UNKNOWN is a collapsed outcome, not full-vocabulary perplexity.',
            'conditions': rows}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('results', nargs='+', type=Path)
    parser.add_argument('--raw-file', type=Path, default=Path('data/raw/ravi-knight-english/11.txt'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = summarize(args.results, args.raw_file)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
