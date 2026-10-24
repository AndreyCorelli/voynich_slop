"""Manifest-driven Latin corpus preparation; independent of decoder and truth."""
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
import unicodedata


VERSION = 'latin-library-lines-v2'


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def normalize(text):
    text = ''.join(c for c in unicodedata.normalize('NFD', text.lower())
                   if unicodedata.category(c) != 'Mn')
    return tuple(re.findall('[a-z]+', text.replace('j', 'i').replace('v', 'u')))


def clean(text):
    """Retain prose lines, not navigation/headings; log losses, never use truth.

    This conservative reference excludes short verse lines. Line-length selection
    is a source-format rule, not a claimed general Latin language detector.
    Angle-bracketed editorial supplements retain their words (not HTML removal).
    """
    tokens, reasons = [], Counter()
    for line in text.splitlines():
        row = normalize(line)
        if not row:
            continue
        letters = ''.join(c for c in line if c.isalpha())
        if any(s in line.lower() for s in ('the latin library', 'the classics page',
                  'all rights reserved', 'copyright', 'http://', 'https://',
                  'click here', 'this text', 'this edition', 'this book', 'latin text')):
            reason = 'editorial_or_navigation'
        elif len(row) < 12:
            reason = 'short_line'
        elif letters.isupper() or (len(letters)>0 and sum(c.isupper() for c in letters)/len(letters)>.65):
            reason = 'heading'
        elif sum(bool(re.fullmatch(r'[IVXLCDM]+[ab]?',w)) for w in line.split()) / max(1,len(line.split())) > .6:
            reason = 'roman_navigation'
        else:
            # Standalone Roman section labels, never arbitrary short Latin words.
            line = re.sub(r'^\s*(?:\[\s*)?[IVXLCDM]+[.\]\s]+', '', line)
            line = re.sub(r'^\s*CAPUT\s+\d+\s*', '', line)
            tokens.extend(normalize(line))
            continue
        reasons[reason] += len(row)
    return tuple(tokens), dict(reasons)


def fingerprint(tokens):
    return hashlib.sha256((' '.join(tokens)).encode()).hexdigest()


def shingles(tokens, n=12):
    for i in range(max(0, len(tokens) - n + 1)):
        yield hashlib.blake2b(' '.join(tokens[i:i+n]).encode(), digest_size=8).digest()


def balanced_order(records):
    """Whole-document round robin, choosing least represented author by tokens."""
    import heapq
    by_author = defaultdict(list)
    for record in sorted(records, key=lambda r: hashlib.sha256(r['id'].encode()).hexdigest()):
        by_author[record['author']].append(record)
    heap = [(0, author, 0) for author in sorted(by_author)]
    heapq.heapify(heap)
    while heap:
        total, author, index = heapq.heappop(heap)
        record = by_author[author][index]
        yield record
        if index + 1 < len(by_author[author]):
            heapq.heappush(heap, (total + record['tokens'], author, index + 1))


def documents(root, records):
    for r in records:
        path = Path(root) / r['normalized_path']
        if sha(path) != r['normalized_sha256']:
            raise ValueError('Normalized corpus changed: ' + r['id'])
        yield tuple(path.read_text().split())


