"""Audit surviving regional witnesses; prepare separate corrected full-block vocabularies."""
import argparse
from collections import Counter
from dataclasses import asdict, replace
import hashlib
import json
from pathlib import Path
import re
import tarfile
from time import perf_counter
import xml.etree.ElementTree as ET

from benchmarks.german_selection import build_vocabulary, normalize_form
from benchmarks.german_short_form_audit import occurrences
from benchmarks.l3_conflict import verify
from voynich_smt.data.corpus import digest, write_json
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.language.dictionary import WordDictionary
from voynich_smt.solver.observed_codes import recover_observed_codes

SOURCES = (123, 153, 233)
ROBUSTNESS = Path('experiments/results/german-vocabulary-robustness/budget-1800000ms.json')
FULL = Path('experiments/results/german-free-extension-30-30min.json')
ARTIFACTS = Path('data/generated/german-regional-audit')
RESULTS = Path('experiments/results/german-regional-audit')
# These are explicit sensitivity decisions, not expansions or claims of transcription error.
EXCLUSIONS = {
    123: {},
    153: {'b': 'Folio-side designation in fo 15 b; not treated as a lexical word.',
          'h': 'Mentioned alphabet letter in H wyrt ... boichstaue ... context.',
          'k': 'Mentioned alphabet letter.', 'q': 'Mentioned alphabet letter.',
          'x': 'Mentioned alphabet letter.', 'y': 'Mentioned alphabet letter.', 'z': 'Mentioned alphabet letter.',
          'u': 'Only occurrence is marked ú; isolated marked form has unestablished expansion.'},
    233: {'d': 'Only occurrence is isolated d before cleine...; lexical interpretation/expansion unresolved.',
          'q': 'Only occurrence follows quantity drytt halp; likely unit notation, expansion unestablished.',
          'v': 'Two isolated forms V/v; lexical interpretation/expansion unresolved.'},
}


def normalized_v2(raw):
    """Keep marked initial attached; quarantine uncertain or other editorial-marked forms."""
    if '?' in raw or '*' in raw:
        return None, 'quarantined_uncertain_or_marked'
    match = re.fullmatch(r'\[([A-Za-zäöüÄÖÜ]+)\]([A-Za-zäöüÄÖÜ].*)', raw)
    if match:
        return normalize_form(''.join(match.groups())), 'joined_marked_initial'
    if '[' in raw or ']' in raw:
        return None, 'quarantined_other_bracketed'
    return normalize_form(raw), 'unchanged_normalization'


def corrected_counts(root, exclusions):
    counts = Counter();events = []
    def walk(node):
        if node.tag in {'bibliographie', 'annotation', 'eingriff', 'ueberschrift'}:return
        if node.tag == 'wortform':
            for morph in node.findall('morph'):
                raw = ''.join(morph.itertext());words, action = normalized_v2(raw)
                if action != 'unchanged_normalization':
                    events.append({'word_number': node.get('nr'), 'raw_form': raw,
                                   'legacy_normalized': normalize_form(raw), 'corrected_normalized': words, 'action': action})
                for word in words or []:
                    if word in exclusions:
                        events.append({'word_number': node.get('nr'), 'raw_form': raw, 'normalized': word,
                                       'action': 'excluded_nonlexical_or_unresolved', 'reason': exclusions[word]})
                    else:counts[word] += 1
            return
        for child in node:walk(child)
    walk(root)
    return counts, events


