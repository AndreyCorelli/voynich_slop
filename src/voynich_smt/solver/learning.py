"""Portable analytic exclusions proved against a larger public ciphertext."""
from voynich_smt.cipher.base import Encoder
from voynich_smt.models.text import Text
from .key_evidence import forced_cycle_conflicts
from .recovery import _recover, score_result


def violates(encoder, rule):
    if rule['kind'] == 'cycle_pair':
        pair = {tuple(c) for c in rule['codes']}
        return any(len(cs) == 2 and set(cs) == pair for cs in encoder.codebook.values())
    if rule['kind'] == 'pin_core':
        for symbol, codes in rule['mappings'].items():
            expected = tuple(tuple(c) for c in codes)
            actual = encoder.codebook[symbol]
            if not any(actual == expected[r:] + expected[:r] for r in range(len(expected))):
                return False
        return True
    return all(tuple(s['code']) in encoder.codebook[s['symbol']] for s in rule['segments'])


def validate_rules(context, rules):
    if (context.representation != 'finite' or context.nulls.enabled or context.optimization.enabled
            or context.bounds.max_homophones != 2 or context.selection.mode != 'cycle'
            or context.selection.reset != 'text'):
        raise ValueError('Learning requires finite, null-free H2 text-wide cycles')
    maximum = context.max_word_length or max(map(len, context.dictionary.words))
    for rule in rules:
        kind = rule.get('kind')
        if kind == 'cycle_pair' and set(rule) == {'kind', 'codes'}:
            codes = tuple(tuple(c) for c in rule['codes'])
            if len(codes) != 2:
                raise ValueError('A cycle pair must contain two codes')
            encoder = Encoder({'_': codes})
            if not forced_cycle_conflicts(context.ciphertext, encoder, ('_',)):
                raise ValueError('Cycle pair has no forced-cycle proof')
        elif kind == 'word' and set(rule) == {'kind', 'word_index', 'segments'}:
            wi = rule['word_index']
            if type(wi) is not int or not 0 <= wi < len(context.ciphertext.words):
                raise ValueError('Invalid word certificate index')
            segments = rule['segments']
            if not segments or any(set(s) != {'symbol', 'code'} for s in segments):
                raise ValueError('Invalid word certificate segments')
            book = {}
            for segment in segments:
                symbol, code = segment['symbol'], tuple(segment['code'])
                if symbol not in context.plaintext_alphabet.symbols:
                    raise ValueError('Invalid certificate owner')
                book.setdefault(symbol, [])
                if code not in book[symbol]:
                    book[symbol].append(code)
            codes = tuple(c for cs in book.values() for c in cs)
            Encoder({s: tuple(cs) for s, cs in book.items()})
            if any(len(cs) > 2 for cs in book.values()):
                raise ValueError('Certificate exceeds H2')
            word = tuple(s['symbol'] for s in segments)
            if tuple(g for s in segments for g in s['code']) != context.ciphertext.words[wi]:
                raise ValueError('Certificate does not cover the ciphertext word')
            if word in context.dictionary.words and context.min_word_length <= len(word) <= maximum:
                raise ValueError('Certificate word is legal')
        elif kind == 'pin_core' and set(rule) == {'kind', 'mappings', 'proof_encoder'}:
            from .guided import recover_guided
            if (set(rule['proof_encoder']) != {'codebook', 'null_symbols'}
                    or rule['proof_encoder']['null_symbols']):
                raise ValueError('Core proof must contain a null-free encoder')
            encoder = Encoder({s: tuple(tuple(c) for c in cs)
                               for s, cs in rule['proof_encoder']['codebook'].items()})
            if not rule['mappings'] or any(s not in encoder.codebook or
                    tuple(tuple(c) for c in cs) != encoder.codebook[s]
                    for s, cs in rule['mappings'].items()):
                raise ValueError('Core does not match proof encoder')
            proof = recover_guided(context, encoder, tuple(rule['mappings']), rotate=True)
            if proof.status != 'UNSAT':
                raise ValueError('Core exclusion lacks an independently replayed UNSAT proof')
            codes = tuple(c for cs in encoder.codebook.values() for c in cs)
        else:
            raise ValueError('Unsupported or malformed exclusion')
        if any(not context.bounds.min_code_length <= len(c) <= context.bounds.max_code_length
               or any(g not in context.ciphertext_alphabet.symbols for g in c) for c in codes):
            raise ValueError('Certificate code violates bounds')


def learn(context, encoder):
    rules = []
    for conflict in forced_cycle_conflicts(context.ciphertext, encoder, encoder.codebook):
        rules.append({'kind': 'cycle_pair', 'codes': [list(c) for c in encoder.codebook[conflict['symbol']]]})
    lookup = {c: s for s, cs in encoder.codebook.items() for c in cs}
    maximum = context.max_word_length or max(map(len, context.dictionary.words))
    for wi, word in enumerate(context.ciphertext.words):
        try:
            decoded = encoder.decode(Text((word,))).words[0]
        except ValueError:
            continue
        if decoded in context.dictionary.words and context.min_word_length <= len(decoded) <= maximum:
            continue
        pending, segments = (), []
        for glyph in word:
            pending += (glyph,)
            if pending in lookup:
                segments.append({'symbol': lookup[pending], 'code': list(pending)})
                pending = ()
        rules.append({'kind': 'word', 'word_index': wi, 'segments': segments})
    validate_rules(context, rules)
    return rules


def recover_learned(request, context, sample_start, rules):
    validate_rules(context, rules)
    fields = ('bounds', 'dictionary', 'plaintext_alphabet', 'ciphertext_alphabet', 'selection',
              'min_word_length', 'max_word_length', 'nulls', 'optimization', 'representation')
    if (type(sample_start) is not int or sample_start < 0
            or any(getattr(request, f) != getattr(context, f) for f in fields)
            or request.ciphertext.words != context.ciphertext.words[sample_start:sample_start + len(request.ciphertext.words)]):
        raise ValueError('Sample must be a contiguous slice of the same scientific model')
    result = _recover(None, request.ciphertext, request.plaintext_alphabet,
        request.ciphertext_alphabet, request.bounds, request.timeout_ms,
        dictionary=request.dictionary, min_word_length=request.min_word_length,
        max_word_length=request.max_word_length or max(map(len, request.dictionary.words)),
        selection=request.selection, dictionary_encoding=request.dictionary_encoding,
        key_exclusions=rules)
    if result.status == 'SAT' and any(violates(result.encoder, rule) for rule in rules):
        raise RuntimeError('SAT key violated an independently checked exclusion')
    return score_result(result, request.optimization)
