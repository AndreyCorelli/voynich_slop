"""Freeze independent source resources, then prepare a work-disjoint continuous cipher.

Resource construction accepts only training text and an external dictionary.
Preparation retains every target token, including out-of-inventory words.
"""
import argparse
from collections import Counter
import hashlib
from itertools import chain
import json
from pathlib import Path
import re

from benchmarks.scalable_english_build import documents
from voynich_smt.word_mapping.scalable.data import generate, tokenize
from voynich_smt.word_mapping.scalable.inventory import Inventory
from voynich_smt.word_mapping.scalable.sparse_lm import SparseBigram
from voynich_smt.word_mapping.scalable.trigram import load_model

AUSTEN = 'It is a truth universally acknowledged,'
WELLS = 'No one would have believed'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prose(path, incipit):
    text = path.read_text(encoding='utf-8-sig')
    end = re.search(r'^\*\*\* END OF (?:THE|THIS) PROJECT GUTENBERG EBOOK.*$', text, re.M)
    anchor = re.search(r'\s+'.join(re.escape(part) for part in incipit.split()),
                       text[:end.start()] if end is not None else '')
    if end is None or anchor is None:
        raise ValueError('Missing pinned prose anchors')
    start = anchor.start()
    body = text[start:end.start()]
    body = re.sub(r'\[Illustration:.*?\]', '', body, flags=re.S)
    return body, start


def cmu_forms(path):
    """Use orthographic entries only; discard pronunciations and variant suffixes."""
    with path.open() as handle:
        for line in handle:
            if not line.strip() or line.startswith(';;;'):
                continue
            entry = re.sub(r'\(\d+\)$', '', line.split()[0]).lower()
            # Same lossy scoring normalization as plaintext; no target dependence.
            yield from tokenize(entry)[0]


def training(ewt, austen):
    yield from (doc.words for doc in documents(ewt))
    yield tokenize(prose(austen, AUSTEN)[0])[0]


def build(ewt, austen, lexicon, output):
    """No target argument: target forms cannot enter the inventory or counts."""
    output.mkdir(parents=True, exist_ok=False)
    protocol = {'scope': 'Independent-source inventory/model; no target access',
                'sources': {role: {'path': str(path), 'sha256': sha(path)}
                            for role, path in [('ewt', ewt), ('austen', austen), ('lexicon', lexicon)]},
                'inventory_policy': 'external CMU forms union training forms; target never contributes',
                'training_policy': 'EWT original document groups plus one continuous Austen work; no sentence resets',
                'text_policy': 'Pinned prose incipit through Gutenberg end marker; illustrations removed; chapter headings retained'}
    (output/'protocol.json').write_text(json.dumps(protocol, indent=2)+'\n')
    inventory = Inventory.build(output/'inventory.sqlite',
                                chain(cmu_forms(lexicon), (w for doc in training(ewt, austen) for w in doc)))
    try:
        model = SparseBigram.train(inventory, ((inventory.id(w) for w in doc) for doc in training(ewt, austen)))
        model.save(output/'model.sqlite')
        report = {'benchmark_role': 'independent-source-resources', 'protocol': protocol,
                  'inventory_forms': inventory.size, 'inventory_sha256': inventory.identity,
                  'model_sha256': model.identity, 'training_tokens': sum(model.counts[:-1]),
                  'training_documents': model.counts[-1], 'observed_edges': len(model.edges),
                  'dictionary_only_forms': model.unseen,
                  'limitations': ['CMU is a pronunciation lexicon, not exhaustive surface morphology.',
                                  'Training remains small; dictionary-only words have no observed contexts.',
                                  'No million-form resource profile or grammatical/semantic evaluation.']}
        (output/'report.json').write_text(json.dumps(report, indent=2)+'\n')
        return report
    finally:
        inventory.close()


def resource_documents(protocol):
    yield from training(Path(protocol['sources']['ewt']['path']),Path(protocol['sources']['austen']['path']))
    for record in protocol.get('additional_sources', []):
        yield tokenize(prose(Path(record['path']),record['incipit'])[0])[0]


def windows(words, size):
    return (tuple(words[i:i+size]) for i in range(len(words)-size+1))


