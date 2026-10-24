"""Seven bounded contraction-aware recovery stages on contiguous cached Latin."""
import argparse
from collections import Counter
from dataclasses import asdict, replace
from functools import lru_cache
import json
from pathlib import Path
import random
import subprocess
import sys
from time import perf_counter

from benchmarks.frozen_key_holdout import decode_word
from benchmarks.german_shuffle_controls import typewise_shuffle
from benchmarks.l3_conflict import verify
from voynich_smt.cipher.base import Bounds, Encoder, generate_ciphertext
from voynich_smt.data.corpus import digest, write_json
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.language.dictionary import WordDictionary
from voynich_smt.models.alphabet import Alphabet
from voynich_smt.models.text import Text

OUT = Path('experiments/results/contraction-hidden-calibration')
CONFIG = Path('experiments/configs/latin-contractions-broader-v1.json')
SOURCE = Path('experiments/results/broader-contraction-capacity/prepared.json')


def core(config):
    ids = set(config['profiles']['broader-core'])
    return [r for r in config['rules'] if r['id'] in ids]


def parts(rule):
    # Exact graphic-unit COST, abstract distinct labels (not transcribed historic glyphs).
    n = rule['units']
    return tuple((f"<{rule['id']}-part-{j}>",
                  rule['expansion'][j:j+1] if j < n-1 else rule['expansion'][j:]) for j in range(n))


def expansion_table(rules):
    return {label: expansion for r in rules for label, expansion in parts(r)}


def expand(path, table):
    return ''.join(table[t] if t in table else t if len(t) == 1 and t.isalpha()
                   else _unknown(t) for t in path)


def _unknown(token):
    raise ValueError('Unknown unit: '+token)


def applies(word, i, rule):
    end = i + len(rule['expansion'])
    return (word.startswith(rule['expansion'], i)
            and (rule['position'] not in ('initial', 'whole') or i == 0)
            and (rule['position'] not in ('final', 'whole') or end == len(word))
            and (not rule.get('left') or i > 0 and word[i-1] == rule['left']))


def variants(word, rules, cap=4096):
    @lru_cache(None)
    def visit(i):
        if i == len(word):
            return ((),)
        edges = [(i+1, (word[i],))]
        edges += [(i+len(r['expansion']), tuple(label for label, _ in parts(r)))
                  for r in rules if applies(word, i, r)]
        out = set()
        for end, labels in edges:
            out.update(labels+tail for tail in visit(end))
            if len(out) > cap:
                raise ValueError('Complete variants exceed frozen cap')
        return tuple(sorted(out))
    return visit(0)


