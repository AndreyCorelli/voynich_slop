"""Capped training-only selection under a declared artificial word-pair prior."""
from dataclasses import asdict
import json
from pathlib import Path

from benchmarks.frozen_key_holdout import score
from benchmarks.l3_conflict import verify
from benchmarks.tiny_key_ambiguity import used_mappings
from voynich_smt.cipher.base import Encoder
from voynich_smt.data.corpus import digest, write_json
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.models.text import Text
from voynich_smt.solver.recovery import _recover

SOURCE = Path('experiments/results/tiny-key-ambiguity/report.json')
OUT = Path('experiments/results/tiny-word-sequence')
# Artificial grammar, specified explicitly; not an independently collected corpus.
REFERENCE = ('ab ac ba', 'ac ba ca', 'ba ca ab', 'ca ab ac')


def allowed_pairs():
    return frozenset((a, b) for phrase in REFERENCE
                     for a, b in zip(Text.from_string(phrase).words, Text.from_string(phrase).words[1:]))


def accepts(words, pairs):
    words = tuple(tuple(w) for w in words)
    return all((a, b) in pairs for a, b in zip(words, words[1:]))


def fit(q, pairs, exclusions=()):
    return asdict(_recover(None, q.ciphertext, q.plaintext_alphabet, q.ciphertext_alphabet,
        q.bounds, 5000, dictionary=q.dictionary, min_word_length=1,
        max_word_length=max(map(len, q.dictionary.words)), selection=q.selection,
        key_exclusions=tuple(exclusions), codeword_domains='observed', word_pairs=pairs))


def run():
    output = OUT / 'report.json'
    if output.exists() or (OUT / 'protocol.json').exists():
        raise ValueError('Fixed experiment already started; do not overwrite')
    saved = json.loads(SOURCE.read_text())
    q = HiddenRecoveryRequest.from_dict(saved['request'])
    pairs = allowed_pairs()
    protocol = {'reference_phrases': REFERENCE, 'allowed_pairs': sorted(pairs),
        'source_sha256': digest(saved), 'request_sha256': digest(asdict(q)),
        'max_solutions': 6, 'timeout_ms_per_attempt': 5000,
        'selection': 'All training adjacencies must belong to the fixed allowed set; no continuation criterion.',
        'limitation': 'Engineered toy grammar chosen after the preceding experiment; not a blind or historical independent corpus test.',
        'code_sha256': {str(p): digest(p.read_text()) for p in
            (Path(__file__), Path('src/voynich_smt/solver/recovery.py'))}}
    write_json(OUT / 'protocol.json', protocol)
    audit = [{'number': row['number'],
              'training_pair_compatible': accepts(row['result']['plaintext']['words'], pairs)}
             for row in saved['solutions']]
    # Fit and select with training only. Evaluate continuation after every fit is frozen.
    results = []; exclusions = []; attempts = []; stop = 'SIX_SOLUTION_CAP'
    for _ in range(6):
        result = fit(q, pairs, exclusions)
        attempts.append({'status': result['status'], 'runtime_seconds': result['runtime_seconds']})
        if result['status'] != 'SAT':
            stop = result['status']; break
        verify(q, result)
        if not accepts(result['plaintext']['words'], pairs):
            raise RuntimeError('Independent word-pair verification failed')
        mappings = used_mappings(result)
        if any(all(m in mappings for m in ex['segments']) for ex in exclusions):
            raise RuntimeError('Ownership exclusion violated')
        results.append(result)
        exclusions.append({'kind': 'word', 'segments': mappings})
    continuation = Text(tuple(tuple(w) for w in saved['continuation']['words']))
    truth_words = saved['generating_continuation_plaintext']['words']
    solutions = []
    for i, result in enumerate(results, 1):
        encoder = Encoder({s: tuple(tuple(c) for c in cs)
                           for s, cs in result['encoder']['codebook'].items()})
        prediction = score(continuation, encoder, q.dictionary, q.ciphertext.words)
        exact = sum(r['fully_decoded'] and r['decoded_prefix'] == w
                    for r, w in zip(prediction['word_results'], truth_words))
        solutions.append({'number': i, 'result': result, 'prediction': prediction,
                          'exact_generating_words': exact})
        print(f"Solution {i}: training-compatible; dictionary={prediction['dictionary_words']}/4; exact={exact}/4")
    report = {'protocol': protocol, 'saved_explanation_audit': audit, 'attempts': attempts,
              'solutions': solutions, 'stop_reason': stop, 'complete': True,
              'generating_training_pair_compatible': accepts(saved['generating_truth']['plaintext']['words'], pairs)}
    write_json(output, report)
    return report


if __name__ == '__main__':
    run()
