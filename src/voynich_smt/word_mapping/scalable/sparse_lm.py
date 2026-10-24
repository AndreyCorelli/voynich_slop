"""Normalized absolute-discount bigram reference with full inventory support.

Only observed edges are materialized. Unseen contexts use the full-support base;
probabilities are never renormalized over a shortlist. Reference edge dictionaries
remain Python objects: O(E) storage is not a production memory guarantee.
"""
from array import array
from collections import Counter
from dataclasses import asdict
import hashlib
import json
import math
from pathlib import Path
import sqlite3
import sys

from voynich_smt.data.corpus import digest
from .config import ModelConfig

BOS = -1


class SparseBigram:
    def __init__(self, inventory_sha256, counts, edges, config, training_sha256):
        self.inventory_sha256 = inventory_sha256
        self.counts = array('Q', counts)  # Words, followed by EOS.
        self.size = len(self.counts) - 1
        self.eos = self.size
        self.edges = dict(edges)
        self.config = config
        self.training_sha256 = training_sha256
        if self.size < 1 or not self.counts[-1]:
            raise ValueError('Expected vocabulary and observed document endpoints')
        self.total = sum(self.counts)
        self.unseen = sum(c == 0 for c in self.counts[:-1])
        self.reserve = config.unseen_mass if self.unseen else 0.
        self.totals, self.distinct = Counter(), Counter()
        for (a, b), count in self.edges.items():
            self._context(a)
            self._outcome(b)
            if type(count) is not int or count < 1 or (a == BOS and b == self.eos):
                raise ValueError('Invalid observed edge')
            self.totals[a] += count
            self.distinct[a] += 1
        # Every observed word and EOS must have exactly its incoming count.
        incoming = Counter()
        for (_, b), count in self.edges.items():
            incoming[b] += count
        if any(incoming[i] != count for i, count in enumerate(self.counts)):
            raise ValueError('Edge and outcome counts differ')
        if self.totals[BOS] != self.counts[-1] or any(
                self.totals[i] != self.counts[i] for i in range(self.size)):
            raise ValueError('Invalid document flow counts')

    def _context(self, word_id):
        if type(word_id) is not int or not BOS <= word_id < self.size:
            raise ValueError('Invalid source context')

    def _outcome(self, word_id):
        if type(word_id) is not int or not 0 <= word_id <= self.size:
            raise ValueError('Invalid prediction outcome')

    def base_probability(self, word_id):
        self._outcome(word_id)
        count = self.counts[word_id]
        if count:
            return (1 - self.reserve) * count / self.total
        return self.reserve / self.unseen

    def probability(self, previous, word_id):
        self._context(previous)
        self._outcome(word_id)
        total = self.totals[previous]
        base = self.base_probability(word_id)
        if not total:
            return base
        count = self.edges.get((previous, word_id), 0)
        discount = self.config.discount
        return max(count - discount, 0.) / total + discount * self.distinct[previous] / total * base

    def score_chunks(self, chunks):
        """One continuous document; arbitrary chunks never reset context.

        Conditions BOS on a nonempty document; score the first word with the BOS
        word distribution normalized excluding EOS. Subsequent transitions include
        EOS, with exactly one endpoint event at the actual document end.
        """
        def log_terms():
            previous, tokens = BOS, 0
            for chunk in chunks:
                for word_id in chunk:
                    if type(word_id) is not int or not 0 <= word_id < self.size:
                        raise ValueError('Document must contain inventory word IDs only')
                    probability = self.probability(previous, word_id)
                    if previous == BOS:
                        probability /= 1 - self.probability(BOS, self.eos)
                    yield math.log(probability)
                    previous, tokens = word_id, tokens + 1
            if not tokens:
                raise ValueError('Cannot score an empty document')
            yield math.log(self.probability(previous, self.eos))
        # Long continuous documents accumulate enough rounding error with +=
        # to cause false incremental-score validation failures.
        return math.fsum(log_terms())

    def score(self, document):
        return self.score_chunks((document,))

    def dense_hmm(self, *, max_types=128):
        """Tiny-state adapter only; refuse accidental dense production allocation."""
        if self.size > max_types:
            raise ValueError('Dense adapter exceeds explicit small-state limit')
        from voynich_smt.word_mapping.ravi_knight.reference import BigramHMM
        nonempty = 1 - self.probability(BOS, self.eos)
        initial = tuple(self.probability(BOS, w) / nonempty for w in range(self.size))
        transition = tuple(tuple(self.probability(a, b) for b in range(self.size)) for a in range(self.size))
        final = tuple(self.probability(a, self.eos) for a in range(self.size))
        return BigramHMM(initial, transition, final,
                         tuple(tuple(float(a == b) for b in range(self.size)) for a in range(self.size)))

    @property
    def identity(self):
        return digest({'inventory': self.inventory_sha256, 'training': self.training_sha256,
                       'config': asdict(self.config), 'counts': list(self.counts),
                       'edges': [(a, b, c) for (a, b), c in sorted(self.edges.items())]})

    def save(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb'):
            pass
        connection = sqlite3.connect(path)
        try:
            counts = array('Q', self.counts)
            if sys.byteorder != 'little':
                counts.byteswap()
            metadata = {'format_version': 1, 'inventory_sha256': self.inventory_sha256,
                        'training_sha256': self.training_sha256, 'config': asdict(self.config),
                        'sha256': self.identity, 'count_encoding': 'uint64-le'}
            connection.execute('CREATE TABLE model (metadata TEXT NOT NULL, counts BLOB NOT NULL)')
            connection.execute('INSERT INTO model VALUES (?, ?)', (json.dumps(metadata), counts.tobytes()))
            connection.execute('CREATE TABLE edges (a INTEGER, b INTEGER, n INTEGER, PRIMARY KEY(a,b)) WITHOUT ROWID')
            connection.executemany('INSERT INTO edges VALUES (?, ?, ?)',
                                   ((a, b, n) for (a, b), n in self.edges.items()))
            connection.commit()
        except BaseException:
            connection.close()
            path.unlink()
            raise
        connection.close()

    @classmethod
    def load(cls, path, inventory):
        connection = sqlite3.connect(Path(path).resolve().as_uri() + '?mode=ro', uri=True)
        try:
            metadata, blob = connection.execute('SELECT metadata, counts FROM model').fetchone()
            metadata = json.loads(metadata)
            if metadata['format_version'] != 1 or metadata['count_encoding'] != 'uint64-le':
                raise ValueError('Unsupported model format')
            if metadata['inventory_sha256'] != inventory.identity:
                raise ValueError('Inventory identity mismatch')
            counts = array('Q')
            counts.frombytes(blob)
            if sys.byteorder != 'little':
                counts.byteswap()
            model = cls(inventory.identity, counts,
                        {(a, b): n for a, b, n in connection.execute('SELECT a,b,n FROM edges')},
                        ModelConfig(**metadata['config']), metadata['training_sha256'])
            if model.size != inventory.size or model.identity != metadata['sha256']:
                raise ValueError('Model identity mismatch')
            return model
        finally:
            connection.close()

    @classmethod
    def train(cls, inventory, documents, *, config=None):
        config = config or ModelConfig()
        counts, edges = array('Q', [0]) * (inventory.size + 1), Counter()
        h = hashlib.sha256()
        for document in documents:
            previous, length = BOS, 0
            document_hash = hashlib.sha256()
            for word_id in document:
                if type(word_id) is not int or not 0 <= word_id < inventory.size:
                    raise ValueError('Training words must belong to the frozen inventory')
                edges[previous, word_id] += 1
                counts[word_id] += 1
                document_hash.update(word_id.to_bytes(8, 'little'))
                previous, length = word_id, length + 1
            if not length:
                raise ValueError('Empty training document')
            edges[previous, inventory.size] += 1
            counts[-1] += 1
            h.update(length.to_bytes(8, 'little'))
            h.update(document_hash.digest())
        return cls(inventory.identity, counts, edges, config, h.hexdigest())