def natural_fixture(source, rules, seed):
    segments = source['segments']
    # Largest preserved segment, midpoint; only move past excluded-token barriers.
    segment_index = max(range(len(segments)), key=lambda i: len(segments[i]))
    segment = segments[segment_index]
    start = len(segment)//2
    while start+40 <= len(segment) and any(w is None for w in segment[start:start+40]):
        start += 1
    train, held = segment[start:start+32], segment[start+32:start+40]
    if len(held) != 8 or any(w is None for w in train+held):
        raise ValueError('No contiguous passage under fixed selection rule')
    reference = [w for w in segment[:len(segment)//2] if w is not None]
    counts = Counter(reference)
    top = sorted(counts, key=lambda w: (-counts[w], w))[:64]
    words = sorted(set(top+train))
    return {'seed': seed, 'segment_index': segment_index, 'start': start,
            'train': train, 'held': held, 'reference_counts': dict(counts),
            'vocabulary': words, 'reference_range': [0, len(segment)//2],
            'canonical_train': [min(variants(w, rules), key=lambda p: (len(p), p)) for w in train],
            'canonical_held': [min(variants(w, rules), key=lambda p: (len(p), p)) for w in held]}


def prepare():
    config = json.loads(CONFIG.read_text())
    source = json.loads(SOURCE.read_text())
    rules = core(config)
    files = [Path(__file__), Path('benchmarks/l3_conflict.py'),
             Path('benchmarks/frozen_key_holdout.py'), Path('benchmarks/german_shuffle_controls.py')]
    files += list(Path('src/voynich_smt/solver').glob('*.py'))
    p = {'inventory_sha256': digest(config), 'source_sha256': digest(source),
         'rules': rules, 'expansions': expansion_table(rules),
         'fixtures': {name: natural_fixture(source['sources'][name], rules, seed)
                      for name, seed in [('caesar', 47001), ('aquinas', 47002), ('einhard', 47003)]},
         'code_sha256': {str(f): digest(f.read_text()) for f in files},
         'solver_ms': 5000, 'worker_wall_seconds': 45,
         'protocol': 'Freeze 27-rule core, complete optional dictionary paths and cheapest generating tokenizations. Multi-unit macros use distinct expansion-labelled parts preserving retained-unit costs, not historic glyph identity. No ambiguous nasal rules. Contiguous 32+8 words at midpoint of largest preserved segment; no coverage/fit-based passage replacement. Dictionary: top64 reference words plus distinct training words, never heldout reservation. Thus training-assisted vocabulary, not fully blind. Independent random H2 choices, prefix-free keys. Public worker input contains no plaintext/key/lengths; oracle offsets separately labeled. First SAT key frozen, no ranking or repair. Five-second solver and45-second worker limits; no timeout ladder. Controls shuffle full passage typewise before train/holdout split. Seven stages: reversible audit; CaesarH1fixed1; CaesarH2fixed1; CaesarH2mixed1-2; mixed oracle diagnosis; independent Aquinas and Einhard replicate highest-complexity family predicting>=6/8 exact with>=4 novel exact on Caesar, otherwise H1 diagnostic. Never use oracle success to choose hidden family. Stop after7, no Voynich search.'}
    p = json.loads(json.dumps(p))
    path = OUT/'prepared.json'
    if path.exists():
        assert json.loads(path.read_text()) == p, 'Frozen code/source changed'
    else:
        write_json(path, p)
    return p


def encoder_for(alphabet, h, mixed, seed):
    rng = random.Random(seed)
    needed = len(alphabet.symbols)*h
    if not mixed:
        glyphs = tuple(f'g{i}' for i in range(needed))
        pool = [(g,) for g in glyphs]
        rng.shuffle(pool)
    else:
        glyphs = tuple(f'g{i}' for i in range(24))
        single_count = min(12, max(1, needed//3))
        singles = [(g,) for g in glyphs[:single_count]]
        doubles = [(a, b) for a in glyphs[single_count:] for b in glyphs]
        rng.shuffle(doubles)
        pool = singles + doubles[:needed-single_count]
        if len(pool) != needed:
            raise ValueError('Prefix code capacity exceeded')
        rng.shuffle(pool)
    return Encoder({s: tuple(pool[h*i:h*i+h]) for i, s in enumerate(alphabet.symbols)}), Alphabet(glyphs)


def make_case(p, source, h, mixed, contracted, oracle=False):
    fixture = p['fixtures'][source]
    rules = p['rules'] if contracted else []
    dictionary = WordDictionary(tuple(sorted({v for w in fixture['vocabulary'] for v in variants(w, rules)})))
    alphabet = Alphabet(tuple(sorted({u for w in dictionary.words for u in w})))
    encoder, ca = encoder_for(alphabet, h, mixed, fixture['seed'])
    plain = Text(tuple(min(variants(w, rules), key=lambda path: (len(path), path)) for w in fixture['train']))
    held = Text(tuple(min(variants(w, rules), key=lambda path: (len(path), path)) for w in fixture['held']))
    missing = set(u for w in held.words for u in w)-set(alphabet.symbols)
    # Keep unknown-unit holdouts explicit, never extend the fitting alphabet with them.
    rng = random.Random(fixture['seed']+100)
    held_book = dict(encoder.codebook)
    if missing:
        # Reserve unused prefix-tree leaves; only truth evaluation gains these mappings.
        used = {c for cs in held_book.values() for c in cs}
        possible = [(g,) for g in ca.symbols] if not mixed else [(a,b) for a in ca.symbols for b in ca.symbols]
        available = [c for c in possible if all(c[:len(v)] != v and v[:len(c)] != c for v in used)]
        # Fixed-one keys use all glyphs: extend public ciphertext alphabet, not plaintext alphabet.
        if not mixed:
            extra = tuple(f'unseen{i}' for i in range(h*len(missing)))
            ca = Alphabet(ca.symbols+extra); available = [(g,) for g in extra]
        if len(available) < h*len(missing):
            raise ValueError('No heldout truth-code capacity')
        rng.shuffle(available)
        for i, s in enumerate(sorted(missing)):
            held_book[s] = tuple(available[h*i:h*i+h])
    full_encoder = Encoder(held_book)
    train_cipher, choices = generate_ciphertext(plain, encoder, fixture['seed']+1)
    held_cipher, held_choices = generate_ciphertext(held, full_encoder, fixture['seed']+2)
    bounds = Bounds('verbose', h, 1, 2 if mixed else 1)
    request = HiddenRecoveryRequest(train_cipher, alphabet, ca, bounds, dictionary,
                                   timeout_ms=p['solver_ms'], dictionary_encoding='trie')
    truth = {'status': 'SAT', 'verified': True, 'encoder': asdict(encoder),
             'plaintext': asdict(plain), 'choices': choices, 'nulls': []}
    verify(request, truth)
    shuffled, metadata = typewise_shuffle(Text(train_cipher.words+held_cipher.words), fixture['seed']+3)
    control_request = replace(request, ciphertext=Text(shuffled.words[:32]))
    # Oracle offsets computed here, never included in ordinary hidden requests.
    cursor = 0; segmentation = []
    for word in plain.words:
        segmentation.append(tuple(len(encoder.codebook[s][choices[cursor+i]]) for i,s in enumerate(word)))
        cursor += len(word)
    seen = {encoder.codebook[s][choice] for s,choice in zip((s for w in plain.words for s in w),choices)}
    held_cursor = 0; coverage = []
    for word in held.words:
        codes = [full_encoder.codebook[s][held_choices[held_cursor+i]] for i,s in enumerate(word)]
        coverage.append(all(c in seen for c in codes)); held_cursor += len(word)
    return {'request': asdict(request), 'control_request': asdict(control_request),
            'truth': truth, 'held_plaintext': fixture['held'], 'held_units': asdict(held),
            'held_cipher': asdict(held_cipher), 'control_held_cipher': asdict(Text(shuffled.words[32:])),
            'control_metadata': metadata, 'generating_covered_mask': coverage,
            'missing_held_units': sorted(missing), 'held_dictionary_mask': [w in fixture['vocabulary'] for w in fixture['held']],
            'oracle_segmentation': segmentation if oracle else None,
            'contracted': contracted, 'source': source, 'h': h, 'mixed': mixed,
            'generation_roundtrip': full_encoder.decode(held_cipher) == held,
            'training_letters': sum(map(len, fixture['train'])), 'training_units': plain.size,
            'training_glyphs': train_cipher.size}


def prediction(case, result, p, control=False):
    if result['status'] != 'SAT':
        return {'status': 'NOT_EVALUATED_NO_SAT'}
    enc = Encoder({s: tuple(tuple(c) for c in cs) for s, cs in result['encoder']['codebook'].items()})
    field = 'control_held_cipher' if control else 'held_cipher'
    train = case['control_request' if control else 'request']['ciphertext']['words']
    rows = []
    for i, word in enumerate(case[field]['words']):
        d = decode_word(tuple(word), enc)
        form = expand(d['decoded_prefix'], p['expansions']) if d['fully_decoded'] else None
        novel = list(word) not in train
        row = {**d, 'expanded_word': form, 'novel_ciphertext': novel,
               'dictionary_hit': form in p['fixtures'][case['source']]['vocabulary'] if form else False}
        if not control:
            row.update(exact=form == case['held_plaintext'][i],
                       generating_codes_seen=case['generating_covered_mask'][i],
                       held_in_dictionary=case['held_dictionary_mask'][i])
        rows.append(row)
    return {'status': 'EVALUATED_FROZEN_KEY', 'words': rows,
            'decoded': sum(r['fully_decoded'] for r in rows),
            'dictionary_hits': sum(r['dictionary_hit'] for r in rows),
            'novel_words': sum(r['novel_ciphertext'] for r in rows),
            'exact': None if control else sum(r['exact'] for r in rows),
            'novel_exact': None if control else sum(r['exact'] and r['novel_ciphertext'] for r in rows)}


def worker(input_path, output_path):
    # Deliberately loads only public request plus explicitly labelled oracle offsets.
    from voynich_smt.solver.recovery import _recover
    public = json.loads(Path(input_path).read_text())
    q = HiddenRecoveryRequest.from_dict(public['request'])
    started = perf_counter()
    result = asdict(_recover(None, q.ciphertext, q.plaintext_alphabet, q.ciphertext_alphabet,
        q.bounds, q.timeout_ms, dictionary=q.dictionary,
        max_word_length=max(map(len, q.dictionary.words)), dictionary_encoding=q.dictionary_encoding,
        codeword_domains='observed', known_segmentation=public.get('oracle_segmentation')))
    elapsed = perf_counter()-started
    verify(q, result)
    write_json(Path(output_path), {'public_sha256': digest(public), 'result': result,
        'fit_wall_seconds': elapsed, 'construction_and_extra_seconds': max(0, elapsed-result['runtime_seconds'])})


def fit(p, stage, name, case, control=False, oracle=False):
    folder = OUT/f'iteration-{stage}'
    public = {'request': case['control_request' if control else 'request']}
    if oracle:
        public['oracle_segmentation'] = case['oracle_segmentation']
    inp = folder/f'{name}-input.json'; out = folder/f'{name}-result.json'
    if inp.exists():
        assert json.loads(inp.read_text()) == json.loads(json.dumps(public))
    else:
        write_json(inp, public)
    if not out.exists():
        print(f'Iteration {stage}: {name} (5s solver /45s worker)', flush=True)
        started = perf_counter()
        try:
            completed = subprocess.run([sys.executable, '-m', 'benchmarks.contraction_hidden_calibration',
                '--worker', str(inp), '--output', str(out)], capture_output=True, text=True,
                timeout=p['worker_wall_seconds'])
            if completed.returncode:
                raise RuntimeError(completed.stderr[-4000:])
        except subprocess.TimeoutExpired:
            write_json(out, {'public_sha256': digest(public), 'result': {'status': 'WALL_TIMEOUT', 'verified': False},
                'fit_wall_seconds': perf_counter()-started})
    saved = json.loads(out.read_text())
    assert saved['public_sha256'] == digest(public)
    q = HiddenRecoveryRequest.from_dict(public['request'])
    verify(q, saved['result'])
    if not control and saved['result']['status'] == 'UNSAT':
        raise RuntimeError('Known verified positive unexpectedly UNSAT')
    evaluated = prediction(case, saved['result'], p, control)
    row = {'name': name, 'control': control, 'oracle': oracle, 'case_sha256': digest(case),
           **saved, 'prediction': evaluated}
    print(name, saved['result']['status'], 'exact', evaluated.get('exact'),
          'novel', evaluated.get('novel_exact'), 'dictionary', evaluated.get('dictionary_hits'), flush=True)
    return row


def choose_family(previous):
    for index, h, mixed in [(4,2,True),(3,2,False),(2,1,False)]:
        row = next(r for r in previous[index]['rows'] if r['name'] == 'contracted-positive')
        ev = row['prediction']
        if ev.get('exact', 0) >= 6 and ev.get('novel_exact', 0) >= 4:
            return h, mixed, 'Highest-complexity hidden Caesar arm meeting fixed exact/novel gate'
    return 1, False, 'No hidden arm passed; replicate simplest diagnostic, not a validated family'


def run():
    p = prepare(); stages = {}
    for i in range(1,8):
        path = OUT/f'iteration-{i}.json'
        if path.exists():
            stages[i] = json.loads(path.read_text()); continue
        previous = stages.get(i-1)
        plan = {'iteration': i, 'prepared_sha256': digest(p), 'previous_sha256': digest(previous) if previous else None}
        rows = []; cases = {}
        if i == 1:
            plan['purpose'] = 'Independently audit complete paths, core retained costs and generator roundtrips before recovery'
            write_json(OUT/f'plan-{i}.json', plan)
            checks = 0
            for r in p['rules']:
                assert len(parts(r)) == r['units']
                assert expand(tuple(x for x,_ in parts(r)), p['expansions']) == r['expansion']
            for fixture in p['fixtures'].values():
                for w in set(fixture['vocabulary']+fixture['held']):
                    paths = variants(w, p['rules'])
                    assert tuple(w) in paths
                    for unit_path in paths:
                        assert expand(unit_path, p['expansions']) == w; checks += 1
            for source in p['fixtures']:
                for h,mixed in [(1,False),(2,False),(2,True)]:
                    case = make_case(p, source, h, mixed, True)
                    assert case['generation_roundtrip']
            assessment = {'path_roundtrips': checks, 'generator_roundtrips': 9,
                          'decision': 'Proceed to simplest hidden contraction-key diagnostic'}
        else:
            source = 'caesar' if i < 6 else 'aquinas' if i == 6 else 'einhard'
            h, mixed = (1,False) if i==2 else (2,False) if i==3 else (2,True)
            if i>=6:
                h,mixed,reason = choose_family(stages)
                plan['selection_reason'] = reason
            oracle = i == 5
            plan.update(source=source, h=h, mixed=mixed, oracle=oracle,
                        purpose='Oracle boundary diagnosis, never hidden evidence' if oracle else
                        'Paired letters/contractions and matched contracted shuffle; first keys, frozen holdout')
            write_json(OUT/f'plan-{i}.json', plan)
            for contracted in (True, False):
                case = make_case(p, source, h, mixed, contracted, oracle)
                label = 'contracted' if contracted else 'letters'
                cases[label] = case
                write_json(OUT/f'iteration-{i}'/f'{label}-fixture.json', case)
                rows.append(fit(p, i, label+'-positive', case, oracle=oracle))
                if contracted and not oracle:
                    rows.append(fit(p, i, 'contracted-shuffle', case, control=True))
            assessment = {'statuses': {r['name']: r['result']['status'] for r in rows},
                'holdout': {r['name']: {k: r['prediction'].get(k) for k in ('exact','novel_exact','decoded','dictionary_hits')} for r in rows},
                'capacity': {label: {k: case[k] for k in ('training_letters','training_units','training_glyphs','missing_held_units','held_dictionary_mask','generating_covered_mask')} for label,case in cases.items()},
                'decision': 'Replicate only hidden passing family; otherwise simplest diagnostic; never increase timeouts or alter inventory'}
        row = {'plan': plan, 'cases': cases, 'rows': rows, 'assessment': assessment}
        write_json(path, row); stages[i] = json.loads(path.read_text())
        print('Completed iteration', i, flush=True)
    write_json(OUT/'report.json', {'prepared_sha256': digest(p), 'complete': True,
        'iterations': [{ 'iteration': i, 'assessment': s['assessment']} for i,s in stages.items()],
        'solver_calls': sum(len(s['rows']) for s in stages.values()),
        'selected_replication_family': choose_family(stages)})
    return stages


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', action='store_true'); parser.add_argument('--worker'); parser.add_argument('--output')
    args = parser.parse_args()
    if args.worker:
        worker(args.worker, args.output)
    elif args.run:
        run()
    else:
        prepare()
