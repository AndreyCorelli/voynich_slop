"""Fixed full-vocabulary contraction pilot; prepare by default, bounded probes optional."""
import argparse
from dataclasses import asdict, replace
import hashlib
import json
from pathlib import Path

from benchmarks.l3_conflict import verify
from voynich_smt.cipher.base import Bounds, generate_encoder, generate_ciphertext
from voynich_smt.data.corpus import digest, write_json
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.language.contractions import expand_units, tokenizations, tokenize_dictionary
from voynich_smt.language.dictionary import WordDictionary
from voynich_smt.models.alphabet import Alphabet
from voynich_smt.models.settings import HomophoneSelection
from voynich_smt.models.text import Text
from voynich_smt.solver.observed_codes import recover_observed_codes

BASELINE = Path('data/generated/clean-latin-voynich/inputs/words-23.json')
INVENTORY = Path('experiments/configs/latin-contractions.json')
ARTIFACTS = Path('data/generated/latin-mixed-comparison')
RESULTS = Path('experiments/results/latin-mixed-comparison')
PROFILES = ('letters','ae-only','bounded-seven')


def prepare(timeout_ms=1800000):
    payload = json.loads(BASELINE.read_text()); base = HiddenRecoveryRequest.from_dict(payload['request'])
    config = json.loads(INVENTORY.read_text())
    words = tuple(sorted(''.join(w) for w in base.dictionary.words))
    # Fixed spelling sample shared across profiles; not tuned to Voynich.
    sample = ('quae','per','est','contra','quorum')
    if not set(sample) <= set(words):
        raise ValueError('Calibration spellings absent from corrected vocabulary')
    folder = ARTIFACTS/f'budget-{timeout_ms}ms'; entries = []
    for profile in PROFILES:
        rules = [r for r in config['rules'] if r['id'] in config['profiles'][profile]]
        unit_words = tokenize_dictionary(words,rules)
        if {expand_units(w,rules) for w in unit_words} != set(words):
            raise ValueError('Expanded vocabulary changed')
        alpha = Alphabet(base.plaintext_alphabet.symbols + tuple('<'+r['id']+'>' for r in rules))
        q = replace(base,dictionary=WordDictionary(unit_words),plaintext_alphabet=alpha,
                    selection=HomophoneSelection('free'),timeout_ms=timeout_ms,max_word_length=None)
        plain = Text(tuple(min(tokenizations(w,rules),key=lambda p:(len(p),p)) for w in sample))
        # Same ciphertext alphabet and cipher bounds as the Voynich comparison.
        encoder = generate_encoder(alpha,base.ciphertext_alphabet,Bounds('verbose',2,2,2),7)
        cipher, choices = generate_ciphertext(plain,encoder,7)
        positive = replace(q,ciphertext=cipher)
        truth = {'status':'SAT','verified':True,'encoder':asdict(encoder),
                 'plaintext':asdict(plain),'choices':choices,'nulls':[]}
        verify(positive,truth)
        for kind,request in (('positive',positive),('voynich',q)):
            name=f'{profile}-{kind}'; inp=folder/'inputs'/f'{name}.json'
            public={'request':asdict(request),'codeword_domains':'observed'};write_json(inp,public)
            e={'id':name,'profile':profile,'kind':kind,'public_input':str(inp),
               'input_sha256':digest(public),'unit_dictionary_size':len(unit_words),
               'expanded_dictionary_size':len(words),'plaintext_alphabet_size':len(alpha.symbols)}
            if kind=='positive':
                tp=folder/'truth'/f'{name}.json';write_json(tp,truth)
                e.update(truth_path=str(tp),truth_sha256=digest(truth),expanded_plaintext=list(sample))
            entries.append(e)
        print(f'{profile}: {len(words)} spellings, {len(unit_words)} unit words',flush=True)
    report={'baseline_sha256':digest(payload),'inventory_sha256':digest(config),
            'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'tokenizer_sha256':hashlib.sha256(Path('src/voynich_smt/language/contractions.py').read_bytes()).hexdigest(),
            'timeout_ms':timeout_ms,'prepared_inputs':entries,
            'semantics':'Fixed letters/ae/seven inventory. Same corrected spelling vocabulary, Voynich block, ciphertext alphabet, H2/L1–3 prefix-free, free selection, no nulls. Active unit alphabets differ as required; unused letter alphabet retained. Earlier cyclic Latin UNSAT is not a free-selection baseline. Positives share five expanded spellings and seed, but ciphertext differs by profile. Synthetic calibration, not an attested passage or a matched shuffle.'}
    write_json(RESULTS/f'prepared-{timeout_ms}ms.json',report)
    return report


