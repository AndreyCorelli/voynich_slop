"""Finite independent Whitaker inventory, using the upstream compatibility matcher."""
from collections import defaultdict, Counter
import hashlib
import json
from pathlib import Path
import random
import sys

from voynich_smt.data.corpus import write_json
from voynich_smt.word_mapping.corpora import WordStream

VENDOR = Path('data/vendor/whitakers-words')
OUT = Path('experiments/results/latin-large-dictionary')


def enumerate_forms():
    sys.path.insert(0, str(VENDOR.resolve()))
    from whitakers_words.datalayer import DataLayer
    from whitakers_words.matcher import Matcher
    from whitakers_words.parser import Inflection, UniqueInflection
    from whitakers_words.util import canonicalize_orth
    data = DataLayer(age='F', frequency='F')
    inflections = {i['iid']: i for group in data.inflects.values() for items in group.values() for i in items}
    inflections.update({i['iid']: i for items in data.empty.values() for i in items})
    by_stem = defaultdict(list)
    for i in inflections.values():
        if data._filter_inflections(i):
            by_stem[i['pos'], i['stem']].append(i)
    forms, ranks = defaultdict(set), {}
    witnesses = {}
    for index, (_, stems) in enumerate(sorted(data.stems.items())):
        for stem in stems:
            if stem['props'][3] > 'F':
                continue
            options = by_stem[stem['pos'], stem['stem_number']]
            if stem['pos'] == 'V':
                options = options + by_stem['VPAR', stem['stem_number']]
            for i in options:
                if not Matcher(stem, i).check():
                    continue
                word = canonicalize_orth(stem['orth'] + i['ending'])
                # Respect parser's ending-length and alphabetic-input limits.
                if not word.isalpha() or (i['ending'] and not 0 < len(i['ending']) < min(8, len(word))):
                    continue
                infl = Inflection(i, stem)
                signature = (infl.wordType.name, None, tuple(sorted((k, v.name) for k, v in infl.features.items())))
                forms[word].add(signature)
                ranks[word] = min(ranks.get(word, 'Z'), stem['props'][3])
                witnesses.setdefault(word, {'lexeme_id': stem['wid'], 'inflection_id': i['iid']})
        if index % 20000 == 0:
            print('stems', index, 'forms', len(forms), flush=True)
    for word, uniques in sorted(data.uniques.items()):
        word = canonicalize_orth(word)
        if not word.isalpha():
            continue
        for unique in uniques:
            infl = UniqueInflection(unique)
            forms[word].add((infl.wordType.name, None, tuple(sorted((k, v.name) for k, v in infl.features.items()))))
        ranks[word] = 'A'
        witnesses.setdefault(word, {'unique': True})
    return forms, ranks, witnesses


def run():
    forms, ranks, witnesses = enumerate_forms()
    # Rank independently of Caesar; stable hash breaks frequency ties without alphabetical bias.
    order = sorted(forms, key=lambda w: (ranks[w], hashlib.sha256(w.encode()).hexdigest()))
    from benchmarks.word_mapping_widening import PARENT, source_streams
    train, development, _, _, _ = source_streams(PARENT)
    counts = Counter(w for segment in train.segments() for w in segment)
    from voynich_smt.word_mapping.morphology import WhitakerAnnotator
    annotator = WhitakerAnnotator(VENDOR, mode='through-medieval-rare')
    for word in sorted(counts):
        parsed = annotator.annotate(word)
        if parsed:
            for a in parsed:
                for i in a['inflections']:
                    forms[word].add((i['part_of_speech'], a['enclitic'], tuple(sorted(i['features'].items()))))
            ranks.setdefault(word, 'Z')
            witnesses.setdefault(word, {'training_attested_and_parser_recognized': True})
    selected = sorted(forms, key=lambda w: (-counts[w], ranks[w], hashlib.sha256(w.encode()).hexdigest()))[:100000]
    if len(selected) != 100000:
        raise ValueError('Resource did not yield 100,000 forms')
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT/'forms-100000.jsonl').open('w') as handle:
        for word in selected:
            handle.write(json.dumps({'surface': word, 'frequency_class': ranks[word],
                'signatures': sorted(forms[word], key=repr), 'witness': witnesses[word]}, sort_keys=True)+'\n')
    # Full inventory membership export enables reproducible coverage audits.
    (OUT/'all-surfaces.txt').write_text('\n'.join(sorted(forms))+'\n')
    from benchmarks.word_mapping_widening import PARENT, source_streams
    train, development, test, _, _ = source_streams(PARENT)
    # Keep the original final-test artifact unopened by this audit beyond its identity checks.
    audits = []
    for name, stream in [('training', train), ('development', development)]:
        counts = Counter(w for s in stream.segments() for w in s)
        for label, inventory in [('100000', set(selected)), ('all-generated', set(forms))]:
            missing = counts.keys()-inventory
            audits.append({'split': name, 'inventory': label, 'tokens': sum(counts.values()),
                'types': len(counts), 'token_coverage': 1-sum(counts[w] for w in missing)/sum(counts.values()),
                'type_coverage': 1-len(missing)/len(counts),
                'top_missing': sorted(((w, counts[w]) for w in missing), key=lambda x: (-x[1], x[0]))[:25]})
    # Deterministic random round-trip sample of the selected inventory.
    from voynich_smt.word_mapping.morphology import WhitakerAnnotator
    annotator = WhitakerAnnotator(VENDOR, mode='through-medieval-rare')
    rng = random.Random(1841)
    sample = rng.sample(selected, 1000)
    failures, disagreements = [], []
    for word in sample:
        parsed = annotator.annotate(word)
        observed = {(i['part_of_speech'], a['enclitic'], tuple(sorted(i['features'].items()))) for a in parsed for i in a['inflections']}
        if not observed:
            failures.append(word)
        if not forms[word] <= observed:
            disagreements.append(word)
    report = {'generated_forms': len(forms), 'selected_forms': len(selected),
        'selection': 'frozen training word frequency, then resource frequency class and SHA256(surface); training-attested parser-recognized forms included; no development-derived additions',
        'scope': 'rule-generated plus parser-recognized training forms; not proof of general attestation; no productive affix or general enclitic expansion',
        'audits': audits, 'roundtrip_sample': len(sample), 'roundtrip_unrecognized': failures,
        'roundtrip_missing_generated_analyses': disagreements,
        'resource': annotator.resource, 'training_sha256': train.identity,
        'development_sha256': development.identity,
        'code_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'files_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (OUT/'forms-100000.jsonl', OUT/'all-surfaces.txt')}}
    write_json(OUT/'report.json', report)
    print(json.dumps({k: v for k,v in report.items() if k not in ('resource',)}, indent=2))


if __name__ == '__main__':
    run()
