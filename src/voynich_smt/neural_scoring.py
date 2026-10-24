"""Offline, whole-word-masked RoBERTa scoring; no optimizer or truth dependency."""
from dataclasses import dataclass, asdict
import math
from pathlib import Path


@dataclass(frozen=True)
class SegmentScore:
    word_log_sums: tuple[float, ...]
    word_subwords: tuple[int, ...]

    def totals(self):
        return {'word_masked_log_sum': math.fsum(self.word_log_sums),
            'word_normalized_log_sum': math.fsum(s / n for s, n in zip(self.word_log_sums, self.word_subwords)),
            'words': len(self.word_log_sums), 'subwords': sum(self.word_subwords)}


class WholeWordScorer:
    def __init__(self, model, tokenizer, *, batch_size=16, threads=4):
        import torch
        if type(batch_size) is not int or batch_size < 1 or type(threads) is not int or threads < 1:
            raise ValueError('Batch size and thread count must be positive')
        if not tokenizer.is_fast or tokenizer.mask_token_id is None or tokenizer.pad_token_id is None:
            raise ValueError('A fast tokenizer with mask/pad tokens is required')
        if model.config.model_type != 'roberta':
            raise ValueError('Scorer currently supports the standard RoBERTa architecture only')
        torch.set_num_threads(threads)
        self.model, self.tokenizer = model.to('cpu').float().eval(), tokenizer
        self.batch_size = batch_size
        self.max_length = min(tokenizer.model_max_length, model.config.max_position_embeddings - 2)
        self.cache = {}
        self.inference_rows = 0

    @classmethod
    def load(cls, path, **kwargs):
        from transformers import AutoModelForMaskedLM, AutoTokenizer
        path = Path(path)
        tokenizer = AutoTokenizer.from_pretrained(path, local_files_only=True, trust_remote_code=False)
        model = AutoModelForMaskedLM.from_pretrained(path, local_files_only=True,
                                                   trust_remote_code=False, use_safetensors=True)
        return cls(model, tokenizer, **kwargs)

    def _job(self, words, target):
        encoded = self.tokenizer(list(words), is_split_into_words=True, truncation=False)
        ids = list(encoded['input_ids'])
        if len(ids) > self.max_length:
            raise ValueError('Segment exceeds model context; silent truncation is forbidden')
        if self.tokenizer.unk_token_id in ids:
            raise ValueError('Unknown tokenizer output cannot be scored as an attested form')
        word_ids = encoded.word_ids()
        if set(w for w in word_ids if w is not None) != set(range(len(words))):
            raise ValueError('Tokenizer dropped or merged surface words')
        positions = tuple(i for i, word in enumerate(word_ids) if word == target)
        targets = tuple(ids[i] for i in positions)
        for i in positions:
            ids[i] = self.tokenizer.mask_token_id
        return ids, positions, targets

    def _batch(self, jobs):
        import torch
        width = max(len(ids) for ids, _, _ in jobs)
        inputs = torch.full((len(jobs), width), self.tokenizer.pad_token_id, dtype=torch.long)
        attention = torch.zeros_like(inputs)
        rows, positions, targets, owners = [], [], [], []
        for row, (ids, places, labels) in enumerate(jobs):
            inputs[row, :len(ids)] = torch.tensor(ids)
            attention[row, :len(ids)] = 1
            rows.extend([row] * len(places))
            positions.extend(places)
            targets.extend(labels)
            owners.extend([row] * len(places))
        with torch.inference_mode():
            # Compute vocabulary logits only at scored positions. This is the
            # same LM head as forward(), avoiding a [batch, length, vocab] buffer.
            hidden = self.model.roberta(input_ids=inputs, attention_mask=attention).last_hidden_state
            logits = self.model.lm_head(hidden[rows, positions])
            values = torch.log_softmax(logits, dim=-1).gather(1, torch.tensor(targets)[:, None]).squeeze(1).tolist()
        result = [[] for _ in jobs]
        for row, value in zip(owners, values):
            result[row].append(value)
        self.inference_rows += len(jobs)
        return [(math.fsum(values), len(values)) for values in result]

    def segment(self, words, *, context_radius=None):
        words = tuple(words)
        if any(not isinstance(w, str) or not w or any(c.isspace() for c in w) for w in words):
            raise ValueError('Segments require nonempty surface words')
        if context_radius is not None and (type(context_radius) is not int or context_radius < 0):
            raise ValueError('Context radius must be nonnegative or None')
        key = words, context_radius
        if key in self.cache:
            return self.cache[key]
        jobs = []
        for index in range(len(words)):
            first = 0 if context_radius is None else max(0, index - context_radius)
            last = len(words) if context_radius is None else min(len(words), index + context_radius + 1)
            jobs.append(self._job(words[first:last], index - first))
        scores = []
        for first in range(0, len(jobs), self.batch_size):
            scores.extend(self._batch(jobs[first:first + self.batch_size]))
        result = SegmentScore(tuple(s for s, _ in scores), tuple(n for _, n in scores))
        if any(not math.isfinite(s) for s in result.word_log_sums):
            raise ValueError('Nonfinite neural score')
        self.cache[key] = result
        return result

    def score(self, segments, *, context_radius=None):
        scores = [self.segment(s, context_radius=context_radius).totals() for s in segments]
        return {key: (sum(s[key] for s in scores) if key in ('words', 'subwords')
                      else math.fsum(s[key] for s in scores))
                for key in ('word_masked_log_sum', 'word_normalized_log_sum', 'words', 'subwords')}