def probe(timeout_ms=10000):
    report=prepare(timeout_ms);report['experiments']=[]
    for e in report['prepared_inputs']:
        if e['kind']!='positive':continue
        payload=json.loads(Path(e['public_input']).read_text())
        q=HiddenRecoveryRequest.from_dict(payload['request'])
        result=asdict(recover_observed_codes(q));verify(q,result)
        if result['status']=='UNSAT':
            raise RuntimeError('Known positive incorrectly UNSAT')
        expanded=[]
        if result['status']=='SAT':
            config=json.loads(INVENTORY.read_text())
            rules=[r for r in config['rules'] if r['id'] in config['profiles'][e['profile']]]
            expanded=[expand_units(w,rules) for w in result['plaintext']['words']]
            source={''.join(w) for w in json.loads(BASELINE.read_text())['request']['dictionary']['words']}
            if not set(expanded)<=source:raise RuntimeError('Recovered spelling outside vocabulary')
        report['experiments'].append({**e,'result':result,'recovered_expanded_words':expanded})
        write_json(RESULTS/f'calibration-{timeout_ms}ms.json',report)
        print(f"{e['id']}: {result['status']}; solver={result['runtime_seconds']:.2f}s",flush=True)
    return report


def voynich_probe(timeout_ms=10000):
    calibration=json.loads((RESULTS/f'calibration-{timeout_ms}ms.json').read_text())
    report=prepare(timeout_ms)
    if calibration['baseline_sha256']!=report['baseline_sha256'] or calibration['inventory_sha256']!=report['inventory_sha256'] or calibration['tokenizer_sha256']!=report['tokenizer_sha256']:
        raise ValueError('Calibration source or tokenizer changed')
    report['experiments']=[];report['skipped_profiles']=[]
    for e in report['prepared_inputs']:
        if e['kind']!='voynich':continue
        control=next(c for c in calibration['experiments'] if c['profile']==e['profile'])
        positive=next(p for p in report['prepared_inputs'] if p['profile']==e['profile'] and p['kind']=='positive')
        if control['input_sha256']!=positive['input_sha256']:raise ValueError('Calibration input changed')
        cq=HiddenRecoveryRequest.from_dict(json.loads(Path(positive['public_input']).read_text())['request'])
        verify(cq,control['result'])
        if control['result']['status']!='SAT':
            report['skipped_profiles'].append(e['profile']);continue
        payload=json.loads(Path(e['public_input']).read_text());q=HiddenRecoveryRequest.from_dict(payload['request'])
        result=asdict(recover_observed_codes(q));verify(q,result)
        inventory=json.loads(INVENTORY.read_text())
        rules=[r for r in inventory['rules'] if r['id'] in inventory['profiles'][e['profile']]]
        expanded=([expand_units(w,rules) for w in result['plaintext']['words']] if result['status']=='SAT' else [])
        report['experiments'].append({**e,'result':result,'recovered_expanded_words':expanded})
        write_json(RESULTS/f'voynich-probe-{timeout_ms}ms.json',report)
        print(f"{e['id']}: {result['status']}; solver={result['runtime_seconds']:.2f}s",flush=True)
    write_json(RESULTS/f'voynich-probe-{timeout_ms}ms.json',report)
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--timeout-ms',type=int,default=1800000)
    parser.add_argument('--probe',action='store_true',help='Solve only three synthetic positives')
    parser.add_argument('--voynich-probe',action='store_true',help='Solve only profiles with saved verified SAT calibration at this budget')
    args=parser.parse_args()
    if args.timeout_ms<=0:parser.error('Positive budget required')
    if args.probe and args.voynich_probe:parser.error('Choose one probe mode')
    if args.voynich_probe:voynich_probe(args.timeout_ms)
    elif args.probe:probe(args.timeout_ms)
    else:prepare(args.timeout_ms)
