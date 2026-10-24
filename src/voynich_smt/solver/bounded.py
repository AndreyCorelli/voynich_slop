"""Null-aware finite recovery and full-codebook complexity optimization.

Unlike the fast feasibility model, this formulation keeps all alphabet mappings
symbolic. Unobserved codes are never completed at an arbitrary maximum length.
"""

from collections import Counter
from dataclasses import asdict
from time import perf_counter

import z3

from voynich_smt.cipher.base import Encoder, NullInsertion
from voynich_smt.metrics.complexity import measurements, weighted_score
from voynich_smt.models.text import Text
from voynich_smt.models.settings import HomophoneSelection
from voynich_smt.cipher.selection import accepts as selection_accepts
from .selection import constrain as constrain_selection
from voynich_smt.solver.recovery import Recovery


def recover_bounded(plaintext, ciphertext, plain_alphabet, cipher_alphabet, bounds,
                    timeout_ms, domains, dictionary, min_word_length, max_word_length,
                    nulls, optimization, selection=HomophoneSelection()):
    if type(timeout_ms) is not int or timeout_ms <= 0:
        raise ValueError("Timeout must be a positive integer")
    if plaintext is not None:
        plaintext.validate(plain_alphabet)
    ciphertext.validate(cipher_alphabet)
    domains = domains or {}
    for i, allowed in domains.items():
        if plaintext is None or type(i) is not int or not 0 <= i < plaintext.size or not allowed:
            raise ValueError("Invalid plaintext domain")
        for symbol in allowed:
            plain_alphabet.index(symbol)
    started = perf_counter()
    solver = z3.Optimize() if optimization.enabled else z3.Tactic("qffd").solver()
    solver.set(timeout=timeout_ms)
    if optimization.enabled:
        solver.set(priority="lex")
    else:
        solver.set(random_seed=0)
    variables = []
    n, h, c, limit = (len(plain_alphabet.symbols), bounds.max_homophones,
                      len(cipher_alphabet.symbols), bounds.max_code_length)
    leaf_count = c ** limit

    def integer(name, upper):
        v = z3.Int(name)
        solver.add(v >= 0, v <= upper)
        variables.append(v)
        return v

    observed_counts = Counter(g for w in ciphertext.words for g in w)
    is_null = []
    for ci, glyph in enumerate(cipher_alphabet.symbols):
        flag = z3.Bool(f"null_{ci}") if nulls.enabled and observed_counts[glyph] else z3.BoolVal(False)
        if not z3.is_false(flag):
            variables.append(flag)
        is_null.append(flag)
    distinct_nulls = z3.Sum([z3.If(flag, 1, 0) for flag in is_null])
    null_occurrences = z3.Sum([z3.If(is_null[i], observed_counts[g], 0)
                               for i, g in enumerate(cipher_alphabet.symbols)])
    solver.add(distinct_nulls <= nulls.max_distinct_symbols,
               null_occurrences <= nulls.max_occurrences)
    for word in ciphertext.words:
        for start in range(len(word) - nulls.max_consecutive):
            solver.add(z3.Not(z3.And([is_null[cipher_alphabet.index(g)]
                                      for g in word[start:start + nulls.max_consecutive + 1]])))

    counts = [integer(f"count_{p}", h) for p in range(n)]
    lengths, lows, highs, glyphs = [], [], [], []
    for p in range(n):
        solver.add(counts[p] >= 1)
        lengths.append([])
        lows.append([])
        highs.append([])
        glyphs.append([])
        for k in range(h):
            active = k < counts[p]
            ln = integer(f"length_{p}_{k}", limit)
            lo = integer(f"low_{p}_{k}", leaf_count - 1)
            hi = integer(f"high_{p}_{k}", leaf_count)
            gs = [integer(f"glyph_{p}_{k}_{j}", c - 1) for j in range(limit)]
            lengths[p].append(ln)
            lows[p].append(lo)
            highs[p].append(hi)
            glyphs[p].append(gs)
            solver.add(z3.If(active, z3.And(ln >= bounds.min_code_length,
                                           z3.Or([z3.And(ln == size, hi == lo + c ** (limit - size))
                                                  for size in range(bounds.min_code_length, limit + 1)])),
                             z3.And(ln == 0, lo == 0, hi == 0)))
            solver.add(lo == z3.Sum([g * c ** (limit - j - 1) for j, g in enumerate(gs)]))
            for j, g in enumerate(gs):
                solver.add(z3.Implies(j >= ln, g == 0))
                for ci in range(c):
                    solver.add(z3.Implies(z3.And(active, j < ln, g == ci), z3.Not(is_null[ci])))
            if k and selection.mode == "free":
                solver.add(z3.Implies(active, lows[p][k - 1] < lo))
    entries = [(k < counts[p], lows[p][k], highs[p][k]) for p in range(n) for k in range(h)]
    for i, (active, lo, hi) in enumerate(entries):
        for other, other_lo, other_hi in entries[i + 1:]:
            solver.add(z3.Implies(z3.And(active, other), z3.Or(hi <= other_lo, other_hi <= lo)))

    def gap(word, before, after):
        if nulls.max_consecutive == 0:
            solver.add(after == before)
            return
        solver.add(z3.Or([
            z3.And(before == b, after == e,
                   *[is_null[cipher_alphabet.index(g)] for g in word[b:e]])
            for b in range(len(word) + 1)
            for e in range(b, min(len(word), b + nulls.max_consecutive) + 1)]))

    word_records = []
    token_index = 0
    cycle_history = []
    if plaintext is not None and len(plaintext.words) != len(ciphertext.words):
        solver.add(False)
    else:
        for wi, word in enumerate(ciphertext.words):
            if selection.reset == "word":
                cycle_history.clear()
            if dictionary is not None:
                # Raw prefix pruning is invalid when leading nulls are possible.
                candidates = tuple(w for w in dictionary.words
                                   if min_word_length <= len(w) <= max_word_length
                                   and len(w) * bounds.min_code_length <= len(word)
                                   <= len(w) * limit + nulls.max_occurrences)
                if not candidates:
                    solver.add(False)
                    continue
                slots = max(map(len, candidates))
                size = integer(f"word_size_{wi}", slots)
                tokens = [integer(f"plain_{wi}_{i}", n) for i in range(slots)]
                solver.add(z3.Or([z3.And(size == len(w), *[
                    tokens[i] == (plain_alphabet.index(w[i]) if i < len(w) else n)
                    for i in range(slots)]) for w in candidates]))
            else:
                source = plaintext.words[wi]
                slots = len(source)
                size = z3.IntVal(slots)
                candidates = None
                tokens = []
                for i, symbol in enumerate(source):
                    allowed = domains.get(token_index + i, (symbol,))
                    p = integer(f"plain_{wi}_{i}", n - 1)
                    solver.add(z3.Or([p == plain_alphabet.index(s) for s in allowed]))
                    tokens.append(p)
            boundaries = [integer(f"boundary_{wi}_{i}", len(word)) for i in range(slots + 1)]
            solver.add(boundaries[0] == 0)
            starts, choices = [], []
            for i, p in enumerate(tokens):
                active = i < size
                start = integer(f"start_{wi}_{i}", len(word))
                choice = integer(f"choice_{wi}_{i}", h - 1)
                selected_length = integer(f"selected_length_{wi}_{i}", limit)
                selected_low = integer(f"selected_low_{wi}_{i}", leaf_count - 1)
                solver.add(z3.Implies(z3.Not(active), z3.And(start == boundaries[i], choice == 0,
                                                           selected_length == 0, selected_low == 0)))
                # The gap is also valid for inactive slots: it has zero length.
                gap(word, boundaries[i], start)
                solver.add(boundaries[i + 1] == start + selected_length)
                ids = ({plain_alphabet.index(w[i]) for w in candidates if i < len(w)}
                       if candidates is not None else
                       {plain_alphabet.index(s) for s in domains.get(token_index + i, (source[i],))})
                for pp in sorted(ids):
                    for kk in range(h):
                        solver.add(z3.Implies(z3.And(active, p == pp, choice == kk),
                                             z3.And(kk < counts[pp], selected_length == lengths[pp][kk],
                                                    selected_low == lows[pp][kk])))
                matches = []
                for ci in range(len(word)):
                    for length in range(bounds.min_code_length, min(limit, len(word) - ci) + 1):
                        lo = sum(cipher_alphabet.index(word[ci + j]) * c ** (limit - j - 1)
                                 for j in range(length))
                        matches.append(z3.And(start == ci, selected_length == length, selected_low == lo))
                solver.add(z3.Implies(active, z3.Or(matches)))
                constrain_selection(solver, selection, p, choice, active, counts, cycle_history, ids, h)
                cycle_history.append(p)
                starts.append(start)
                choices.append(choice)
            gap(word, boundaries[-1], z3.IntVal(len(word)))
            word_records.append((tokens, size, choices, starts, boundaries))
            token_index += slots

    mappings = z3.Sum(counts)
    book_glyphs = z3.Sum([ln for row in lengths for ln in row])
    expressions = {
        "mappings": mappings, "additional_homophones": mappings - n,
        "total_codebook_glyphs": book_glyphs, "extra_code_glyphs": book_glyphs - mappings,
        "distinct_null_symbols": distinct_nulls, "null_occurrences": null_occurrences,
    }
    if optimization.method == "weighted":
        objectives = [("weighted_score", z3.Sum([expressions[name] * getattr(optimization.weights, name)
                                                 for name in optimization.weights.__dataclass_fields__]))]
    else:
        objectives = [(name, expressions[name]) for name in
                      ("distinct_null_symbols", "null_occurrences", "additional_homophones", "total_codebook_glyphs")]
    handles = [solver.minimize(expression) for _, expression in objectives] if optimization.enabled else []
    construction = perf_counter() - started
    check_start = perf_counter()
    outcome = solver.check()
    result = Recovery(str(outcome).upper(), perf_counter() - check_start,
                      statistics={k: solver.statistics().get_key_value(k) for k in solver.statistics().keys()},
                      capacity={"symbolic_variables": len(variables), "constraints": len(solver.assertions()),
                                "codebook_slots": n * h, "representation": "bounded-full-codebook",
                                "selection": asdict(selection),
                                "selection_counters": n if selection.mode == "cycle" else 0,
                                "construction_seconds": construction})
    result.optimization = {"enabled": optimization.enabled, "method": optimization.method,
                           "optimality_proven": False, "objectives": []}
    if outcome == z3.unknown:
        result.reason_unknown = solver.reason_unknown()
        return result
    if outcome == z3.unsat:
        return result
    model = solver.model()

    def value(expr):
        return model.eval(expr, model_completion=True).as_long()

    null_symbols = tuple(g for i, g in enumerate(cipher_alphabet.symbols)
                         if z3.is_true(model.eval(is_null[i], model_completion=True)))
    encoder = Encoder({s: tuple(tuple(cipher_alphabet.symbols[value(g)]
                                     for g in glyphs[p][k][:value(lengths[p][k])])
                               for k in range(value(counts[p])))
                       for p, s in enumerate(plain_alphabet.symbols)}, null_symbols)
    words, choices, spans = [], [], []
    for tokens, size, selections, starts, boundaries in word_records:
        count = value(size)
        words.append(tuple(plain_alphabet.symbols[value(p)] for p in tokens[:count]))
        choices.extend(value(k) for k in selections[:count])
        spans.append(tuple((value(starts[i]), value(boundaries[i + 1])) for i in range(count)))
    recovered = Text(tuple(words))
    insertions = tuple(NullInsertion(wi, i, g) for wi, word in enumerate(ciphertext.words)
                       for i, g in enumerate(word) if g in null_symbols)
    result.encoder, result.plaintext, result.choices = encoder, recovered, tuple(choices)
    result.nulls, result.code_spans = insertions, tuple(spans)
    result.segmentation = tuple((0,) + tuple(end for _, end in row) for row in spans) if not insertions else ()
    raw = measurements(encoder, insertions)
    result.complexity = {"raw": raw, "weighted_score": weighted_score(raw, optimization.weights),
                         "weights": asdict(optimization.weights)}
    if optimization.enabled:
        certified = True
        for (name, expression), handle in zip(objectives, handles):
            lower, upper, actual = handle.lower(), handle.upper(), value(expression)
            certified &= z3.is_int_value(lower) and z3.is_int_value(upper) and lower.as_long() == upper.as_long() == actual
            result.optimization["objectives"].append({"name": name, "value": actual,
                                                      "lower": str(lower), "upper": str(upper)})
            expected = result.complexity["weighted_score"] if name == "weighted_score" else raw[name]
            if expected != actual:
                raise RuntimeError("Complexity extraction failed independent measurement")
        result.optimization["optimality_proven"] = bool(certified)
    verify(result, ciphertext, plaintext, domains, dictionary, bounds, nulls, min_word_length, max_word_length)
    if not selection_accepts(recovered, encoder, result.choices, selection):
        raise RuntimeError("SAT explanation violated its homophone selection policy")
    result.verified = True
    result.capacity.update(raw)
    return result


