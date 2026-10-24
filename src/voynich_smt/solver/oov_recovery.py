"""Experimental OOV feasibility builder, isolated from frozen strict baselines.

Derived from recovery._recover; dictionary pruning and symbol domains must be
relaxed together with membership. Budget counts word occurrences, not types.
"""
from dataclasses import asdict
from time import perf_counter
import z3
from voynich_smt.cipher.base import Bounds, Encoder
from voynich_smt.cipher.selection import accepts as selection_accepts
from voynich_smt.models.settings import HomophoneSelection, Optimization
from voynich_smt.models.alphabet import Alphabet
from voynich_smt.models.text import Text
from voynich_smt.language.dictionary import WordDictionary, CandidateGraph, PrefixRelation
from .recovery import Recovery
from .selection import constrain as constrain_selection
from .key_evidence import fixed_word_conflicts, forced_cycle_conflicts


def recover_oov(request, max_oov_words=1):
    if request.representation != 'finite' or request.nulls.enabled or request.optimization.enabled:
        raise ValueError('OOV requires finite null-free feasibility')
    return _recover(None, request.ciphertext, request.plaintext_alphabet,
        request.ciphertext_alphabet, request.bounds, request.timeout_ms,
        dictionary=request.dictionary, min_word_length=request.min_word_length,
        max_word_length=request.max_word_length or max(map(len,request.dictionary.words)),
        selection=request.selection,dictionary_encoding=request.dictionary_encoding,
        codeword_domains='observed',max_oov_words=max_oov_words)

