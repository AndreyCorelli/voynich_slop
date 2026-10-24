"""Equivalent dictionary formulas, with shared-prefix factoring for large vocabularies."""
import z3


def membership(candidates, symbols, size, alphabet, encoding="flat", entry_id=None):
    sentinel = len(alphabet.symbols)
    if encoding == "flat":
        size_atoms = {}
        slot_atoms = [{} for _ in symbols]
        token_indices = {}
        alternatives = []
        for word in candidates:
            length = len(word)
            if length not in size_atoms:
                size_atoms[length] = size == length
            terms = []
            for i, symbol in enumerate(symbols):
                value = sentinel
                if i < length:
                    token = word[i]
                    if token not in token_indices:
                        token_indices[token] = alphabet.index(token)
                    value = token_indices[token]
                if value not in slot_atoms[i]:
                    slot_atoms[i][value] = symbol == value
                terms.append(slot_atoms[i][value])
            alternatives.append(z3.And(size_atoms[length], *terms))
        return z3.Or(alternatives)
    if encoding == "entry":
        if entry_id is None:
            raise ValueError("Entry encoding requires a bounded word selector")
        if not candidates:
            return z3.BoolVal(False)
        def lookup(values, lo=0):
            if all(v == values[0] for v in values):
                return z3.IntVal(values[0])
            middle = len(values) // 2
            return z3.If(entry_id < lo + middle,
                         lookup(values[:middle], lo), lookup(values[middle:], lo + middle))
        return z3.And(entry_id >= 0, entry_id < len(candidates),
            size == lookup(tuple(map(len, candidates))), *[
                symbol == lookup(tuple(alphabet.index(word[i]) if i < len(word) else sentinel
                                       for word in candidates))
                for i, symbol in enumerate(symbols)])
    if encoding != "trie":
        raise ValueError("Unknown dictionary encoding")
    root = {}
    for word in candidates:
        node = root
        for token in word:
            node = node.setdefault(alphabet.index(token), {})
        node[None] = True

    def branch(node, depth):
        options = [size == depth] if None in node else []
        options.extend(z3.And(symbols[depth] == token, branch(child, depth + 1))
                       for token, child in node.items() if token is not None)
        return z3.Or(options)

    padding = [z3.If(i < size, z3.And(symbol >= 0, symbol < sentinel), symbol == sentinel)
               for i, symbol in enumerate(symbols)]
    return z3.And(branch(root, 0), *padding)
