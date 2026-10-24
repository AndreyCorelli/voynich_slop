"""Disk-indexed stable surface IDs, without a process-wide string dictionary.

SQLite is the first reference storage backend, not a claimed minimal packed
format. Streaming construction sorts/deduplicates on disk; actual file/RSS cost
must be measured before selecting a production backend.
"""
from functools import lru_cache
import hashlib
from pathlib import Path
import sqlite3

from .data import surface


class Inventory:
    def __init__(self, path):
        self.path = Path(path).resolve()
        self.connection = sqlite3.connect(self.path.as_uri() + '?mode=ro', uri=True)
        metadata = dict(self.connection.execute('SELECT key, value FROM metadata'))
        if metadata.get('format_version') != '1':
            self.close()
            raise ValueError('Unsupported inventory format')
        self.identity = metadata['sha256']
        self.size = int(metadata['size'])
        self.tokenization = metadata.get('tokenization', 'english-continuous-v1')
        if self.tokenization not in {'english-continuous-v1', 'ref-historical-continuous-v1'}:
            self.close()
            raise ValueError('Unsupported inventory surface contract')
        self.id = lru_cache(maxsize=65536)(self._id)
        try:
            self.verify()
        except BaseException:
            self.close()
            raise

    def verify(self):
        h, count = hashlib.sha256(), 0
        previous = None
        for word_id, word in self.connection.execute('SELECT id,word FROM forms ORDER BY id'):
            if word_id != count or (previous is not None and word <= previous):
                raise ValueError('Inventory IDs/order mismatch')
            value = surface(word, tokenization=self.tokenization).encode('utf-8')
            h.update(len(value).to_bytes(8, 'little'))
            h.update(value)
            previous, count = word, count + 1
        if count != self.size or h.hexdigest() != self.identity:
            raise ValueError('Inventory identity mismatch')
        return self.identity

    def _id(self, word):
        row = self.connection.execute('SELECT id FROM forms WHERE word=?', (word,)).fetchone()
        if row is None:
            raise KeyError(word)
        return row[0]

    def word(self, word_id):
        if type(word_id) is not int or not 0 <= word_id < self.size:
            raise ValueError('Invalid inventory ID')
        return self.connection.execute('SELECT word FROM forms WHERE id=?', (word_id,)).fetchone()[0]

    def close(self):
        if hasattr(self, 'id'):
            self.id.cache_clear()
        self.connection.close()

    @classmethod
    def build(cls, path, words, *, tokenization='english-continuous-v1'):
        if tokenization not in {'english-continuous-v1', 'ref-historical-continuous-v1'}:
            raise ValueError('Unsupported inventory surface contract')
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        # Exclusive creation preserves an existing resource, including on error.
        with path.open('xb'):
            pass
        connection = sqlite3.connect(path)
        try:
            connection.execute('CREATE TABLE staging (word TEXT PRIMARY KEY) WITHOUT ROWID')
            connection.executemany('INSERT OR IGNORE INTO staging VALUES (?)', ((surface(w, tokenization=tokenization),) for w in words))
            connection.execute('CREATE TABLE forms (id INTEGER PRIMARY KEY, word TEXT UNIQUE NOT NULL)')
            connection.execute('INSERT INTO forms SELECT row_number() OVER (ORDER BY word)-1, word FROM staging ORDER BY word')
            size = connection.execute('SELECT count(*) FROM forms').fetchone()[0]
            if not size:
                raise ValueError('Inventory cannot be empty')
            h = hashlib.sha256()
            for word, in connection.execute('SELECT word FROM forms ORDER BY id'):
                value = word.encode('utf-8')
                h.update(len(value).to_bytes(8, 'little'))
                h.update(value)
            connection.execute('DROP TABLE staging')
            connection.execute('CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)')
            connection.executemany('INSERT INTO metadata VALUES (?, ?)',
                                   [('format_version', '1'), ('size', str(size)), ('sha256', h.hexdigest())])
            if tokenization != 'english-continuous-v1':
                connection.execute('INSERT INTO metadata VALUES (?, ?)', ('tokenization', tokenization))
            connection.commit()
            connection.execute('VACUUM')
        except BaseException:
            connection.close()
            path.unlink()
            raise
        connection.close()
        return cls(path)
