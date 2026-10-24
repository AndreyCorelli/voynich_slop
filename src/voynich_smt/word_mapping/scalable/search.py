"""Budgeted heuristic dictionary optimization, not posterior inference.

Annealing accepts whole-key replacements/swaps. Checkpoints preserve RNGs,
retrieval rows/archives/cache order and numeric event scores at transaction
boundaries, so proposal-limited continuation can be replayed exactly.
"""
from bisect import bisect_right
from collections import OrderedDict
from dataclasses import asdict, dataclass
from itertools import accumulate
import json
import math
import os
from pathlib import Path
import random
import resource
import sys
import tempfile
import time

from voynich_smt.data.corpus import digest
from .incremental import DictionaryScorer
from .retrieval import Candidate, CandidateRetriever, CandidateRow, RetrievalConfig, positive_integer
from .state import DictionaryState


@dataclass(frozen=True)
class SearchConfig:
    proposals: int = 20000
    initial_temperature: float = 1.0
    final_temperature: float = 0.05
    greedy_probability: float = 0.5
    frequency_mix: float = 0.5
    refresh_interval: int = 100
    validation_interval: int = 500
    checkpoint_interval: int = 1000
    joint_archive_size: int = 4
    budget_seconds: float = 3600.
    reserve_seconds: float = 10.
    memory_limit_bytes: int = 8 * 1024**3
    scheduler: str = "mixed"
    initialization: str = "random"
    joint_probability: float = 0.0

    def __post_init__(self):
        if self.initialization not in ("random", "frequency", "profile", "classes"):
            raise ValueError("Unknown dictionary initialization")
        if self.scheduler not in ("mixed", "coverage_first"):
            raise ValueError("Unknown type scheduler")
        for name in ('proposals', 'refresh_interval', 'validation_interval', 'checkpoint_interval',
                     'joint_archive_size', 'memory_limit_bytes'):
            positive_integer(getattr(self, name), name)
        for name in ('initial_temperature', 'final_temperature', 'budget_seconds'):
            if not math.isfinite(getattr(self, name)) or getattr(self, name) <= 0:
                raise ValueError(f'{name} must be finite and positive')
        for name in ('greedy_probability', 'frequency_mix', 'joint_probability'):
            if not math.isfinite(getattr(self, name)) or not 0 <= getattr(self, name) < 1:
                raise ValueError(f'{name} must be in [0,1), preserving broad reachability')
        if not math.isfinite(self.reserve_seconds) or not 0 <= self.reserve_seconds < self.budget_seconds:
            raise ValueError('Invalid export/evaluation reserve')


def tuples(value):
    return tuple(map(tuples, value)) if isinstance(value, list) else value


def peak_rss():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (1 if sys.platform == 'darwin' else 1024)


