"""Bounded dynamic proposals over the full inventory; no truth-dependent inputs.

Single-context indexes are exact for the fixed sparse bigram model. A bounded
union across sampled contexts is only a heuristic shortlist for dictionary moves.
Neither candidate scores nor their softmax are posterior probabilities.
"""
from array import array
from collections import Counter, OrderedDict
from dataclasses import dataclass
import heapq
import math
import random

from .incremental import EOS
from .sparse_lm import BOS
from .state import _word


def positive_integer(value, name):
    if type(value) is not int or value < 1:
        raise ValueError(f'{name} must be a positive integer')


@dataclass(frozen=True)
class RetrievalConfig:
    active_limit: int = 100
    total_entries: int = 100000
    context_limit: int = 8
    per_context: int = 16
    frequency_limit: int = 32
    random_candidates: int = 8
    pool_limit: int = 400
    cache_queries: int = 256
    archive_per_type: int = 32
    exploration_probability: float = 0.1
    context_strategy: str = "sampled"
    attested_mix: float = 0.0

    def __post_init__(self):
        if not math.isfinite(self.attested_mix) or not 0 <= self.attested_mix < 1:
            raise ValueError("attested_mix must be in [0,1), preserving full inventory support")
        if self.context_strategy not in ("sampled", "pooled"):
            raise ValueError("Unknown context retrieval strategy")
        for name in ('active_limit', 'total_entries', 'context_limit', 'per_context',
                     'frequency_limit', 'random_candidates', 'pool_limit', 'cache_queries', 'archive_per_type'):
            positive_integer(getattr(self, name), name)
        if self.total_entries < self.active_limit or self.pool_limit < self.active_limit:
            raise ValueError('Entry/pool budgets must accommodate one active row')
        if not math.isfinite(self.exploration_probability) or not 0 < self.exploration_probability <= 1:
            raise ValueError('Exploration probability must be positive and at most one')


class ContextIndex:
    def __init__(self, model, *, limit=16, cache_queries=256):
        positive_integer(limit, 'limit')
        positive_integer(cache_queries, 'cache_queries')
        self.model, self.limit, self.cache_queries = model, limit, cache_queries
        successors, predecessors = {}, {}
        for a, b in model.edges:
            if b != model.eos:
                successors.setdefault(a, []).append(b)
            if a != BOS:
                predecessors.setdefault(b, []).append(a)
        self.successors = {a: array('I', sorted(words)) for a, words in successors.items()}
        self.predecessors = {b: array('I', sorted(words)) for b, words in predecessors.items()}
        self.base_top = tuple(heapq.nsmallest(limit, range(model.size), key=lambda w: (-model.base_probability(w), w)))
        def backoff(a):
            return model.config.discount * model.distinct[a] / model.totals[a] if model.totals[a] else 1.
        # For words without an observed edge to a fixed right neighbor, its
        # probability is this coefficient times the same base probability.
        leaders = heapq.nsmallest(limit, range(model.size), key=lambda a: (-backoff(a), a))
        cutoff = backoff(leaders[-1])
        # Near-identical coefficients can round to identical probabilities after
        # multiplying by the neighbor's base probability. Keep lowest-ID leaders
        # per near-cutoff coefficient group so final probability ties are resolved
        # correctly, without retaining every word in a large equal-weight group.
        groups = {}
        for word in range(model.size):
            coefficient = backoff(word)
            if coefficient >= cutoff or math.isclose(coefficient, cutoff, rel_tol=1e-14, abs_tol=0.):
                group = groups.setdefault(coefficient, [])
                if len(group) < limit:
                    group.append(word)
        self.backoff_top = tuple(sorted(w for group in groups.values() for w in group))
        self._cache = OrderedDict()
        self.cache_hits, self.cache_misses = 0, 0

    def query(self, direction, neighbor, *, count=None):
        count = self.limit if count is None else count
        if type(count) is not int or not 1 <= count <= self.limit:
            raise ValueError('Query exceeds configured index limit')
        if direction in ('successors', 'successors_evidence'):
            self.model._context(neighbor)
        elif direction in ('predecessors', 'predecessors_evidence'):
            self.model._outcome(neighbor)
        else:
            raise ValueError('Unknown context direction')
        key = direction, neighbor, count
        if key in self._cache:
            self.cache_hits += 1
            self._cache.move_to_end(key)
            return self._cache[key]
        self.cache_misses += 1
        if direction == 'successors_evidence':
            words = self.successors.get(neighbor, ())
            score = lambda w: self.model.probability(neighbor, w) / self.model.base_probability(w)
        elif direction == 'predecessors_evidence':
            words = self.predecessors.get(neighbor, ())
            score = lambda w: self.model.probability(w, neighbor)
        elif direction == 'successors':
            words = set(self.successors.get(neighbor, ())) | set(self.base_top)
            score = lambda w: self.model.probability(neighbor, w)
        else:
            words = set(self.predecessors.get(neighbor, ())) | set(self.backoff_top)
            score = lambda w: self.model.probability(w, neighbor)
        if direction in ('successors','predecessors') and hasattr(self.model,'retrieval_candidates'):
            words = set(words) | set(self.model.retrieval_candidates(direction,count))
        if hasattr(self.model,'factor_candidates'):
            # Factored mixtures have approximate, explicitly bounded retrieval.
            words = set(words) | set(self.model.factor_candidates(direction,neighbor,count))
        if hasattr(self.model,'context_score'):
            score = lambda w: self.model.context_score(direction,neighbor,w)
        result = tuple(heapq.nsmallest(count, words, key=lambda w: (-score(w), w)))
        self._cache[key] = result
        if len(self._cache) > self.cache_queries:
            self._cache.popitem(last=False)
        return result


