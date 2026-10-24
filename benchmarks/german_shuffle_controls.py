"""Matched glyph-shuffle controls for corrected Swabian/Alsatian full-block SAT fits."""
import argparse
from collections import Counter
from copy import deepcopy
from dataclasses import asdict, replace
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import random
from time import perf_counter

from benchmarks.l3_conflict import verify
from voynich_smt.cipher.base import Encoder
from voynich_smt.data.controls import control
from voynich_smt.data.corpus import digest, write_json
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.models.text import Text
from voynich_smt.solver.observed_codes import recover_observed_codes

BASELINE = Path('experiments/results/german-regional-audit/budget-1800000ms.json')
ARTIFACTS = Path('data/generated/german-shuffle-controls')
RESULTS = Path('experiments/results/german-shuffle-controls')
SEEDS = (7, 17, 1729)
SOURCES = (123, 233)


def repetition_partition(text):
    first = {};return tuple(first.setdefault(w, i) for i,w in enumerate(text.words))


def typewise_shuffle(text, seed):
    """Same permutation per identical word; reject collisions and unchanged draws."""
    rng = random.Random(seed);types = list(dict.fromkeys(text.words))
    for attempt in range(1000):
        mapping = {}
        for word in types:
            out = list(word);rng.shuffle(out);mapping[word] = tuple(out)
        if len(set(mapping.values())) != len(types):continue
        shuffled = Text(tuple(mapping[w] for w in text.words))
        if shuffled != text:
            return shuffled, {'kind': 'typewise-within-word-shuffle', 'seed': seed,
                'generator_version': 1, 'rejected_draws': attempt,
                'preserves': ['word-length sequence', 'global glyph counts', 'per-word glyph counts', 'exact equality partition of words']}
    raise ValueError('Unable to generate a changed collision-free word-type shuffle')


def positive_control(request, result, seed):
    """Resample valid homophone choices for the verified plaintext at fixed word lengths."""
    if request.selection.mode != 'free' or request.nulls.enabled:
        raise ValueError('Positive resampling requires free selection without nulls')
    verify(request, result)
    encoder = Encoder({s:tuple(tuple(c) for c in codes) for s,codes in result['encoder']['codebook'].items()})
    plain = Text(tuple(tuple(w) for w in result['plaintext']['words']))
    rng = random.Random(seed)
    samplers = []
    for word, cipher in zip(plain.words, request.ciphertext.words):
        # Default arguments bind this word's closure independently.
        def make_sampler(word, target):
            @lru_cache(None)
            def ways(i, remaining):
                if remaining < 0:return 0
                if i == len(word):return int(remaining == 0)
                return sum(ways(i+1, remaining-len(c)) for c in encoder.codebook[word[i]])
            def sample():
                remaining = target;out = []
                for i,s in enumerate(word):
                    options = [(k, ways(i+1, remaining-len(c))) for k,c in enumerate(encoder.codebook[s])]
                    draw = rng.randrange(sum(n for _,n in options))
                    for k,n in options:
                        if draw < n:out.append(k);remaining -= len(encoder.codebook[s][k]);break
                        draw -= n
                return out
            return sample, ways(0, target)
        samplers.append(make_sampler(word, len(cipher)))
    for attempt in range(100):
        choices = tuple(c for sampler,_ in samplers for c in sampler())
        text = encoder.encode(plain, choices)
        if text != request.ciphertext or all(count == 1 for _,count in samplers):break
    public = replace(request, ciphertext=text)
    truth = {'status': 'SAT', 'verified': True, 'encoder': asdict(encoder), 'plaintext': asdict(plain),
             'choices': choices, 'nulls': [], 'generator': {'kind': 'length-conditioned-free-choice-resampling',
                'seed': seed, 'changed_from_source': text != request.ciphertext,
                'choice_assignment_counts_by_word': [n for _,n in samplers],
                'scope': 'Uses fitted key and plaintext; calibration control, not an independent language sample. Word lengths matched, glyph counts and word repetitions need not match.'}}
    verify(public, truth)
    return public, truth