class DictionarySearch:
    def __init__(self, model, stream, *, seed=0, config=None, retrieval_config=None, state=None, clock=time.monotonic):
        started = clock()
        self.config = config or SearchConfig()
        self.seed, self.clock = seed, clock
        state = state or DictionaryState.initialize(stream, model, method=self.config.initialization, seed=seed)
        self.scorer = DictionaryScorer(model, stream, state)
        self.retriever = CandidateRetriever(self.scorer, config=retrieval_config, seed=seed + 1000003)
        self.rng = random.Random(seed + 2000003)
        # Independent RNG preserves the historical mixed scheduler trajectory.
        order = list(range(stream.type_count)) if self.config.scheduler == "coverage_first" else []
        random.Random(seed + 3000017).shuffle(order)
        self.coverage_order = tuple(order)
        self.model_sha256 = model.identity
        self.cumulative = tuple(accumulate(len(p) for p in self.scorer.index.occurrences))
        self.step, self.accepted, self.noops, self.validations = 0, 0, 0, 0
        self.source_counts = {}
        self.initial_score = self.scorer.score
        self.joint_archive = [(self.scorer.score, tuple(state.assignments))]
        self.elapsed_seconds = clock() - started
        self.stop_reason = 'not_started'
        self._run_started = None

    def temperature(self):
        fraction = min(self.step / max(1, self.config.proposals - 1), 1.)
        return self.config.initial_temperature * (self.config.final_temperature / self.config.initial_temperature)**fraction

    def _archive(self):
        if len(self.joint_archive) >= self.config.joint_archive_size and self.scorer.score <= self.joint_archive[-1][0]:
            return
        key = self.scorer.state.assignments
        if any(key == old for _, old in self.joint_archive):
            return
        self.joint_archive.append((self.scorer.score, key))
        self.joint_archive.sort(key=lambda pair: (-pair[0], pair[1]))
        del self.joint_archive[self.config.joint_archive_size:]

    def joint_proposal(self, cipher):
        """Search a bounded chain of occupied shortlist entries for a 3-cycle."""
        scorer = self.scorer
        candidates = self.retriever.get(cipher).candidates[:4]
        moves = []
        for candidate in candidates:
            second = scorer.owner(candidate.word_id)
            if second is None or second == cipher:
                continue
            for next_candidate in self.retriever.get(second).candidates[:4]:
                third = scorer.owner(next_candidate.word_id)
                if third is None or third in (cipher,second):
                    continue
                changes = {cipher: scorer.assignment(second), second: scorer.assignment(third),
                           third: scorer.assignment(cipher)}
                moves.append(scorer.propose(changes))
        if moves:
            return max(moves, key=lambda move: (move.log_delta, move.changes))
        # Full support of ordinary moves remains; a failed cycle attempt is explicit.
        return scorer.propose({})

    def advance(self):
        """One complete proposal/decision transaction; no wall-clock branching."""
        if self.step >= self.config.proposals:
            raise ValueError('Proposal schedule is complete')
        if self.step < len(self.coverage_order):
            cipher = self.coverage_order[self.step]
        elif self.rng.random() < self.config.frequency_mix:
            cipher = bisect_right(self.cumulative, self.rng.randrange(self.cumulative[-1]))
        else:
            cipher = self.rng.randrange(self.scorer.stream.type_count)
        if self.step % self.config.refresh_interval == 0:
            self.retriever.refresh(cipher)
        if self.config.joint_probability and self.rng.random() < self.config.joint_probability:
            move, source = self.joint_proposal(cipher), 'joint_cycle'
        elif self.rng.random() < self.config.greedy_probability:
            word = self.retriever.get(cipher).candidates[0].word_id
            move, source = self.scorer.assign_or_swap(cipher, word), 'greedy'
        else:
            move, source = self.retriever.propose(cipher)
        word = dict(move.changes).get(cipher, self.scorer.assignment(cipher))
        self._last_proposal = (cipher, word, move)
        self.source_counts[source] = self.source_counts.get(source, 0) + 1
        accepted = False
        temperature = self.temperature()
        if not move.changes:
            self.noops += 1
        elif move.log_delta >= 0 or math.log(max(self.rng.random(), 1e-300)) < move.log_delta / temperature:
            self.scorer.commit(move)
            self.accepted += 1
            self._archive()
            accepted = True
        self.step += 1
        if self.step % self.config.validation_interval == 0:
            self.scorer.validate()
            self.validations += 1
        return {'step': self.step, 'cipher': cipher, 'source': source, 'delta': move.log_delta,
                'temperature': temperature, 'accepted': accepted, 'score': self.scorer.score}

    def _elapsed(self):
        return self.elapsed_seconds + (self.clock() - self._run_started if self._run_started is not None else 0.)

    def run(self, *, steps=None, checkpoint=None, progress=None):
        if steps is not None and (type(steps) is not int or steps < 0):
            raise ValueError('steps must be a nonnegative integer')
        end = self.config.proposals if steps is None else min(self.step + steps, self.config.proposals)
        self._run_started = self.clock()
        next_update = self.clock() + 30.
        try:
            while self.step < end:
                if self._elapsed() >= self.config.budget_seconds - self.config.reserve_seconds:
                    self.stop_reason = 'time_budget'
                    break
                if peak_rss() > self.config.memory_limit_bytes:
                    self.stop_reason = 'memory_budget'
                    break
                event = self.advance()
                if progress is not None and self.clock() >= next_update:
                    progress({**event, 'elapsed_seconds': self._elapsed()})
                    next_update = self.clock() + 30.
                if checkpoint is not None and self.step % self.config.checkpoint_interval == 0:
                    self.save(checkpoint)
            else:
                self.stop_reason = 'proposal_limit' if self.step == self.config.proposals else 'partial'
            self.scorer.validate()
            self.validations += 1
        finally:
            self.elapsed_seconds = self._elapsed()
            self._run_started = None
        if checkpoint is not None:
            self.save(checkpoint)
        return self.summary()

    def summary(self):
        return {'step': self.step, 'stop_reason': self.stop_reason, 'accepted': self.accepted,
                'noops': self.noops, 'validations': self.validations, 'source_counts': dict(self.source_counts),
                'initial_score': self.initial_score, 'current_score': self.scorer.score,
                'best_score': self.joint_archive[0][0], 'elapsed_seconds': self._elapsed(),
                'peak_rss_bytes': peak_rss(), 'refresh_count': self.retriever.refresh_count,
                'active_entries': self.retriever.entry_count, 'archive_entries': self.retriever.archive_entry_count,
                'joint_archive': [{'score': score, 'assignments': key} for score, key in self.joint_archive]}

    def snapshot(self):
        r = self.retriever
        return {'format_version': 1, 'model_sha256': self.model_sha256,
                'cipher_sha256': self.scorer.stream.identity, 'seed': self.seed,
                'config': asdict(self.config), 'retrieval_config': asdict(r.config),
                'assignments': self.scorer.state.assignments, 'generation': self.scorer.generation,
                'event_scores': list(self.scorer._scores), 'score': self.scorer.score,
                'search_rng': self.rng.getstate(), 'retrieval_rng': r.rng.getstate(),
                'rows': [asdict(row) for row in r.rows.values()],
                'archives': list(r.archives.items()),
                'context_cache': list(r.contexts._cache.items()),
                'cache_hits': r.contexts.cache_hits, 'cache_misses': r.contexts.cache_misses,
                'refresh_count': r.refresh_count, 'step': self.step, 'accepted': self.accepted,
                'noops': self.noops, 'validations': self.validations,
                'source_counts': dict(self.source_counts), 'initial_score': self.initial_score,
                'joint_archive': list(self.joint_archive), 'elapsed_seconds': self._elapsed(),
                'stop_reason': self.stop_reason}

    def save(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = self.snapshot()
        envelope = {'sha256': digest(payload), 'payload': payload}
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', dir=path.parent, prefix=path.name + '.', delete=False) as handle:
                temporary = handle.name
                json.dump(envelope, handle)
                handle.write('\n')
            os.replace(temporary, path)
        finally:
            if temporary is not None and os.path.exists(temporary):
                os.unlink(temporary)

    @classmethod
    def load(cls, path, model, stream, *, clock=time.monotonic):
        started = clock()
        envelope = json.loads(Path(path).read_text())
        p = envelope['payload']
        if envelope['sha256'] != digest(p) or p['format_version'] != 1:
            raise ValueError('Checkpoint identity/format mismatch')
        if p['model_sha256'] != model.identity or p['cipher_sha256'] != stream.identity:
            raise ValueError('Checkpoint public resources differ')
        state = DictionaryState.create(stream, model, p['assignments'])
        result = cls(model, stream, seed=p['seed'], config=SearchConfig(**p['config']),
                     retrieval_config=RetrievalConfig(**p['retrieval_config']), state=state, clock=clock)
        s, r = result.scorer, result.retriever
        s._generation = p['generation']
        s._scores, s._score = list(p['event_scores']), p['score']
        s.validate()
        result.rng.setstate(tuples(p['search_rng']))
        r.rng.setstate(tuples(p['retrieval_rng']))
        r.rows = OrderedDict()
        for raw in p['rows']:
            row = CandidateRow(raw['cipher'], raw['generation'], tuple(Candidate(
                c['word_id'], c['log_delta'], tuple(c['sources'])) for c in raw['candidates']),
                raw['pool_size'], tuple(raw['proposed_exploration']))
            r.rows[row.cipher] = row
        r.archives = OrderedDict((c, tuple(words)) for c, words in p['archives'])
        r.entry_count = sum(len(row.candidates) for row in r.rows.values())
        r.archive_entry_count = sum(map(len, r.archives.values()))
        if r.entry_count > r.config.total_entries or r.archive_entry_count > r.config.total_entries:
            raise ValueError('Checkpoint exceeds candidate budgets')
        r.contexts._cache = OrderedDict((tuple(k), tuple(v)) for k, v in p['context_cache'])
        if len(r.contexts._cache) > r.config.cache_queries:
            raise ValueError('Checkpoint exceeds context-cache budget')
        r.contexts.cache_hits, r.contexts.cache_misses = p['cache_hits'], p['cache_misses']
        r.refresh_count = p['refresh_count']
        for field in ('step', 'accepted', 'noops', 'validations', 'initial_score', 'source_counts', 'stop_reason'):
            setattr(result, field, p[field])
        result.joint_archive = [(score, tuple(key)) for score, key in p['joint_archive']]
        for score, key in result.joint_archive:
            from .incremental import full_score
            archived = DictionaryState.create(stream, model, key)
            if abs(full_score(model, stream, archived) - score) > 1e-7:
                raise ValueError('Checkpoint joint hypothesis score mismatch')
        if not 0 <= result.step <= result.config.proposals:
            raise ValueError('Checkpoint step outside schedule')
        result.elapsed_seconds = p['elapsed_seconds'] + clock() - started
        return result
