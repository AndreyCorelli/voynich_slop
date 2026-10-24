from dataclasses import replace
from itertools import permutations, product
import pytest
from voynich_smt.cipher.base import Bounds, Encoder
from voynich_smt.cipher.selection import choose
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.language.dictionary import WordDictionary
from voynich_smt.models.alphabet import Alphabet
from voynich_smt.models.settings import HomophoneSelection
from voynich_smt.models.text import Text
from voynich_smt.solver.learning import learn, recover_learned, validate_rules, violates


def request(text, words=('a', 'b')):
    return HiddenRecoveryRequest(Text.from_string(text), Alphabet(tuple('ab')), Alphabet(tuple('xyz')),
        Bounds('verbose', 2, 1, 1), WordDictionary.from_strings(words),
        selection=HomophoneSelection('cycle', 'text'))


def test_cycle_certificate_is_label_independent_and_rejects_tampering():
    context = request('x x y')
    rule = {'kind': 'cycle_pair', 'codes': [['x'], ['y']]}
    validate_rules(context, [rule])
    for text in ('x y x', 'x y'):
        with pytest.raises(ValueError): validate_rules(request(text), [rule])
    with pytest.raises(ValueError):
        validate_rules(replace(context, selection=HomophoneSelection('cycle', 'word')), [rule])
    suffix = replace(context, ciphertext=Text.from_string('y'))
    result = recover_learned(suffix, context, 2, [rule])
    assert result.verified and not violates(result.encoder, rule)


def test_word_certificate_checks_coverage_language_and_unused_owners():
    context = request('x y', ('a',))
    rule = {'kind': 'word', 'word_index': 0, 'segments': [{'symbol': 'b', 'code': ['x']}]}
    validate_rules(context, [rule])
    result = recover_learned(replace(context, ciphertext=Text.from_string('y')), context, 1, [rule])
    assert result.verified and ('x',) not in result.encoder.codebook['b']
    assert result.capacity['protected_key_owners'] == ['b']
    for bad in (dict(rule, word_index=1), dict(rule, segments=[{'symbol': 'a', 'code': ['x']}])):
        with pytest.raises(ValueError): validate_rules(context, [bad])
    with pytest.raises(ValueError): recover_learned(request('z', ('a',)), context, 1, [rule])


def test_analytic_rules_preserve_all_full_keys_by_exhaustive_oracle():
    context = request('x x y')
    seed = Encoder({'a': (('x',), ('y',)), 'b': (('z',),)})
    rules = learn(context, seed)
    assert rules
    for order in permutations('xyz'):
        for na, nb in ((1, 1), (1, 2), (2, 1)):
            key = Encoder({'a': tuple((g,) for g in order[:na]),
                           'b': tuple((g,) for g in order[na:na+nb])})
            for symbols in product('ab', repeat=3):
                plain = Text(tuple((s,) for s in symbols))
                if key.encode(plain, choose(plain, key, context.selection)) == context.ciphertext:
                    assert not any(violates(key, rule) for rule in rules)


def test_unknown_never_creates_candidate_exclusion(tmp_path, monkeypatch):
    import benchmarks.learned_search as runner
    from voynich_smt.solver.recovery import Recovery
    monkeypatch.setattr(runner, 'recover_learned', lambda *args: Recovery('UNKNOWN', 0, 'test timeout'))
    report = runner.run({'source_report': 'experiments/results/l3-conflict.json', 'timeout_ms': 1,
                         'dictionary_encoding': 'trie', 'candidate_count': 2},
                        tmp_path / 'report.json', tmp_path / 'artifacts')
    assert report['outcome']['status'] == 'UNKNOWN'
    assert len(report['experiments']) == 1
    assert len(report['learned_rules']) == 3


def test_core_is_reproved_and_unknown_or_sat_certificates_are_rejected(monkeypatch):
    from dataclasses import asdict
    import voynich_smt.solver.guided as guided
    from voynich_smt.solver.recovery import Recovery
    key = Encoder({'a': (('x',), ('y',)), 'b': (('z',),)})
    rule = {'kind': 'pin_core', 'mappings': {'a': [['x'], ['y']]}, 'proof_encoder': asdict(key)}
    context = request('x x y')
    validate_rules(context, [rule])
    result = recover_learned(replace(context, ciphertext=Text.from_string('y')), context, 2, [rule])
    assert result.verified and not violates(result.encoder, rule)
    with pytest.raises(ValueError): validate_rules(request('x y x'), [rule])
    monkeypatch.setattr(guided, 'recover_guided', lambda *a, **k: Recovery('UNKNOWN', 0, 'timeout'))
    with pytest.raises(ValueError): validate_rules(context, [rule])


def test_full_prefix_learned_solve_leaves_every_mapping_free():
    context = request('x x y')
    seed = Encoder({'a': (('x',), ('y',)), 'b': (('z',),)})
    rules = learn(context, seed)
    result = recover_learned(context, context, 0, rules)
    assert result.status == 'SAT' and result.verified
    assert result.plaintext != Text.from_string('a a a')
    assert not result.capacity.get('pinned_symbols')
    assert not any(violates(result.encoder, rule) for rule in rules)


def test_full_prefix_timeout_is_reported_as_unresolved(tmp_path, monkeypatch):
    import benchmarks.learned_prefix as runner
    from voynich_smt.solver.recovery import Recovery
    captured = []
    def timeout(request, context, start, rules):
        captured.append((request, context, start, rules))
        return Recovery('UNKNOWN', 0, 'test timeout')
    monkeypatch.setattr(runner, 'recover_learned', timeout)
    report = runner.run({'source_report': 'experiments/results/learned-search.json', 'timeout_ms': 120000,
                         'dictionary_encoding': 'trie'}, tmp_path / 'report.json', tmp_path / 'artifacts')
    req, context, start, rules = captured[0]
    assert start == 0 and req.ciphertext == context.ciphertext and len(req.ciphertext.words) == 23
    assert req.timeout_ms == 120000 and len(rules) == 19
    assert report['complete'] and report['outcome']['status'] == 'UNKNOWN'
    assert 'unresolved' in report['outcome']['interpretation']
