"""Truth-free enumeration of public vocabulary word-length branches."""
from heapq import heappop, heappush
from math import prod
from collections import Counter
from itertools import zip_longest
from .segmented import recover_with_word_lengths


def ordered_vectors(domains):
    """Enumerate the full Cartesian product by total length, then lexicographically."""
    if not domains or any(not domain for domain in domains):
        return
    domains = tuple(tuple(sorted(set(domain))) for domain in domains)
    initial = (0,) * len(domains)
    first = tuple(domain[0] for domain in domains)
    queue, seen = [(sum(first), first, initial)], {initial}
    while queue:
        _, vector, indices = heappop(queue)
        yield vector
        for i, index in enumerate(indices):
            if index + 1 == len(domains[i]):
                continue
            adjacent = indices[:i] + (index+1,) + indices[i+1:]
            if adjacent in seen:
                continue
            seen.add(adjacent)
            changed = vector[:i] + (domains[i][index+1],) + vector[i+1:]
            heappush(queue, (sum(changed), changed, adjacent))


def balanced_vectors(domains):
    """Interleave a diagonal rank sweep with complete shortest-first enumeration."""
    if not domains or any(not d for d in domains):
        return
    domains = tuple(tuple(sorted(set(d))) for d in domains)
    diagonal = (tuple(d[min(rank, len(d)-1)] for d in domains)
                for rank in range(max(map(len, domains))))
    seen = set()
    for pair in zip_longest(diagonal, ordered_vectors(domains)):
        for vector in pair:
            if vector is not None and vector not in seen:
                seen.add(vector)
                yield vector


def ranked_vectors(domains):
    """Complete product ordered by sum of per-word preference ranks."""
    if not domains or any(not d for d in domains):
        return
    initial = (0,) * len(domains)
    vector = tuple(d[0] for d in domains)
    queue, seen = [(0, vector, initial)], {initial}
    while queue:
        _, vector, indices = heappop(queue)
        yield vector
        for i, index in enumerate(indices):
            if index+1 == len(domains[i]):
                continue
            adjacent = indices[:i] + (index+1,) + indices[i+1:]
            if adjacent in seen:
                continue
            seen.add(adjacent)
            changed = vector[:i] + (domains[i][index+1],) + vector[i+1:]
            heappush(queue, (sum(adjacent), changed, adjacent))


def public_domains(request):
    if request.representation != 'finite' or request.nulls.enabled or request.optimization.enabled:
        raise ValueError('Length search requires finite null-free feasibility')
    maximum = request.max_word_length or max(map(len, request.dictionary.words))
    graph = request.dictionary.candidate_graph(request.ciphertext, request.bounds,
                                                request.min_word_length, maximum)
    return tuple(tuple(sorted({len(word) for word in candidates})) for candidates in graph.candidates), graph


def admissible_vectors(domains, graph, ordering="shortest_first"):
    if ordering == "shortest_first":
        vectors = ordered_vectors(domains)
    elif ordering == "balanced":
        vectors = balanced_vectors(domains)
    elif ordering == "candidate_rich":
        counts = tuple(Counter(map(len, words)) for words in graph.candidates)
        ranked = tuple(tuple(sorted(d, key=lambda n: (-counts[i][n], n))) for i, d in enumerate(domains))
        vectors = ranked_vectors(ranked)
    else:
        raise ValueError("Unknown length ordering")
    for vector in vectors:
        if any((r.prefix == 'equal' and vector[r.left] != vector[r.right])
               or (r.prefix == 'left' and vector[r.left] >= vector[r.right])
               or (r.prefix == 'right' and vector[r.left] <= vector[r.right]) for r in graph.relations):
            continue
        yield vector


def search(request, max_branches=12, on_branch=None, *, ordering="shortest_first"):
    """SAT is a full witness; UNSAT requires exhaustive proved branch rejection."""
    if type(max_branches) is not int or max_branches <= 0:
        raise ValueError('Branch limit must be a positive integer')
    if ordering not in {'shortest_first','balanced','candidate_rich'}:
        raise ValueError('Unknown length ordering')
    domains, graph = public_domains(request)
    report = {'ordering': ordering, 'domains': domains,
              'length_candidate_counts': tuple(dict(Counter(map(len, words))) for words in graph.candidates), 'cartesian_combinations': prod(map(len, domains)),
              'attempts': [], 'exhausted': False, 'status': 'UNKNOWN', 'verified': False}
    vectors = admissible_vectors(domains, graph, ordering)
    for index in range(max_branches):
        vector = next(vectors, None)
        if vector is None:
            report['exhausted'] = True
            break
        result = recover_with_word_lengths(request, vector)
        result.capacity.pop("oracle_word_lengths", None)
        result.capacity.update(fixed_word_lengths=list(vector), word_length_source="public_search")
        if result.status == 'SAT' and not result.verified:
            raise RuntimeError('Length search returned an unverified SAT fit')
        report['attempts'].append({'word_lengths': vector, 'result': result})
        if on_branch is not None: on_branch(index, vector, result)
        if result.status == 'SAT':
            report.update(status='SAT', verified=True)
            return report
    else:
        report['exhausted'] = next(vectors, None) is None
    if report['exhausted'] and all(a['result'].status == 'UNSAT' for a in report['attempts']):
        report['status'] = 'UNSAT'
    return report