def prepare(resources, source, output, *, tokens=35000, seed=83, incipit=WELLS):
    if type(tokens) is not int or tokens < 1:
        raise ValueError('tokens must be positive')
    protocol = json.loads((resources/'protocol.json').read_text())
    # Check source paths and hashes before evaluating any overlap.
    source_sha = sha(source)
    for record in protocol['sources'].values():
        if sha(Path(record['path'])) != record['sha256']:
            raise ValueError('Frozen resource input changed')
        if source_sha == record['sha256']:
            raise ValueError('Held-out source is a training/resource source')
    body, body_offset = prose(source, incipit)
    words, spans = tokenize(body)
    if len(words) < tokens:
        raise ValueError('Source shorter than predeclared target prefix')
    words, spans = words[:tokens], spans[:tokens]
    stream, truth = generate((words,), seed=seed)
    # Exact 12-token window overlap with every training document, no cross-doc joins.
    width = 12
    target_windows = set(windows(words, width))
    overlaps = set()
    for doc in resource_documents(protocol):
        overlaps.update(window for window in windows(doc, width) if window in target_windows)
    inventory = Inventory(resources/'inventory.sqlite')
    try:
        model = load_model(resources/'model.sqlite', inventory)
        counts = Counter(words)
        missing = {}
        attested_types, attested_tokens, covered_tokens = 0, 0, 0
        for word, count in counts.items():
            try:
                word_id = inventory.id(word)
            except KeyError:
                missing[word] = count
                continue
            covered_tokens += count
            if model.counts[word_id]:
                attested_types += 1
                attested_tokens += count
        audit = {'scope': 'evaluation-only source independence and vocabulary coverage',
                 'public_sha256': stream.identity, 'model_sha256': model.identity,
                 'inventory_sha256': inventory.identity, 'source_path': str(source), 'raw_sha256': source_sha,
                 'tokens': len(words), 'types': stream.type_count, 'documents': 1,
                 'selection': 'first predeclared number of tokens after prose incipit; no vocabulary filtering',
                 'normalization': 'english-continuous-v1; chapter headings retained; no sentence/paragraph resets',
                 'body_character_offset': body_offset, 'character_spans': spans,
                 'span_coordinates': 'Relative to extracted body after illustration removal and newline normalization; not raw-byte offsets.',
                 'overlap_audit': {'window_tokens': width, 'distinct_target_windows': len(target_windows),
                                   'matching_distinct_windows': len(overlaps),
                                   'matching_examples': [' '.join(w) for w in sorted(overlaps)[:10]],
                                   'limits': 'Exact normalized windows only; not paraphrase or all possible quote detection.'},
                 'coverage': {'missing_types': len(missing), 'missing_tokens': sum(missing.values()),
                              'token_ceiling': covered_tokens/len(words),
                              'type_ceiling': (len(counts)-len(missing))/len(counts),
                              'lm_attested_types': attested_types, 'lm_attested_token_fraction': attested_tokens/len(words)},
                 'missing_words': missing,
                 'resource_protocol': protocol,
                 'limits': ['Wells is deliberately excluded; incidental EWT quotations are audited, not assumed absent.',
                            'One older literary work; not representative of all contemporary English.']}
        output.mkdir(parents=True, exist_ok=False)
        stream.save(output/'public/cipher.json')
        truth.save(output/'evaluation-only/truth.json')
        (output/'evaluation-only/provenance.json').write_text(json.dumps(audit, indent=2)+'\n')
        return audit
    finally:
        inventory.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    builder = sub.add_parser('build')
    builder.add_argument('--ewt', type=Path, required=True)
    builder.add_argument('--austen', type=Path, required=True)
    builder.add_argument('--lexicon', type=Path, required=True)
    builder.add_argument('--output', type=Path, required=True)
    preparer = sub.add_parser('prepare')
    preparer.add_argument('--resources', type=Path, required=True)
    preparer.add_argument('--source', type=Path, required=True)
    preparer.add_argument('--output', type=Path, required=True)
    preparer.add_argument('--tokens', type=int, default=35000)
    preparer.add_argument('--seed', type=int, default=83)
    args = vars(parser.parse_args())
    command = args.pop('command')
    report = build(**args) if command == 'build' else prepare(**args)
    print(json.dumps({k:v for k,v in report.items() if k not in ('character_spans','missing_words','resource_protocol')}, indent=2))
