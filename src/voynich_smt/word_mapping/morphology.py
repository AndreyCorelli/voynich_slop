"""Ambiguity-preserving annotations from the existing pinned Whitaker resource."""
from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
import sys

from voynich_smt.data.corpus import digest, write_json

UPSTREAM_COMMIT = '92eb56f188ec9dadecca01ca34d3c9fd13d746da'


@dataclass(frozen=True)
class MorphologyCatalog:
    entries: dict
    resource: dict
    training_sha256: str
    format_version: int = 1
    annotation_failures: dict = field(default_factory=dict)

    @property
    def identity(self):
        return digest(self.artifact())

    def artifact(self):
        result = {'format_version': self.format_version, 'entries': self.entries,
                  'resource': self.resource, 'training_sha256': self.training_sha256}
        if self.annotation_failures:
            result['annotation_failures'] = self.annotation_failures
        return result

    def save(self, path):
        write_json(path, {**self.artifact(), 'sha256': self.identity})

    @classmethod
    def load(cls, path, *, expected_resource=None):
        value = json.loads(Path(path).read_text(encoding='utf-8'))
        if value['format_version'] != 1:
            raise ValueError('Unsupported morphology catalog version')
        catalog = cls(value['entries'], value['resource'], value['training_sha256'],
                      annotation_failures=value.get('annotation_failures', {}))
        if catalog.identity != value['sha256']:
            raise ValueError('Morphology checksum mismatch')
        if expected_resource is not None and catalog.resource != expected_resource:
            raise ValueError('Morphology resource changed')
        return catalog

    def lemma_ids(self, surface):
        return frozenset(a['lemma_id'] for a in self.entries.get(surface, []))

    def form_groups(self):
        groups = {}
        for surface in sorted(self.entries):
            for lemma in sorted(self.lemma_ids(surface)):
                groups.setdefault(lemma, []).append(surface)
        return {lemma: tuple(forms) for lemma, forms in sorted(groups.items())}


class WhitakerAnnotator:
    def __init__(self, vendor_path, *, mode='upstream-default'):
        options = {'upstream-default': {}, 'through-medieval-rare': {'age': 'F', 'frequency': 'F'}}
        if mode not in options:
            raise ValueError('Unknown morphology mode')
        root = Path(vendor_path).resolve()
        paths = sorted(p for p in (root / 'whitakers_words').rglob('*')
                       if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.db')
        if not paths or not (root / 'LICENSE').exists():
            raise ValueError('Pinned morphology resource not available')
        paths.append(root / 'LICENSE')
        self.resource = {'upstream_commit': UPSTREAM_COMMIT, 'mode': mode,
            'options': options[mode], 'files_sha256': {
                str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
            'annotation_version': 2,
            'failure_policy': 'known upstream missing PACK table: retain surface, no analyses, record error; other failures raise',
            'lemma_labels': 'resource lexeme IDs; roots are stems, not reconstructed headwords',
            'orthography': 'lookup merges j/i and v/u; surface key remains unchanged'}
        sys.path.insert(0, str(root))
        self.annotation_failures = {}
        try:
            from whitakers_words import parser
            if not Path(parser.__file__).resolve().is_relative_to(root):
                raise ValueError('A different Whitaker implementation is already imported')
            self.engine = parser.Parser(**options[mode])
        finally:
            sys.path.pop(0)

    def annotate(self, surface):
        try:
            parsed = self.engine.parse(surface)
        except KeyError as error:
            if error.args != ('PACK',):
                raise
            self.annotation_failures[surface] = 'upstream missing PACK empty-inflection table'
            return []
        entries = []
        for form in parsed.forms:
            for analysis in form.analyses.values():
                # Upstream unique forms all use lexeme ID 0. Do not merge them.
                lexeme_id = analysis.lexeme.id
                lemma_id = (f'whitaker:{lexeme_id}' if lexeme_id else
                            f'whitaker:unique:{parsed.text}')
                inflections = [{'stem': i.stem, 'ending': i.affix,
                    'part_of_speech': i.wordType.name,
                    'features': {k: v.name for k, v in sorted(i.features.items())}}
                    for i in analysis.inflections]
                entries.append({'lemma_id': lemma_id, 'lexeme_id': lexeme_id,
                    'roots': list(analysis.lexeme.roots), 'lemma_label': None,
                    'part_of_speech': analysis.lexeme.wordType.name,
                    'properties': list(analysis.lexeme.props),
                    'enclitic': analysis.enclitic.text if analysis.enclitic else None,
                    'inflections': sorted(inflections, key=lambda r: json.dumps(r, sort_keys=True))})
        return sorted(entries, key=lambda r: json.dumps(r, sort_keys=True))

    def catalog(self, forms, *, training_sha256):
        forms = sorted(set(forms))
        entries = {w: self.annotate(w) for w in forms}
        return MorphologyCatalog(entries, self.resource, training_sha256,
            annotation_failures={w: self.annotation_failures[w] for w in forms if w in self.annotation_failures})