def _recover(plaintext: Text | None, ciphertext: Text, plain_alphabet: Alphabet,
             cipher_alphabet: Alphabet, bounds: Bounds, timeout_ms: int,
             domains: dict[int, tuple[str, ...]] | None = None,
             dictionary: WordDictionary | None = None,
             min_word_length: int = 1, max_word_length: int = 1,
             representation: str = "finite", selection=HomophoneSelection(), observed_words=None,
             dictionary_encoding="flat", guidance=None, key_exclusions=(),
             cycle_encoding="auto", known_segmentation=None, known_word_lengths=None,
             solver_backend="auto", codeword_domains="none", word_pairs=None, language_objective=None, max_oov_words=1) -> Recovery:
    if type(max_oov_words) is not int or max_oov_words < 0:
        raise ValueError("Invalid OOV occurrence budget")
    if max_oov_words and (dictionary is None or plaintext is not None or representation != "finite" or observed_words is not None or word_pairs is not None or language_objective is not None or guidance or known_word_lengths is not None):
        raise ValueError("OOV recovery requires unguided finite hidden feasibility")
    if codeword_domains not in {"none", "observed"}:
        raise ValueError("Unknown codeword domain strategy")
    if codeword_domains == "observed" and (representation != "finite" or observed_words is not None):
        raise ValueError("Observed domains require finite recovery with all words observed")
    if word_pairs is not None:
        if representation != "finite" or dictionary is None or plaintext is not None or observed_words is not None:
            raise ValueError("Word pairs require finite hidden dictionary recovery with all words observed")
        word_pairs = tuple(word_pairs)
        if any(len(pair) != 2 or any(tuple(w) not in dictionary.words for w in pair)
               for pair in word_pairs):
            raise ValueError("Word pairs must contain two dictionary words")
        word_pairs = frozenset((tuple(a), tuple(b)) for a, b in word_pairs)
    if language_objective is not None:
        if representation != "finite" or dictionary is None or plaintext is not None or observed_words is not None or guidance:
            raise ValueError("Language objective requires unguided finite hidden dictionary recovery")
        from .language_objective import validate_objective
        validate_objective(language_objective, dictionary)
    record_formula = solver_backend != "auto"
    if cycle_encoding == "auto":
        cycle_encoding = "state" if bounds.max_homophones == 2 and selection.mode == "cycle" else "history"
    if cycle_encoding not in {"history", "state"}:
        raise ValueError("Unknown cycle encoding")
    if cycle_encoding == "state" and (bounds.max_homophones != 2 or selection.mode != "cycle"):
        raise ValueError("State encoding requires H2 cycles")
    if solver_backend == "auto":
        solver_backend = "qffd" if representation == "finite" else "smt"
    if solver_backend not in {"qffd", "smt"} or (solver_backend == "qffd" and representation != "finite"):
        raise ValueError("Invalid solver backend for representation")
    if timeout_ms <= 0:
        raise ValueError("Timeout must be positive")
    if representation not in {"ite", "array", "interval", "chunk", "finite"}:
        raise ValueError("Unknown codebook representation")
    if observed_words is not None:
        if representation != "finite" or dictionary is None or plaintext is not None:
            raise ValueError("Masked word observations require finite dictionary recovery")
        if any(type(i) is not int or not 0 <= i < len(ciphertext.words) for i in observed_words):
            raise ValueError("Invalid observed word indices")
        observed_words = set(observed_words)
    if plaintext is not None:
        plaintext.validate(plain_alphabet)
    ciphertext.validate(cipher_alphabet)
    domains = domains or {}
    for position, symbols in domains.items():
        if plaintext is None or not 0 <= position < plaintext.size or not symbols:
            raise ValueError("Invalid symbolic plaintext domain")
        for symbol in symbols:
            plain_alphabet.index(symbol)
    if known_segmentation is not None:
        if representation != "finite" or dictionary is None or plaintext is not None or observed_words is not None:
            raise ValueError("Boundary diagnostics require finite dictionary recovery with all words observed")
        from .segmented import validate_segmentation
        known_segmentation = validate_segmentation(ciphertext, bounds, known_segmentation)
    if known_word_lengths is not None:
        if known_segmentation is not None:
            raise ValueError("Supply boundaries or word lengths, not both")
        if representation != "finite" or dictionary is None or plaintext is not None or observed_words is not None:
            raise ValueError("Length diagnostics require finite dictionary recovery with all words observed")
        from .segmented import validate_word_lengths
        known_word_lengths = validate_word_lengths(ciphertext, bounds, known_word_lengths)
    oracle_lengths = (tuple(len(row)-1 for row in known_segmentation)
                      if known_segmentation is not None else known_word_lengths)
    start = perf_counter()
    candidate_graph = (dictionary.candidate_graph(ciphertext, bounds, min_word_length, max_word_length)
                       if dictionary is not None and observed_words is None else None)
    if observed_words is not None:
        indices = sorted(observed_words)
        selected = dictionary.candidate_graph(Text(tuple(ciphertext.words[i] for i in indices)),
                                               bounds, min_word_length, max_word_length)
        candidates = [dictionary.candidates(len(w), bounds, min_word_length, max_word_length)
                      for w in ciphertext.words]
        for j, i in enumerate(indices):
            candidates[i] = selected.candidates[j]
        candidate_graph = CandidateGraph(tuple(candidates), tuple(
            PrefixRelation(indices[r.left], indices[r.right], r.shared_tokens, r.prefix)
            for r in selected.relations), selected.pruned_candidates)
    if max_oov_words:
        # Pairwise dictionary pruning assumes both words are dictionary members.
        # It is unsound when the solver may exempt either occurrence.
        candidate_graph = CandidateGraph(tuple(dictionary.candidates(len(w), bounds, min_word_length, max_word_length) for w in ciphertext.words), (), 0)
    if oracle_lengths is not None:
        filtered = tuple(tuple(w for w in candidates if len(w) == count)
                         for candidates, count in zip(candidate_graph.candidates, oracle_lengths))
        candidate_graph = CandidateGraph(filtered, candidate_graph.relations,
            candidate_graph.pruned_candidates + sum(map(len, candidate_graph.candidates)) - sum(map(len, filtered)))
    solver = z3.Tactic("qffd").solver() if solver_backend == "qffd" else z3.Solver()
    solver.set(timeout=timeout_ms, random_seed=0)
    pinned = set(guidance["pinned_symbols"]) if guidance else set()
    excluded_owners = {segment["symbol"] for rule in key_exclusions if rule["kind"] == "word"
                       for segment in rule["segments"]}
    excluded_owners.update(s for rule in key_exclusions if rule["kind"] == "pin_core"
                           for s in rule["mappings"])
    protected = pinned | excluded_owners
    pin_guards = {s: z3.Bool(f"pin_{plain_alphabet.index(s)}") for s in sorted(pinned)}
    if pinned:
        solver.set(unsat_core=True)
        if guidance["minimize_core"]:
            solver.set("core.minimize", True)
    variables = []

    def integer(name):
        value = z3.Int(name)
        variables.append(value)
        if representation == "finite":
            # qffd needs explicit finite ranges before eliminating integer terms.
            upper = max(c ** length, n, h,
                        max(map(len, ciphertext.words), default=0),
                        max(map(len, plaintext.words), default=0) if plaintext is not None else max_word_length)
            solver.add(value >= 0, value <= upper)
        return value

    n, h, length, c = (len(plain_alphabet.symbols), bounds.max_homophones,
                        bounds.max_code_length, len(cipher_alphabet.symbols))
    counts = [integer(f"count_{p}") for p in range(n)]
    lengths = [[integer(f"length_{p}_{k}") for k in range(h)] for p in range(n)]
    interval = representation in {"interval", "chunk", "finite"}
    glyphs = (None if interval else [[[integer(f"glyph_{p}_{k}_{j}") for j in range(length)]
                                     for k in range(h)] for p in range(n)])
    starts = [[integer(f"start_{p}_{k}") for k in range(h)] for p in range(n)] if interval else None
    ends = [[integer(f"end_{p}_{k}") for k in range(h)] for p in range(n)] if interval else None
    entries = []
    for p in range(n):
        solver.add(counts[p] >= (0 if interval else 1), counts[p] <= h)
        ranks = []
        for k in range(h):
            active = k < counts[p]
            ln = lengths[p][k]
            solver.add(z3.If(active, z3.And(ln >= bounds.min_code_length, ln <= length), ln == 0))
            if interval:
                lo, hi = starts[p][k], ends[p][k]
                solver.add(lo >= 0, lo < c ** length, hi <= c ** length,
                           z3.If(active, z3.Or([
                               z3.And(ln == size, lo % (c ** (length - size)) == 0,
                                      hi == lo + c ** (length - size))
                               for size in range(bounds.min_code_length, length + 1)]),
                               z3.And(lo == 0, hi == 0)))
                rank = lo
                entries.append((active, lo, hi))
            else:
                gs = glyphs[p][k]
                for j, g in enumerate(gs):
                    solver.add(g >= 0, g < c, z3.Implies(j >= ln, g == 0))
                # Base-(c+1) encoding with zero padding gives a strict canonical order.
                rank = sum(z3.If(j < ln, gs[j] + 1, 0) * (c + 1) ** (length - j - 1)
                           for j in range(length))
                entries.append((active, ln, gs))
            if k and selection.mode == "free":
                solver.add(z3.Implies(active, ranks[-1] < rank))
            ranks.append(rank)
    for i, (active_a, a1, a2) in enumerate(entries):
        for active_b, b1, b2 in entries[i + 1:]:
            distinct = (z3.Or(a2 <= b1, b2 <= a1) if interval else z3.Or([
                z3.And(j < a1, j < b1, a2[j] != b2[j]) for j in range(length)]))
            solver.add(z3.Implies(z3.And(active_a, active_b), distinct))

    def code_matches(p, k, code):
        lo = sum(cipher_alphabet.index(g) * c ** (length - j - 1) for j, g in enumerate(code))
        return z3.And(k < counts[p], lengths[p][k] == len(code), starts[p][k] == lo)

    def owns(symbol, code):
        p = plain_alphabet.index(symbol)
        return z3.Or([code_matches(p, k, code) for k in range(h)])

    for symbol in excluded_owners:
        # These are real full-key owners even when absent from the suffix.
        # Completion or removal of unvisited codes could evade a learned rule.
        solver.add(counts[plain_alphabet.index(symbol)] >= 1)
    for rule in key_exclusions:
        if rule["kind"] == "cycle_pair":
            for p, symbol in enumerate(plain_alphabet.symbols):
                solver.add(z3.Not(z3.And(counts[p] == 2,
                    *[owns(symbol, code) for code in rule["codes"]])))
        elif rule["kind"] == "word":
            solver.add(z3.Not(z3.And([owns(s["symbol"], s["code"]) for s in rule["segments"]])))
        elif rule["kind"] == "pin_core":
            matches = []
            for symbol, codes in rule["mappings"].items():
                p = plain_alphabet.index(symbol)
                matches.append(z3.And(counts[p] == len(codes), z3.Or([
                    z3.And([code_matches(p, k, codes[(k + r) % len(codes)])
                            for k in range(len(codes))]) for r in range(len(codes))])))
            solver.add(z3.Not(z3.And(matches)))

    hint_count = 0
    forced_conflicts = []
    word_conflicts = []
    if guidance:
        word_conflicts = fixed_word_conflicts(ciphertext, guidance["encoder"], pinned,
                                             dictionary, min_word_length, max_word_length)
        for conflict in word_conflicts:
            solver.add(z3.Not(z3.And([pin_guards[s] for s in conflict["pinned_symbols"]])))
        if selection.reset == "text":
            forced_conflicts = forced_cycle_conflicts(ciphertext, guidance["encoder"], sorted(pinned))
            for conflict in forced_conflicts:
                # With this complete homophone set pinned, prefix-freeness forces
                # a start-of-word cycle contradiction regardless of other keys.
                solver.add(z3.Not(pin_guards[conflict["symbol"]]))
        for p, symbol in enumerate(plain_alphabet.symbols):
            codes = guidance["encoder"].codebook[symbol]
            if symbol in pinned:
                rotations = range(len(codes)) if guidance["rotate"] else (0,)
                options = []
                for rotation in rotations:
                    constraints = [counts[p] == len(codes)]
                    for k in range(len(codes)):
                        code = codes[(k + rotation) % len(codes)]
                        lo = sum(cipher_alphabet.index(g) * c ** (length - j - 1)
                                 for j, g in enumerate(code))
                        constraints.extend((lengths[p][k] == len(code), starts[p][k] == lo))
                    options.append(z3.And(constraints))
                solver.add(z3.Implies(pin_guards[symbol], z3.Or(options)))
            if symbol in guidance["hint_symbols"]:
                solver.set_initial_value(counts[p], len(codes)); hint_count += 1
                for k, code in enumerate(codes):
                    lo = sum(cipher_alphabet.index(g) * c ** (length - j - 1)
                             for j, g in enumerate(code))
                    solver.set_initial_value(lengths[p][k], len(code))
                    solver.set_initial_value(starts[p][k], lo); hint_count += 2

    # Symbols which cannot occur need only one code. Their labels are freely
    # permutable, so order these unused entries without excluding explanations.
    possible = ({s for candidates in candidate_graph.candidates for w in candidates for s in w} if dictionary is not None
                else {s for w in plaintext.words for s in w})
    if max_oov_words: possible.update(plain_alphabet.symbols)
    possible.update(s for allowed in domains.values() for s in allowed)
    unused = [p for p, symbol in enumerate(plain_alphabet.symbols) if symbol not in possible]
    unused_ranks = []
    for p in unused:
        if plain_alphabet.symbols[p] in protected:
            continue
        if interval:
            solver.add(counts[p] == 0)
            continue
        solver.add(counts[p] == 1)
        rank = (starts[p][0] if interval else sum(z3.If(j < lengths[p][0], glyphs[p][0][j] + 1, 0)
                   * (c + 1) ** (length - j - 1) for j in range(length)))
        if unused_ranks:
            solver.add(unused_ranks[-1] < rank)
        unused_ranks.append(rank)

    def select(values, index):
        if z3.is_int_value(index):
            return values[index.as_long()]
        result = values[-1]
        for k in reversed(range(len(values) - 1)):
            result = z3.If(index == k, values[k], result)
        return result

    if representation in {"array", "interval", "chunk"}:
        count_table = z3.Array("count_table", z3.IntSort(), z3.IntSort())
        length_table = z3.Array("length_table", z3.IntSort(), z3.IntSort())
        variables.extend([count_table, length_table])
        if interval:
            start_table = z3.Array("start_table", z3.IntSort(), z3.IntSort())
            end_table = z3.Array("end_table", z3.IntSort(), z3.IntSort())
            variables.extend([start_table, end_table])
        else:
            glyph_table = z3.Array("glyph_table", z3.IntSort(), z3.IntSort())
            variables.append(glyph_table)
        for p in range(n):
            solver.add(count_table[p] == counts[p])
            for k in range(h):
                solver.add(length_table[p * h + k] == lengths[p][k])
                if interval:
                    solver.add(start_table[p * h + k] == starts[p][k], end_table[p * h + k] == ends[p][k])
                else:
                    for j in range(length):
                        solver.add(glyph_table[(p * h + k) * length + j] == glyphs[p][k][j])

    choices, symbols, positions, word_sizes = [], [], [], []
    cycle_history = []
    cycle_states = {}
    repeated = {}
    dictionary_symbols = {}
    oov_flags = []
    if plaintext is not None and len(plaintext.words) != len(ciphertext.words):
        solver.add(False)
    else:
        index = 0
        for wi, cw in enumerate(ciphertext.words):
            if selection.reset == "word":
                cycle_history.clear()
                cycle_states.clear()
            if dictionary is not None:
                candidates = candidate_graph.candidates[wi]
                if not candidates and not max_oov_words:
                    solver.add(False)
                    continue
                slots = (min(max_word_length, len(cw)//bounds.min_code_length) if max_oov_words else max(map(len, candidates)))
                word_size = integer(f"word_size_{wi}")
                # Dictionary membership links every symbolic token and its length.
                word_symbols = [integer(f"plain_{wi}_{pi}") for pi in range(slots)]
                solver.add(word_size >= (max(min_word_length, (len(cw)+bounds.max_code_length-1)//bounds.max_code_length) if max_oov_words else min(map(len, candidates))), word_size <= slots,
                           *[z3.And(p >= 0, p <= n) for p in word_symbols])
                from .dictionary_encoding import membership
                entry_id = None
                if dictionary_encoding == "entry":
                    entry_id = z3.Int(f"dictionary_entry_{wi}")
                    variables.append(entry_id)
                member = membership(candidates, word_symbols, word_size, plain_alphabet, dictionary_encoding, entry_id)
                if max_oov_words:
                    outside = z3.Bool(f"oov_{wi}")
                    solver.add(outside == z3.Not(member))
                    oov_flags.append(outside)
                    # Padding belongs outside the decoded word; active slots are letters.
                    for pi, token in enumerate(word_symbols):
                        solver.add(z3.If(pi < word_size, token < n, token == n))
                else:
                    solver.add(member)
                if guidance and wi in guidance["word_hints"]:
                    word = guidance["word_hints"][wi]
                    solver.set_initial_value(word_size, len(word)); hint_count += 1
                    for pi, variable in enumerate(word_symbols):
                        value = plain_alphabet.index(word[pi]) if pi < len(word) else n
                        solver.set_initial_value(variable, value); hint_count += 1
                # Unique decoding entails equal plaintext for identical ciphertext
                # words. State it directly to avoid rediscovering it via the key.
                observed = observed_words is None or wi in observed_words
                if observed and cw in repeated:
                    previous_size, previous_symbols = repeated[cw]
                    solver.add(word_size == previous_size,
                               *[a == b for a, b in zip(word_symbols, previous_symbols)])
                elif observed:
                    repeated[cw] = word_size, word_symbols
                word_sizes.append(word_size)
                dictionary_symbols[wi] = word_size, word_symbols
            else:
                pw = plaintext.words[wi]
                slots = len(pw)
                word_size = z3.IntVal(slots)
                word_symbols = []
                for pi, symbol in enumerate(pw):
                    allowed = domains.get(index + pi, (symbol,))
                    if len(allowed) == 1:
                        word_symbols.append(z3.IntVal(plain_alphabet.index(allowed[0])))
                    else:
                        token = integer(f"plain_{wi}_{pi}")
                        solver.add(token >= 0, token < n)
                        solver.add(z3.Or([token == plain_alphabet.index(s) for s in allowed]))
                        word_symbols.append(token)
                word_sizes.append(word_size)
            observed = z3.K(z3.IntSort(), z3.IntVal(-1))
            for ci, symbol in enumerate(cw):
                if interval:
                    # A padded maximum-length window represents a leaf in the
                    # c-ary prefix tree. Containment means matching a code prefix.
                    window = sum(cipher_alphabet.index(cw[ci + j]) * c ** (length - j - 1)
                                 for j in range(min(length, len(cw) - ci)))
                    observed = z3.Store(observed, ci, window)
                else:
                    observed = z3.Store(observed, ci, cipher_alphabet.index(symbol))
            offsets = [integer(f"offset_{wi}_{i}") for i in range(slots + 1)]
            solver.add(offsets[0] == 0, offsets[-1] == len(cw))
            if known_segmentation is not None:
                row = known_segmentation[wi]
                solver.add(word_size == len(row)-1,
                           *[offset == (row[i] if i < len(row) else len(cw))
                             for i, offset in enumerate(offsets)])
            if known_word_lengths is not None:
                solver.add(word_size == known_word_lengths[wi])
            positions.append(offsets)
            for pi, p in enumerate(word_symbols):
                active = pi < word_size
                choice = integer(f"choice_{index}")
                if representation == "finite":
                    code_length = integer(f"selected_length_{index}")
                    selected_start = integer(f"selected_start_{index}")
                    solver.add(choice >= 0, choice < h,
                               code_length >= 0, code_length <= length,
                               selected_start >= 0, selected_start < c ** length,
                               z3.Implies(z3.Not(active), z3.And(choice == 0, code_length == 0, selected_start == 0)))
                    possible_ids = ({plain_alphabet.index(w[pi]) for w in candidates if pi < len(w)}
                                    if dictionary is not None and not max_oov_words else
                                    (set(range(n)) if max_oov_words else {plain_alphabet.index(s) for s in domains.get(index, (pw[pi],))}))
                    for pp in sorted(possible_ids):
                        for kk in range(h):
                            solver.add(z3.Implies(z3.And(active, p == pp, choice == kk),
                                                 z3.And(kk < counts[pp], code_length == lengths[pp][kk],
                                                        selected_start == starts[pp][kk])))
                else:
                    selected_count = count_table[p] if representation != "ite" else select(counts, p)
                    solver.add(choice >= 0, z3.If(active, choice < selected_count, choice == 0))
                if representation in {"array", "interval", "chunk"}:
                    code_length = length_table[p * h + choice]
                elif representation == "ite":
                    code_length = select([select(row, choice) for row in lengths], p)
                chosen_length = z3.If(active, code_length, 0)
                solver.add(offsets[pi] >= 0, offsets[pi + 1] <= len(cw),
                           offsets[pi + 1] == offsets[pi] + chosen_length)
                solver.add(z3.Implies(active, z3.And(
                    offsets[pi] >= pi * bounds.min_code_length,
                    offsets[pi] <= pi * length,
                    offsets[pi + 1] >= len(cw) - (word_size - pi - 1) * length,
                    offsets[pi + 1] <= len(cw) - (word_size - pi - 1) * bounds.min_code_length)))
                if representation in {"chunk", "finite"}:
                    matches = []
                    for ci in range(pi * bounds.min_code_length, min(len(cw), pi * length + 1)):
                        for size in range(bounds.min_code_length, min(length, len(cw) - ci) + 1):
                            prefix = sum(cipher_alphabet.index(cw[ci + j]) * c ** (length - j - 1)
                                         for j in range(size))
                            matches.append(z3.And(offsets[pi] == ci, chosen_length == size,
                                                  (selected_start if representation == "finite"
                                                   else start_table[p * h + choice]) == prefix))
                    if observed_words is None or wi in observed_words:
                        solver.add(z3.Implies(active, z3.Or(matches)))
                elif interval:
                    window = z3.Select(observed, offsets[pi])
                    solver.add(z3.Implies(active, z3.And(start_table[p * h + choice] <= window,
                                                       window < end_table[p * h + choice])))
                for j in range(0 if interval else length):
                    if representation == "array":
                        glyph = glyph_table[(p * h + choice) * length + j]
                    else:
                        gs = [select([glyphs[pp][kk][j] for kk in range(h)], choice) for pp in range(n)]
                        glyph = select(gs, p)
                    solver.add(z3.Implies(j < chosen_length,
                                         z3.Select(observed, offsets[pi] + j) == glyph))
                choices.append(choice)
                selection_ids = ({plain_alphabet.index(w[pi]) for w in candidates if pi < len(w)}
                                 if dictionary is not None and not max_oov_words else
                                 (set(range(n)) if max_oov_words else {plain_alphabet.index(s) for s in domains.get(index, (pw[pi],))}))
                if cycle_encoding == "state":
                    from .selection import constrain_state
                    constrain_state(solver, p, choice, active, counts, cycle_states, selection_ids, index)
                else:
                    constrain_selection(solver, selection, p, choice, active, counts, cycle_history, selection_ids, h)
                cycle_history.append(p)
                symbols.append(p)
                index += 1
    if oov_flags:
        solver.add(z3.Sum([z3.If(flag, 1, 0) for flag in oov_flags]) <= max_oov_words)
    if candidate_graph is not None:
        for relation in candidate_graph.relations:
            if relation.left not in dictionary_symbols or relation.right not in dictionary_symbols:
                continue  # Empty candidate set already asserted UNSAT.
            a_size, a = dictionary_symbols[relation.left]
            b_size, b = dictionary_symbols[relation.right]
            solver.add(*[a[i] == b[i] for i in range(relation.shared_tokens)])
            if relation.prefix == "left":
                solver.add(a_size < b_size, *[z3.Implies(i < a_size, x == b[i])
                                              for i, x in enumerate(a[:len(b)])])
            elif relation.prefix == "right":
                solver.add(b_size < a_size, *[z3.Implies(i < b_size, x == a[i])
                                              for i, x in enumerate(b[:len(a)])])
    if word_pairs is not None:
        for wi in range(len(ciphertext.words) - 1):
            if wi not in dictionary_symbols or wi + 1 not in dictionary_symbols:
                continue  # Empty candidates already force UNSAT.
            a_size, a_symbols = dictionary_symbols[wi]
            b_size, b_symbols = dictionary_symbols[wi + 1]
            options = []
            for a, b in sorted(word_pairs):
                if a not in candidate_graph.candidates[wi] or b not in candidate_graph.candidates[wi + 1]:
                    continue
                options.append(z3.And(a_size == len(a), b_size == len(b),
                    *[a_symbols[i] == plain_alphabet.index(s) for i, s in enumerate(a)],
                    *[b_symbols[i] == plain_alphabet.index(s) for i, s in enumerate(b)]))
            solver.add(z3.Or(options))
    observed_code_set = None
    if codeword_domains == "observed":
        from .observed_codes import substrings
        observed_code_set = substrings(ciphertext, bounds)
        by_size = {}
        for code in observed_code_set:
            rank = sum(cipher_alphabet.index(g) * c ** (length-j-1) for j, g in enumerate(code))
            by_size.setdefault(len(code), set()).add(rank)
        for p in range(n):
            for k in range(h):
                # Unprotected active slots are all used by the canonicalization
                # below. Protected mappings can retain unvisited alternatives.
                used = (k < counts[p] if plain_alphabet.symbols[p] not in protected else
                        z3.Or([z3.And(symbol == p, choice == k)
                               for symbol, choice in zip(symbols, choices)]))
                solver.add(z3.Implies(used, z3.Or([
                    z3.And(lengths[p][k] == size, z3.Or([starts[p][k] == rank for rank in sorted(ranks)]))
                    for size, ranks in sorted(by_size.items())])))
    # Remove unused alternatives (then relabel canonically). Unobserved letters
    # retain one code, which may be extended to maximum length without changing
    # any observed encoding or breaking prefix-freeness. These preserve existence,
    # not the full set of equivalent unconstrained codebooks.
    for p in range(n):
        if plain_alphabet.symbols[p] in protected:
            continue  # Exact pins may include mappings never used in this text.
        appears = z3.Or([symbol == p for symbol in symbols])
        if interval:
            solver.add(z3.Implies(z3.Not(appears), counts[p] == 0))
        else:
            solver.add(z3.Implies(z3.Not(appears), lengths[p][0] == length))
        for k in range(h):
            used = z3.Or([z3.And(symbol == p, choice == k)
                          for symbol, choice in zip(symbols, choices)])
            solver.add(z3.Implies(z3.And(k < counts[p], z3.Or(appears, k > 0)), used))
    if interval:
        # Disjoint intervals occupy whole maximum-depth leaves. Reserving one
        # remaining leaf per unobserved letter is sufficient to complete its
        # codebook outside SMT, eliminating equivalent unused-code placements.
        reserved = sum(z3.If(counts[p] == 0, 1, 0) for p in range(n))
        solver.add(sum(ends[p][k] - starts[p][k] for p in range(n) for k in range(h))
                   + reserved <= c ** length)
    constraint_count = len(solver.assertions())
    formula_sha256 = None
    if record_formula:
        from hashlib import sha256
        formula_sha256 = sha256("\n".join(a.sexpr() for a in solver.assertions()).encode()).hexdigest()
    objective_expression = None
    if language_objective is not None and all(candidate_graph.candidates):
        from .language_objective import expression
        objective_expression = expression(language_objective, dictionary_symbols,
                                          candidate_graph.candidates, plain_alphabet)
    construction_seconds = perf_counter() - start
    check_start = perf_counter()
    outcome = solver.check(*pin_guards.values())
    best_model = solver.model() if outcome == z3.sat else None
    objective_trace = []
    objective_optimal = False
    if language_objective is not None:
        objective_trace.append({"status": str(outcome).upper(),
                                "runtime_seconds": perf_counter() - check_start})
        if outcome == z3.sat and objective_expression is not None:
            best_score = best_model.eval(objective_expression).as_long()
            objective_trace[-1]["score"] = best_score
            for _ in range(language_objective["max_checks"] - 1):
                remaining = timeout_ms - int((perf_counter() - check_start) * 1000 + 0.999)
                if remaining <= 0:
                    break
                solver.add(objective_expression > best_score)
                solver.set(timeout=remaining)
                step_start = perf_counter()
                improved = solver.check()
                step = {"status": str(improved).upper(),
                        "runtime_seconds": perf_counter() - step_start}
                objective_trace.append(step)
                if improved == z3.sat:
                    best_model = solver.model()
                    best_score = best_model.eval(objective_expression).as_long()
                    step["score"] = best_score
                elif improved == z3.unsat:
                    objective_optimal = True
                    break
                else:
                    step["reason_unknown"] = solver.reason_unknown()
                    break
            # A verified feasible incumbent remains SAT after an unresolved improvement search.
    result = Recovery(str(outcome).upper(), perf_counter() - check_start,
                      statistics={key: solver.statistics().get_key_value(key)
                                  for key in solver.statistics().keys()},
                      capacity={"symbolic_variables": len(variables),
                                "constraints": constraint_count,
                                "codebook_slots": n * h,
                                "representation": representation,
                                "solver_backend": solver_backend,
                                "selection": asdict(selection),
                                "cycle_encoding": cycle_encoding,
                                "selection_counters": n if selection.mode == "cycle" else 0,
                                "pruned_dictionary_candidates": candidate_graph.pruned_candidates if candidate_graph else 0,
                                "prefix_relations": len(candidate_graph.relations) if candidate_graph else 0,
                                "construction_seconds": construction_seconds})
    if language_objective is not None:
        result.capacity["language_objective"] = {
            "checks": objective_trace, "optimality_proven": objective_optimal,
            "score": best_score if best_model is not None and objective_expression is not None else None,
            "scope": "Integer training score; shared-key constraints retained; feasible incumbent returned even when improvement is UNKNOWN."}
    if formula_sha256 is not None:
        result.capacity["formula_sha256"] = formula_sha256
    result.capacity["codeword_domains"] = codeword_domains
    if observed_code_set is not None:
        result.capacity["observed_codeword_count"] = len(observed_code_set)
        result.capacity["observed_codewords_by_length"] = {
            size: sum(len(code) == size for code in observed_code_set)
            for size in range(bounds.min_code_length, length+1)}
    if dictionary is not None:
        result.capacity["dictionary_encoding"] = dictionary_encoding
        result.capacity["max_oov_words"] = max_oov_words
    if known_word_lengths is not None:
        result.capacity["oracle_word_lengths"] = True
    if known_segmentation is not None:
        result.capacity["oracle_segmentation"] = True
    if key_exclusions:
        result.capacity.update(key_exclusion_count=len(key_exclusions),
                               protected_key_owners=sorted(excluded_owners))
    if guidance:
        result.capacity.update(pinned_symbols=sorted(pinned),
                               pin_rotations_allowed=guidance["rotate"], initial_value_hints=hint_count,
                               core_minimization_requested=guidance["minimize_core"],
                               forced_cycle_conflicts=forced_conflicts,
                               fixed_word_conflicts=word_conflicts,
                               guidance_scope="key restrictions; UNSAT excludes only the pinned submodel")
    if observed_words is not None:
        result.capacity.update(observed_word_indices=sorted(observed_words),
                               verification_scope="selected glyph observations; all word lengths and cycle context retained")
    if outcome == z3.unknown:
        result.reason_unknown = solver.reason_unknown()
        return result
    if outcome == z3.unsat:
        if pinned:
            core = set(map(str, solver.unsat_core()))
            result.capacity["pinned_unsat_core"] = sorted(
                s for s, guard in pin_guards.items() if str(guard) in core)
        return result
    model = best_model

    def value(expression):
        return model.eval(expression, model_completion=True).as_long()

    def extract_code(p, k):
        size = value(lengths[p][k])
        if interval:
            lo = value(starts[p][k])
            return tuple(cipher_alphabet.symbols[(lo // c ** (length - j - 1)) % c]
                         for j in range(size))
        return tuple(cipher_alphabet.symbols[value(g)] for g in glyphs[p][k][:size])

    codebook = {s: tuple(
        extract_code(p, k)
        for k in range(value(counts[p]))) for p, s in enumerate(plain_alphabet.symbols)}
    if interval:
        occupied = sorted((value(starts[p][k]), value(ends[p][k]))
                          for p in range(n) for k in range(value(counts[p])))
        cursor, interval_index, completed_letters = 0, 0, 0
        for symbol, codes in codebook.items():
            if codes:
                continue
            while interval_index < len(occupied):
                lo, hi = occupied[interval_index]
                if cursor < lo:
                    break
                cursor = max(cursor, hi)
                interval_index += 1
            if cursor >= c ** length:
                raise RuntimeError("Reserved prefix-tree capacity was insufficient")
            codebook[symbol] = (tuple(cipher_alphabet.symbols[(cursor // c ** (length - j - 1)) % c]
                                     for j in range(length)),)
            completed_letters += 1
            cursor += 1
        result.capacity["completed_unobserved_letters"] = completed_letters
    result.encoder = Encoder(codebook)
    recovered_words, recovered_choices, segmentation = [], [], []
    base = 0
    for offsets, size in zip(positions, word_sizes):
        count = value(size)
        recovered_words.append(tuple(plain_alphabet.symbols[value(s)] for s in symbols[base:base + count]))
        recovered_choices.extend(value(choice) for choice in choices[base:base + count])
        segmentation.append(tuple(value(offset) for offset in offsets[:count + 1]))
        base += len(offsets) - 1
    result.plaintext = Text(tuple(recovered_words))
    result.choices = tuple(recovered_choices)
    result.segmentation = tuple(segmentation)
    legal_codes = all(
        1 <= len(codes) <= bounds.max_homophones
        and all(bounds.min_code_length <= len(code) <= bounds.max_code_length
                and all(g in cipher_alphabet.symbols for g in code) for code in codes)
        for codes in result.encoder.codebook.values())
    if dictionary is None:
        observed_plaintext = [s for w in plaintext.words for s in w]
        recovered_plaintext = [s for w in result.plaintext.words for s in w]
        legal_language = (tuple(map(len, result.plaintext.words)) == tuple(map(len, plaintext.words))
                          and all(s in domains.get(i, (original,)) for i, (s, original)
                                  in enumerate(zip(recovered_plaintext, observed_plaintext))))
    else:
        legal_language = (sum(w not in dictionary.words for w in result.plaintext.words) <= max_oov_words
                          and all(min_word_length <= len(w) <= max_word_length
                                  for w in result.plaintext.words))
    if word_pairs is not None:
        legal_language = legal_language and all(
            (a, b) in word_pairs for a, b in zip(result.plaintext.words, result.plaintext.words[1:]))
    expected_offsets, choice_index = [], 0
    for word in result.plaintext.words:
        offsets = [0]
        for symbol in word:
            code = result.encoder.codebook[symbol][result.choices[choice_index]]
            offsets.append(offsets[-1] + len(code))
            choice_index += 1
        expected_offsets.append(tuple(offsets))
    generated = result.encoder.encode(result.plaintext, result.choices)
    matches_observations = (generated == ciphertext if observed_words is None else
                            tuple(map(len, generated.words)) == tuple(map(len, ciphertext.words))
                            and all(generated.words[i] == ciphertext.words[i] for i in observed_words))
    result.verified = (matches_observations
                       and result.encoder.decode(generated) == result.plaintext
                       and legal_codes and legal_language
                       and selection_accepts(result.plaintext, result.encoder, result.choices, selection)
                       and result.segmentation == tuple(expected_offsets))
    if observed_code_set is not None:
        used_codes = [result.encoder.codebook[s][choice] for s, choice in zip(
            (s for word in result.plaintext.words for s in word), result.choices)]
        if any(code not in observed_code_set for code in used_codes):
            raise RuntimeError("SAT explanation violated an observed substring domain")
    if not result.verified:
        raise RuntimeError("SAT explanation failed independent Python verification")
    if known_word_lengths is not None and tuple(map(len, result.plaintext.words)) != known_word_lengths:
        raise RuntimeError("SAT explanation violated the supplied word lengths")
    if known_segmentation is not None and result.segmentation != known_segmentation:
        raise RuntimeError("SAT explanation violated the supplied boundaries")
    if guidance:
        for symbol in pinned:
            original = guidance["encoder"].codebook[symbol]
            rotations = range(len(original)) if guidance["rotate"] else (0,)
            if not any(result.encoder.codebook[symbol] == original[r:] + original[:r] for r in rotations):
                raise RuntimeError("SAT explanation violated a pinned mapping")
    codes = [code for alternatives in result.encoder.codebook.values() for code in alternatives]
    result.capacity.update(mappings=len(codes), additional_homophones=len(codes) - n,
                           total_codebook_glyphs=sum(map(len, codes)),
                           code_lengths=[len(code) for code in codes],
                           null_symbols=0, context_rules=0, exceptions=0)
    from voynich_smt.metrics.complexity import measurements, weighted_score
    result.complexity = {"raw": measurements(result.encoder),
                         "weighted_score": weighted_score(measurements(result.encoder), Optimization().weights)}
    result.optimization = {"enabled": False, "optimality_proven": False}
    return result