@dataclass(frozen=True)
class Candidate:
    word_id: int
    log_delta: float  # Full assign-or-swap delta, all affected occurrences.
    sources: tuple[str, ...]


@dataclass(frozen=True)
class CandidateRow:
    cipher: int
    generation: int
    candidates: tuple[Candidate, ...]
    pool_size: int
    proposed_exploration: tuple[int, ...]


class CandidateRetriever:
    def __init__(self, scorer, *, config=None, seed=0):
        self.scorer = scorer
        self.config = config or RetrievalConfig()
        self.rng = random.Random(seed)
        self.contexts = ContextIndex(scorer.model, limit=self.config.per_context,
                                     cache_queries=self.config.cache_queries)
        self.frequency_order = array('I', sorted(range(scorer.model.size), key=lambda w: (-scorer.model.counts[w], w)))
        order = sorted(range(scorer.stream.type_count), key=lambda c: (-len(scorer.index.occurrences[c]), c))
        self.cipher_ranks = {c: i for i, c in enumerate(order)}
        self.attested = (array("I", (w for w in self.frequency_order if scorer.model.counts[w]))
                         if self.config.attested_mix else ())
        self.rows, self.archives = OrderedDict(), OrderedDict()
        self.entry_count, self.archive_entry_count, self.refresh_count = 0, 0, 0

    def random_word(self):
        """Mix existing training evidence with full-inventory uniform support.

        Zero weight preserves the historical RNG sequence exactly. No target
        statistics or labels enter this distribution.
        """
        if self.config.attested_mix and self.rng.random() < self.config.attested_mix:
            return self.rng.choice(self.attested)
        return self.rng.randrange(self.scorer.model.size)

    def pooled_context_words(self, cipher):
        """Aggregate all occurrences, then fuse bounded observed-edge lists.

        Successor likelihood ratios avoid filling every list with common words;
        predecessor lists require an attested edge. No inventory-wide scoring.
        Exact complete-key deltas still determine the final active shortlist.
        """
        scorer, config = self.scorer, self.config
        left, right = Counter(), Counter()
        for doc_id, position in scorer.index.occurrences[cipher]:
            document = scorer.stream.documents[doc_id]
            left[BOS if position == 0 else scorer.assignment(document[position-1])] += 1
            right[scorer.model.eos if position+1 == len(document) else scorer.assignment(document[position+1])] += 1
        votes = Counter()
        for direction, contexts in (('successors_evidence',left), ('predecessors_evidence',right)):
            selected = sorted(contexts, key=lambda word: (-contexts[word],word))[:config.context_limit]
            for neighbor in selected:
                for rank, word in enumerate(self.contexts.query(direction,neighbor),1):
                    votes[word] += contexts[neighbor] / rank
        return sorted(votes, key=lambda word: (-votes[word],word))[:config.pool_limit//2]

    def refresh(self, cipher, *, audit=None):
        self.scorer.assignment(cipher)  # Validate ID before changing caches.
        config, scorer = self.config, self.scorer
        generation = scorer.generation
        current = scorer.assignment(cipher)
        previous = self.rows.get(cipher)
        pool = {}
        def add(word, source):
            _word(word, scorer.model.size)
            if word in pool:
                pool[word].add(source)
            elif len(pool) < config.pool_limit:
                pool[word] = {source}
        add(current, 'current')
        # Exploration reserves pool slots before retained/context lists can fill it.
        explored = tuple(self.random_word() for _ in range(config.random_candidates))
        for w in explored:
            add(w, 'exploration')
        if config.context_strategy == 'pooled':
            for w in self.pooled_context_words(cipher):
                add(w, 'pooled_context')
        for w in self.archives.get(cipher, ()):
            add(w, 'archive')
        if previous is not None:
            for candidate in previous.candidates:
                add(candidate.word_id, 'retained')
        rank = min(self.cipher_ranks[cipher], scorer.model.size - 1)
        start = max(0, min(rank - config.frequency_limit // 2, scorer.model.size - config.frequency_limit))
        for w in self.frequency_order[start:start + config.frequency_limit]:
            add(w, 'frequency')
        if config.context_strategy == 'sampled':
            positions = scorer.index.occurrences[cipher]
            chosen = (positions[i * len(positions) // min(len(positions), config.context_limit)]
                      for i in range(min(len(positions), config.context_limit)))
            for doc_id, position in chosen:
                document = scorer.stream.documents[doc_id]
                left = BOS if position == 0 else scorer.assignment(document[position - 1])
                right = scorer.model.eos if position + 1 == len(document) else scorer.assignment(document[position + 1])
                for w in self.contexts.query('successors', left):
                    add(w, 'left_context')
                for w in self.contexts.query('predecessors', right):
                    add(w, 'right_context')
        candidates = [Candidate(w, scorer.assign_or_swap(cipher, w).log_delta, tuple(sorted(sources)))
                      for w, sources in pool.items()]
        candidates.sort(key=lambda c: (-c.log_delta, c.word_id))
        if audit is not None:
            audit(tuple(candidates))
        kept = candidates[:config.active_limit]
        if current not in {c.word_id for c in kept}:
            kept[-1] = next(c for c in candidates if c.word_id == current)
            kept.sort(key=lambda c: (-c.log_delta, c.word_id))
        if scorer.generation != generation:
            raise RuntimeError('Dictionary changed during candidate refresh')
        row = CandidateRow(cipher, generation, tuple(kept), len(pool), explored)
        if previous is not None:
            self.entry_count -= len(previous.candidates)
        self.rows[cipher] = row
        self.rows.move_to_end(cipher)
        self.entry_count += len(row.candidates)
        # This archive is explicitly bounded per row and across cipher types.
        self.archive_entry_count -= len(self.archives.get(cipher, ()))
        active_words = {k.word_id for k in kept}
        self.archives[cipher] = tuple(c.word_id for c in candidates if c.word_id not in active_words)[:config.archive_per_type]
        self.archive_entry_count += len(self.archives[cipher])
        self.archives.move_to_end(cipher)
        max_rows = max(1, config.total_entries // config.active_limit)
        while len(self.archives) > max_rows or self.archive_entry_count > config.total_entries:
            _, evicted_archive = self.archives.popitem(last=False)
            self.archive_entry_count -= len(evicted_archive)
        while self.entry_count > config.total_entries:
            _, evicted = self.rows.popitem(last=False)
            self.entry_count -= len(evicted.candidates)
        self.refresh_count += 1
        return row

    def get(self, cipher):
        row = self.rows.get(cipher)
        if row is None or row.generation != self.scorer.generation:
            return self.refresh(cipher)
        self.rows.move_to_end(cipher)
        return row

    def propose(self, cipher):
        """Full-support exploration bypasses shortlist ranking and eviction.

        This is a heuristic proposal policy, not an exact MH/Gibbs kernel.
        Every form retains probability at least epsilon * (1-attested_mix) / V.
        """
        self.scorer.assignment(cipher)
        if self.rng.random() < self.config.exploration_probability:
            return self.scorer.assign_or_swap(cipher, self.random_word()), 'exploration'
        row = self.get(cipher)
        word = self.rng.choice(row.candidates).word_id
        return self.scorer.assign_or_swap(cipher, word), 'active'