def census(source, output, design):
    """Build only training streams. Held-out streams remain evaluation-side."""
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    write(output / 'design.json', design)
    excluded = set(design['excluded_authors'])
    registry = design['training_directories']
    heldout = design['heldouts']
    heldout_shingles = set()
    private = output / 'evaluation-only'
    for r in heldout:
        tokens, losses = clean((source / r['path']).read_text(encoding='utf-8-sig'))
        tokens = tokens[:design['maximum_target_tokens']]
        if len(tokens) < 1000:
            raise ValueError('Held-out prose unexpectedly short: ' + r['path'])
        target = private / (r['id'] + '.txt')
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(' '.join(tokens) + '\n')
        heldout_shingles.update(shingles(tokens))
        write(private / (r['id'] + '.json'), {**r, 'tokens': len(tokens),
              'source_sha256': sha(source / r['path']), 'losses': losses,
              'normalized_sha256': sha(target)})
    records, rejected, duplicates, seen = [], [], [], {}
    for path in sorted(source.rglob('*.txt')):
        relative = path.relative_to(source)
        if len(relative.parts) != 2 or relative.parts[0] not in registry:
            rejected.append({'path': str(relative), 'reason': 'unregistered_source'})
            continue
        author = registry[relative.parts[0]]
        if author in excluded:
            raise ValueError('Excluded author admitted in registry')
        if any(s in path.stem.lower() for s in design['excluded_filename_fragments']):
            rejected.append({'path': str(relative), 'reason': 'index_or_fragment'})
            continue
        tokens, losses = clean(path.read_text(encoding='utf-8-sig'))
        if len(tokens) < design['minimum_document_tokens']:
            rejected.append({'path': str(relative), 'reason': 'insufficient_prose', 'tokens': len(tokens)})
            continue
        identity = fingerprint(tokens)
        if identity in seen:
            duplicates.append({'path': str(relative), 'duplicate_of': seen[identity], 'kind': 'exact'})
            continue
        # Whole-document exclusion, not target-tailored removal of phrases.
        matches = sum(s in heldout_shingles for s in shingles(tokens))
        if matches >= 12:
            rejected.append({'path': str(relative), 'reason': 'heldout_passage_overlap', 'matching_12grams': matches})
            continue
        seen[identity] = str(relative)
        rid = str(relative).replace('/', '__')
        norm = Path('training') / rid
        (output / norm).parent.mkdir(parents=True, exist_ok=True)
        (output / norm).write_text(' '.join(tokens) + '\n')
        records.append({'id': rid, 'author': author, 'source_path': str(relative),
               'source_sha256': sha(path), 'normalized_path': str(norm),
               'normalized_sha256': sha(output / norm), 'tokens': len(tokens),
               'cleaning_losses': losses, 'matching_heldout_12grams': matches})
    # Sampled 12-gram Jaccard identifies near-duplicate documents; deterministic
    # bottom-hash samples, with exact overlap verification before exclusion.
    samples, kept = [], []
    for r in sorted(records, key=lambda r: (-r['tokens'], r['id'])):
        toks = (output / r['normalized_path']).read_text().split()
        sample = set(sorted(set(shingles(toks)))[:256])
        duplicate = None
        for prev, other in samples:
            if sample and len(sample & other) / max(1, len(sample | other)) >= .65:
                a = set(shingles(toks))
                b = set(shingles((output / prev['normalized_path']).read_text().split()))
                if len(a & b) / min(len(a), len(b)) >= .8:
                    duplicate = prev['id']
                    break
        if duplicate:
            duplicates.append({'path': r['source_path'], 'duplicate_of': duplicate, 'kind': 'verified_near_duplicate'})
            (output / r['normalized_path']).unlink()
        else:
            kept.append(r)
            samples.append((r, sample))
    order = list(balanced_order(kept))
    subsets = {}
    for budget in design['training_sizes']:
        subset, total = [], 0
        for r in order:
            subset.append(r['id']); total += r['tokens']
            if total >= budget:
                break
        subsets[str(budget)] = {'documents': subset, 'tokens': total, 'requested_tokens': budget}
    report = {'format_version': 1, 'cleaner': VERSION, 'source': design['source'],
              'documents': order, 'subsets': subsets, 'rejected': rejected,
              'duplicates': duplicates, 'training_tokens': sum(r['tokens'] for r in order),
              'authors': dict(Counter({a: sum(r['tokens'] for r in order if r['author'] == a)
                                     for a in sorted({r['author'] for r in order})})),
              'limitations': ['Line cleaner favors prose and can retain unmarked editorial text.',
                  'Author registry is conservative; unregistered files are quarantined.',
                  '12-gram and near-duplicate screens do not prove independence.',
                  'Book files are treated as documents; no transitions across files.']}
    write(output / 'corpus.json', report)
    return report
