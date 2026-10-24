"""Trace short source-133 witness forms and prepare a conservative k/x exclusion."""
from collections import Counter, defaultdict
from dataclasses import asdict, replace
import hashlib
import json
from pathlib import Path
import tarfile
import xml.etree.ElementTree as ET

from benchmarks.german_selection import build_vocabulary, normalize_form
from benchmarks.l3_conflict import verify
from voynich_smt.data.corpus import digest, write_json
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.language.dictionary import WordDictionary

RESULT = Path('experiments/results/german-133-full-30-30min.json')
OUT = Path('experiments/results/german-short-form-audit.json')
INPUT = Path('data/generated/german-short-form-audit/133-without-k-x.json')


def occurrences(root):
    """Mirror vocabulary traversal while retaining raw forms and source context."""
    parents = {child: node for node in root.iter() for child in node}
    result = defaultdict(list)
    def walk(node):
        if node.tag in {'bibliographie', 'annotation', 'eingriff', 'ueberschrift'}:return
        if node.tag == 'wortform':
            ancestor = node;line = None
            while ancestor in parents:
                ancestor = parents[ancestor]
                if ancestor.tag == 'zeile':line = ancestor;break
            forms = [''.join(m.itertext()) for m in node.findall('morph')]
            annotation = node.find('annotation')
            context = [''.join(m.itertext()) for w in line.iter('wortform') for m in w.findall('morph')] if line is not None else []
            for morph in node.findall('morph'):
                raw = ''.join(morph.itertext())
                for word in normalize_form(raw) or []:
                    result[word].append({'word_number': node.get('nr'), 'raw_form': raw,
                        'parent_morph_forms': forms, 'annotation': dict(annotation.attrib) if annotation is not None else {},
                        'line_attributes': dict(line.attrib) if line is not None else {}, 'line_words': context,
                        'word_xml': ET.tostring(node, encoding='unicode')})
            return
        for child in node:walk(child)
    walk(root)
    return result


def run():
    saved = json.loads(RESULT.read_text());request = HiddenRecoveryRequest.from_dict(saved['request'])
    if saved['result']['status'] != 'SAT' or digest({'request': asdict(request), 'codeword_domains': 'observed'}) != saved['input_sha256']:
        raise ValueError('Verified full-block SAT input required')
    verify(request, saved['result'])
    vocabulary = build_vocabulary(133)
    if [''.join(w) for w in request.dictionary.words] != vocabulary['words']:
        raise ValueError('Witness vocabulary differs from source')
    with tarfile.open('data/raw/historical-lengths/german-corpus.tar.xz') as archive:
        raw = archive.extractfile('XML/133.xml').read()
    if hashlib.sha256(raw).hexdigest() != vocabulary['source']['xml_sha256']:
        raise ValueError('Source XML hash mismatch')
    found = occurrences(ET.fromstring(raw))
    if {w: len(items) for w,items in found.items()} != vocabulary['frequencies']:
        raise ValueError('Audit traversal differs from original vocabulary extraction')
    witness = [''.join(w) for w in saved['result']['plaintext']['words']]
    targets = sorted({w for w in witness if len(w) <= 3} | {'k', 'x', 'o'})
    audit = []
    for word in targets:
        audit.append({'word': word, 'witness_positions': [i+1 for i,w in enumerate(witness) if w == word],
                      'source_occurrence_count': len(found[word]), 'occurrences': found[word]})
    excluded = {'k', 'x'}
    clean = replace(request, dictionary=WordDictionary.from_strings(tuple(w for w in vocabulary['words'] if w not in excluded)), timeout_ms=30000)
    # Alphabet and all cipher parameters remain fixed for this dictionary-only sensitivity test.
    payload = {'request': asdict(clean), 'codeword_domains': 'observed'};write_json(INPUT, payload)
    report = {'schema_version': 1, 'source_id': 133, 'source': vocabulary['source'],
        'xml_sha256': hashlib.sha256(raw).hexdigest(), 'source_result_sha256': digest(saved),
        'vocabulary_sha256': digest(vocabulary), 'audit': audit,
        'findings': {'k_x': 'Unexplained standalone forms confined to repeated k x k prayer-instruction contexts. Not inside excluded editorial XML elements, but ordinary lexical status and expansion are unestablished.',
                     'o': 'Standalone source forms in O wye / O ... contexts support an interjection; retained.',
                     'aue': 'Source form in aue Maria prayer contexts; retained. This is not evidence of grammaticality of the solver sequence.',
                     'other_short_forms': 'All trace to retained source morph forms. Some appear as separately written parts grouped into one wortform; original corpus documentation section 4.2 explains that convention. Unknown annotation type is not an artifact test.'},
        'sensitivity_input': str(INPUT), 'sensitivity_input_sha256': digest(payload),
        'excluded_words': sorted(excluded), 'original_vocabulary_size': len(vocabulary['words']),
        'filtered_vocabulary_size': len(clean.dictionary.words), 'remaining_one_letter_words': ['o'],
        'current_witness_rejected_by_filtered_dictionary': not clean.dictionary.accepts(
            type(request.ciphertext)(tuple(tuple(w) for w in witness))),
        'status': 'PREPARED_NOT_SOLVED', 'solver_calls': 0,
        'semantics': 'Provenance audit, not a decipherment or definite identification of k/x as abbreviations. Excluding only these unexplained tokens is a sensitivity variant; original inputs/results remain intact. Ciphertext, original alphabet and all cipher rules unchanged; timeout set to 30 seconds. No speculative expansions added.'}
    write_json(OUT, report);print(f'Audited {len(targets)} short forms; k/x excluded in separate {len(clean.dictionary.words)}-word sensitivity input. No solver calls.')
    return report


if __name__ == '__main__':run()