def prepare(timeout_ms):
    if type(timeout_ms) is not int or timeout_ms <= 0:raise ValueError('Positive integer budget required')
    baseline = json.loads(BASELINE.read_text());requests = {};results = {}
    for n in SOURCES:
        row = next(r for r in baseline['rows'] if r['source_id'] == n)
        saved = next(e for e in baseline['experiments'] if e['source_id'] == n)
        payload = json.loads(Path(row['public_input']).read_text())
        if digest(payload) != row['input_sha256'] or saved['input_sha256'] != row['input_sha256'] or saved['result']['status'] != 'SAT':
            raise ValueError('Corrected verified SAT baseline required')
        q = HiddenRecoveryRequest.from_dict(payload['request']);verify(q,saved['result'])
        if q.selection.mode != 'free' or q.nulls.enabled or len(q.ciphertext.words) != 30:
            raise ValueError('Expected full 30-word free-selection baseline')
        requests[n] = replace(q, timeout_ms=timeout_ms);results[n] = saved['result']
    original = requests[123].ciphertext
    if original != requests[233].ciphertext:raise ValueError('Same ciphertext required for paired controls')
    for n in SOURCES:
        if replace(requests[n], dictionary=requests[123].dictionary, plaintext_alphabet=requests[123].plaintext_alphabet) != requests[123]:
            raise ValueError('Paired models differ beyond vocabulary/alphabet')
    folder = ARTIFACTS/f'budget-{timeout_ms}ms';entries = []
    for seed in SEEDS:
        tight, meta = typewise_shuffle(original, seed)
        broad, broad_meta = control(original, 'frequency-shuffle', seed)
        broad_meta = {**broad_meta, 'preserves': ['word-length sequence', 'global glyph counts'],
                      'not_preserved': ['per-word glyph counts', 'word equality partition']}
        for family,text,metadata in (('typewise',tight,meta),('frequency',broad,broad_meta)):
            assert tuple(map(len,text.words)) == tuple(map(len,original.words))
            assert Counter(g for w in text.words for g in w) == Counter(g for w in original.words for g in w)
            if family == 'typewise':
                assert repetition_partition(text) == repetition_partition(original)
                assert all(Counter(a)==Counter(b) for a,b in zip(text.words,original.words))
            for n in SOURCES:
                q = replace(requests[n],ciphertext=text)
                payload = {'request':asdict(q),'codeword_domains':'observed'}
                name = f'{n}-{family}-seed-{seed}';path = folder/'inputs'/f'{name}.json';write_json(path,payload)
                entries.append({'id':name,'source_id':n,'kind':'shuffle','family':family,'seed':seed,
                    'generator':metadata,'ciphertext_sha256':digest(asdict(text)),
                    'public_input':str(path),'input_sha256':digest(payload),
                    'original_unique_words':len(set(original.words)), 'control_unique_words':len(set(text.words))})
    for n in SOURCES:
        for seed in SEEDS[:2]:
            q, truth = positive_control(requests[n], results[n], seed)
            name = f'{n}-positive-seed-{seed}';path = folder/'inputs'/f'{name}.json';tp = folder/'truth'/f'{name}.json'
            payload = {'request':asdict(q),'codeword_domains':'observed'};write_json(path,payload);write_json(tp,truth)
            entries.append({'id':name,'source_id':n,'kind':'positive','family':'resampled-positive','seed':seed,
                'generator':truth['generator'],'public_input':str(path),'input_sha256':digest(payload),
                'truth_path':str(tp),'truth_sha256':digest(truth),'generating_witness_verified':True})
    config = {'timeout_ms':timeout_ms,'baseline_sha256':digest(baseline), 'seeds':list(SEEDS),
              'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'input_sha256':{e['id']:e['input_sha256'] for e in entries}}
    return {'schema_version':1,'config':config,'config_sha256':digest(config),
            'original_results':[{'source_id':n,'status':'SAT','verified':True,'solver_seconds':results[n]['runtime_seconds']} for n in SOURCES],
            'prepared_inputs':entries,'experiments':[],'complete':False,
            'semantics':'Paired corrected source-123/233 models; 3 seeds per shuffle family. Free selection, original full 30-word block length sequence and global glyph counts fixed for shuffles. Typewise shuffles also preserve per-word multisets and exact repeated-word relationships. Whole-word reordering cannot discriminate this model. Positive controls reuse fitted plaintext/key with new length-conditioned free choices, not independent language samples. No SAT/UNSAT/UNKNOWN confusion or language significance claim.'}


def run(timeout_ms=30000, solve=False, resume=False, max_solves=16):
    if type(max_solves) is not int or max_solves < 1:raise ValueError('Positive maximum solves required')
    report = prepare(timeout_ms);output = RESULTS/f'budget-{timeout_ms}ms.json'
    if output.exists():
        if not resume:raise ValueError('Existing checkpoint: use --resume')
        cached=json.loads(output.read_text())
        if cached['config_sha256'] != report['config_sha256']:raise ValueError('Resume requires same sources, code, controls and budget')
        seen=set()
        for row in cached['experiments']:
            entry=next(e for e in report['prepared_inputs'] if e['id']==row['id'])
            if row['id'] in seen or row['input_sha256'] != entry['input_sha256']:raise ValueError('Cached input mismatch')
            seen.add(row['id']);payload=json.loads(Path(entry['public_input']).read_text())
            if digest(payload)!=entry['input_sha256']:raise ValueError('Public input hash mismatch')
            verify(HiddenRecoveryRequest.from_dict(payload['request']),row['result'])
            if entry['kind']=='positive' and row['result']['status']=='UNSAT':raise RuntimeError('Positive control incorrectly UNSAT')
        report['experiments']=cached['experiments']
    write_json(output,report)
    print(f'Prepared 12 paired shuffles and 4 verified positive controls; saved {output}',flush=True)
    if not solve:return report
    done={e['id'] for e in report['experiments']};solves=0
    for entry in report['prepared_inputs']:
        if entry['id'] in done:continue
        if solves >= max_solves:break
        payload=json.loads(Path(entry['public_input']).read_text())
        if digest(payload)!=entry['input_sha256']:raise ValueError('Public input hash mismatch')
        request=HiddenRecoveryRequest.from_dict(payload['request'])
        print(f'{entry["id"]}: budget={timeout_ms}ms',flush=True)
        begin=perf_counter();result=asdict(recover_observed_codes(request));verify(request,result)
        report['experiments'].append({**entry,'result':result,'wall_seconds':perf_counter()-begin})
        solves+=1;write_json(output,report);print(f'  {result["status"]}; solver={result["runtime_seconds"]:.2f}s',flush=True)
        if entry['kind']=='positive' and result['status']=='UNSAT':raise RuntimeError('Known positive control incorrectly UNSAT')
    report['complete']=len(report['experiments'])==len(report['prepared_inputs'])
    report['summary']=[{'source_id':n,'family':family,
        **{s:sum(e['source_id']==n and e['family']==family and e['result']['status']==s for e in report['experiments']) for s in ('SAT','UNSAT','UNKNOWN')},
        'NOT_RUN':sum(e['source_id']==n and e['family']==family and e['id'] not in {r['id'] for r in report['experiments']} for e in report['prepared_inputs'])}
        for n in SOURCES for family in ('typewise','frequency','resampled-positive')]
    write_json(output,report)
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--timeout-ms',type=int,default=30000)
    parser.add_argument('--max-solves',type=int,default=16)
    parser.add_argument('--solve',action='store_true')
    parser.add_argument('--resume',action='store_true')
    args=parser.parse_args();run(args.timeout_ms,args.solve,args.resume,args.max_solves)