def verify(result, ciphertext, plaintext, domains, dictionary, bounds, null_bounds, min_word_length, max_word_length):
    encoder, recovered = result.encoder, result.plaintext
    if encoder.encode(recovered, result.choices, result.nulls) != ciphertext or encoder.decode(ciphertext) != recovered:
        raise RuntimeError("SAT explanation failed independent encoding/decoding")
    if dictionary is not None:
        if not dictionary.accepts(recovered) or any(not min_word_length <= len(w) <= max_word_length for w in recovered.words):
            raise RuntimeError("SAT explanation violated its dictionary")
    else:
        flat_source = [s for w in plaintext.words for s in w]
        flat_recovered = [s for w in recovered.words for s in w]
        if tuple(map(len, recovered.words)) != tuple(map(len, plaintext.words)) or any(
            s not in domains.get(i, (original,)) for i, (s, original) in enumerate(zip(flat_recovered, flat_source))
        ):
            raise RuntimeError("SAT explanation violated known plaintext")
    if any(not 1 <= len(codes) <= bounds.max_homophones or any(
        not bounds.min_code_length <= len(code) <= bounds.max_code_length for code in codes
    ) for codes in encoder.codebook.values()):
        raise RuntimeError("SAT explanation violated cipher bounds")
    if len(encoder.null_symbols) > null_bounds.max_distinct_symbols or len(result.nulls) > null_bounds.max_occurrences:
        raise RuntimeError("SAT explanation violated null budgets")
    for word in ciphertext.words:
        run = 0
        for g in word:
            run = run + 1 if g in encoder.null_symbols else 0
            if run > null_bounds.max_consecutive:
                raise RuntimeError("SAT explanation violated consecutive null bounds")
    choice_index = 0
    if len(result.code_spans) != len(recovered.words) or any(
        len(row) != len(word) for row, word in zip(result.code_spans, recovered.words)
    ):
        raise RuntimeError("SAT explanation has incomplete code spans")
    for word, observed, spans in zip(recovered.words, ciphertext.words, result.code_spans):
        occupied = set()
        for symbol, (start, end) in zip(word, spans):
            code = encoder.codebook[symbol][result.choices[choice_index]]
            if observed[start:end] != code or occupied.intersection(range(start, end)):
                raise RuntimeError("SAT explanation violated its code spans")
            occupied.update(range(start, end))
            choice_index += 1
        if occupied != {i for i, g in enumerate(observed) if g not in encoder.null_symbols}:
            raise RuntimeError("SAT explanation did not cover every non-null glyph")
