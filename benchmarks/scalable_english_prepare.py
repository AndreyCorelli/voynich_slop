"""Prepare opaque continuous word-cipher inputs; keep source details private."""
import argparse
from dataclasses import asdict
import hashlib
from pathlib import Path

from voynich_smt.data.corpus import write_json
from voynich_smt.word_mapping.scalable.data import generate, tokenize


def prepare(paths, output, *, seed=71, max_tokens=None):
    if max_tokens is not None and (type(max_tokens) is not int or max_tokens < 1):
        raise ValueError('max_tokens must be positive')
    plaintext, records = [], []
    for path in paths:
        raw = Path(path).read_bytes()
        words, spans = tokenize(raw.decode('utf-8-sig'))
        if max_tokens is not None:
            words, spans = words[:max_tokens], spans[:max_tokens]
        if not words:
            raise ValueError('No scoring words in source')
        plaintext.append(words)
        records.append({'path': str(path), 'raw_sha256': hashlib.sha256(raw).hexdigest(),
                        'character_spans': spans})
    public, truth = generate(plaintext, seed=seed)
    output.mkdir(parents=True, exist_ok=False)
    public.save(output / 'public' / 'cipher.json')
    truth.save(output / 'evaluation-only' / 'truth.json')
    write_json(output / 'evaluation-only' / 'provenance.json',
               {'public_sha256': public.identity, 'sources': records,
                'normalization': 'english-continuous-v1; lowercase ASCII words, internal apostrophes retained'})
    return public


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--text', type=Path, nargs='+', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--seed', type=int, default=71)
    parser.add_argument('--max-tokens', type=int)
    args = parser.parse_args()
    public = prepare(args.text, args.output, seed=args.seed, max_tokens=args.max_tokens)
    print(f'Prepared {sum(map(len, public.documents))} tokens; public identity {public.identity}')