def run(timeout_ms=30000, solve=False, resume=False):
    if type(timeout_ms) is not int or timeout_ms <= 0:raise ValueError('Positive integer budget required')
    robustness = json.loads(ROBUSTNESS.read_text());full = json.loads(FULL.read_text())
    model = HiddenRecoveryRequest.from_dict(full['request'])
    if len(model.ciphertext.words) != 30:raise ValueError('Expected full contiguous 30-word block')
    rows = []
    with tarfile.open('data/raw/historical-lengths/german-corpus.tar.xz') as archive:
        for n in SOURCES:
            entry = next(e for e in robustness['experiments'] if e['source_id'] == n)
            payload = json.loads(Path(entry['public_input']).read_text())
            if digest(payload) != entry['input_sha256'] or entry['result']['status'] != 'SAT':
                raise ValueError('Invalid surviving witness source')
            old_request = HiddenRecoveryRequest.from_dict(payload['request']);verify(old_request, entry['result'])
            vocabulary = build_vocabulary(n)
            if [''.join(w) for w in old_request.dictionary.words] != vocabulary['words']:
                raise ValueError('Original vocabulary mismatch')
            raw = archive.extractfile(f'XML/{n}.xml').read()
            if hashlib.sha256(raw).hexdigest() != vocabulary['source']['xml_sha256']:raise ValueError('XML hash mismatch')
            root = ET.fromstring(raw);found = occurrences(root)
            if {w:len(items) for w,items in found.items()} != vocabulary['frequencies']:
                raise ValueError('Audit traversal differs from original extraction')
            counts, events = corrected_counts(root, EXCLUSIONS[n]);words = sorted(counts)
            witness = [''.join(w) for w in entry['result']['plaintext']['words']]
            targets = sorted({w for w in witness if len(w) <= 3} | {w for w in found if len(w) == 1})
            clean = replace(old_request, ciphertext=model.ciphertext,
                            dictionary=WordDictionary.from_strings(tuple(words)), timeout_ms=timeout_ms)
            if replace(clean, dictionary=model.dictionary, plaintext_alphabet=model.plaintext_alphabet,
                       timeout_ms=model.timeout_ms) != model:
                raise ValueError('Full-block cipher model mismatch')
            public = {'request': asdict(clean), 'codeword_domains': 'observed'}
            path = ARTIFACTS/f'budget-{timeout_ms}ms'/'inputs'/f'{n}-full-30.json';write_json(path, public)
            new_vocabulary = {'schema_version': 2, 'source': vocabulary['source'], 'words': words,
                'frequencies': dict(sorted(counts.items())), 'normalization': 'Legacy historical normalization plus joined bracketed initial letters, whole-form quarantine for uncertainty/asterisk/remaining brackets, and explicit source-specific sensitivity exclusions.',
                'explicit_exclusions': EXCLUSIONS[n], 'events': events,
                'original_plaintext_alphabet_kept': list(old_request.plaintext_alphabet.symbols)}
            vp = ARTIFACTS/'vocabularies'/f'{n}-v2.json';write_json(vp, new_vocabulary)
            rows.append({'source_id': n, 'source': vocabulary['source'], 'original_vocabulary_size': len(vocabulary['words']),
                'corrected_vocabulary_size': len(words), 'removed_words': sorted(set(vocabulary['words'])-set(words)),
                'added_words': sorted(set(words)-set(vocabulary['words'])),
                'original_one_letter_words': sorted(w for w in vocabulary['words'] if len(w)==1),
                'remaining_one_letter_words': sorted(w for w in words if len(w)==1),
                'witness_words_missing_after_correction': sorted(set(witness)-set(words)),
                'audit': [{'word':w, 'witness_positions':[i+1 for i,x in enumerate(witness) if x==w],
                           'source_occurrence_count':len(found[w]), 'occurrences':found[w]} for w in targets],
                'normalization_events':events, 'explicit_exclusions': EXCLUSIONS[n],
                'vocabulary_path':str(vp), 'vocabulary_sha256':digest(new_vocabulary),
                'public_input':str(path), 'input_sha256':digest(public)})
    config = {'timeout_ms':timeout_ms, 'robustness_sha256':digest(robustness), 'full_block_sha256':digest(full),
              'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'vocabulary_sha256':{str(r['source_id']):r['vocabulary_sha256'] for r in rows}}
    report = {'schema_version':1, 'config':config, 'config_sha256':digest(config), 'rows':rows,
              'experiments':[], 'complete':False,
              'semantics':'Provenance audit and separately versioned normalization/lexical sensitivity variants. Original inputs/results preserved. Full 30-word text, original per-source plaintext alphabet and all cipher settings fixed. Prepared inputs have no truth hints. Original 19-word SAT witnesses are no longer dictionary-valid; replacement SAT/UNSAT has not been inferred from that fact.'}
    path = RESULTS/f'budget-{timeout_ms}ms.json'
    if path.exists():
        if not resume:raise ValueError('Existing checkpoint: use --resume')
        cached = json.loads(path.read_text())
        if cached['config_sha256'] != report['config_sha256']:raise ValueError('Resume requires unchanged source/code/budget')
        for e in cached['experiments']:
            row = next(r for r in rows if r['source_id']==e['source_id']);public=json.loads(Path(row['public_input']).read_text())
            if e['input_sha256'] != row['input_sha256'] or digest(public)!=row['input_sha256']:raise ValueError('Cached request mismatch')
            verify(HiddenRecoveryRequest.from_dict(public['request']), e['result'])
        report['experiments']=cached['experiments']
    write_json(path, report)
    print(f'Audited sources {SOURCES}; separate corrected full-block inputs saved to {path}', flush=True)
    if not solve:return report
    done={e['source_id'] for e in report['experiments']}
    for row in rows:
        if row['source_id'] in done:continue
        public=json.loads(Path(row['public_input']).read_text())
        if digest(public)!=row['input_sha256']:raise ValueError('Public input hash mismatch')
        q=HiddenRecoveryRequest.from_dict(public['request'])
        print(f'Corrected German {row["source_id"]}: vocabulary={row["corrected_vocabulary_size"]}; budget={timeout_ms}ms',flush=True)
        begin=perf_counter();result=asdict(recover_observed_codes(q));verify(q,result)
        report['experiments'].append({'source_id':row['source_id'],'input_sha256':row['input_sha256'],
                                     'result':result,'wall_seconds':perf_counter()-begin})
        write_json(path,report);print(f'  {result["status"]}; solver={result["runtime_seconds"]:.2f}s',flush=True)
    report['complete']=True
    report['summary']={s:[e['source_id'] for e in report['experiments'] if e['result']['status']==s] for s in ('SAT','UNSAT','UNKNOWN')}
    write_json(path,report)
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--timeout-ms',type=int,default=30000)
    parser.add_argument('--solve',action='store_true')
    parser.add_argument('--resume',action='store_true')
    args=parser.parse_args()
    run(args.timeout_ms,args.solve,args.resume)
