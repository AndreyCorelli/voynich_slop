"""Bounded hidden recovery gate for reversible contraction plus expansion."""
from dataclasses import asdict
import hashlib
import json
from pathlib import Path

from benchmarks.l3_conflict import verify
from voynich_smt.cipher.base import Bounds, generate_encoder, generate_ciphertext
from voynich_smt.data.corpus import digest, write_json
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.language.contractions import expand_units, tokenize_dictionary
from voynich_smt.language.dictionary import WordDictionary
from voynich_smt.models.alphabet import Alphabet
from voynich_smt.models.text import Text
from voynich_smt.solver.observed_codes import recover_observed_codes


def run():
    inventory = json.loads(Path('experiments/configs/latin-contractions.json').read_text())
    rules = inventory['rules']
    # Every predefined contraction is exercised; ae/per also remain spelled out.
    spellings = ('ae', 'per', 'pro', 'con', 'et', 'est', 'rum')
    dictionary = WordDictionary(tokenize_dictionary(spellings, rules))
    alphabet = Alphabet(tuple(sorted({s for w in dictionary.words for s in w})))
    plain = Text(tuple((('<'+r['id']+'>',) for r in rules)) + (tuple('ae'),tuple('per')))
    cipher_alphabet = Alphabet(tuple('0123456789ABCDEF'))
    generation_bounds = Bounds('verbose', 2, 2, 2)
    recovery_bounds = Bounds('verbose', 2, 1, 3)
    folder = Path('data/generated/mixed-contraction-gate')
    report = {'inventory_sha256':digest(inventory),
              'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'tokenizer_sha256':hashlib.sha256(Path('src/voynich_smt/language/contractions.py').read_bytes()).hexdigest(),
              'semantics':'Small synthetic gate, not a Latin passage or performance estimate. Every inventory unit exercised; complete optional tokenizations; hidden plaintext/key. Generate H2/L2, recover H2/L1–3 free prefix-free. No Voynich solves.', 'experiments':[]}
    for seed in (7,17,1729):
        encoder = generate_encoder(alphabet,cipher_alphabet,generation_bounds,seed)
        cipher, choices = generate_ciphertext(plain,encoder,seed)
        q = HiddenRecoveryRequest(cipher,alphabet,cipher_alphabet,recovery_bounds,dictionary,timeout_ms=10000)
        truth = {'status':'SAT','verified':True,'encoder':asdict(encoder),
                 'plaintext':asdict(plain),'choices':choices,'nulls':[]}
        verify(q,truth)
        public = {'request':asdict(q),'codeword_domains':'observed'}
        inp = folder/'inputs'/f'seed-{seed}.json';tp = folder/'truth'/f'seed-{seed}.json'
        write_json(inp,public);write_json(tp,truth)
        result = asdict(recover_observed_codes(q));verify(q,result)
        expanded = []
        if result['status']=='SAT':
            expanded = [expand_units(w,rules) for w in result['plaintext']['words']]
            if not all(w in spellings for w in expanded):
                raise RuntimeError('Recovered expansion outside source dictionary')
        report['experiments'].append({'seed':seed,'public_input':str(inp),'input_sha256':digest(public),
            'truth_path':str(tp),'truth_sha256':digest(truth),'generating_expanded_words':[expand_units(w,rules) for w in plain.words],
            'recovered_expanded_words':expanded,'result':result})
        write_json(Path('experiments/results/mixed-contraction-gate.json'),report)
        print(f"Seed {seed}: {result['status']}; verified={result['verified']}; solver={result['runtime_seconds']:.2f}s",flush=True)
    report['gate_passed'] = all(e['result']['status']=='SAT' and e['result']['verified'] for e in report['experiments'])
    write_json(Path('experiments/results/mixed-contraction-gate.json'),report)
    return report


if __name__ == '__main__':
    run()
