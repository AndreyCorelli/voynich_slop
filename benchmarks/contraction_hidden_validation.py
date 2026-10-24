"""Independent path/cost and saved-witness validation; no additional solves."""
from collections import Counter
import json
from pathlib import Path

from benchmarks import contraction_hidden_calibration as base
from benchmarks.broader_contraction_capacity import minimum
from benchmarks.contraction_hidden_calibration_run import oracle_case
from benchmarks.l3_conflict import verify
from voynich_smt.cipher.base import Encoder
from voynich_smt.data.corpus import digest, write_json
from voynich_smt.experiments.hidden import HiddenRecoveryRequest


def normalized(value):
    return json.loads(json.dumps(value))


def independent_paths(word, rules):
    """Forward exhaustive scan; does not call benchmark applicability or recursion."""
    table = {i: set() for i in range(len(word)+1)}
    table[0].add(())
    for i in range(len(word)):
        edges = [(i+1, (word[i],))]
        for r in rules:
            suffix = r['expansion']; end = i+len(suffix)
            if word[i:end] != suffix: continue
            if r['position'] in ('initial','whole') and i != 0: continue
            if r['position'] in ('final','whole') and end != len(word): continue
            if r.get('left') and (i == 0 or word[i-1] != r['left']): continue
            labels = tuple(f"<{r['id']}-part-{j}>" for j in range(r['units']))
            edges.append((end, labels))
        for end, labels in edges:
            table[end].update(prefix+labels for prefix in table[i])
    return table[len(word)]


def independent_decode(word, encoder):
    lookup = {tuple(c): s for s, cs in encoder['codebook'].items() for c in cs}
    output = []; start = 0
    while start < len(word):
        matches = [(end, lookup[tuple(word[start:end])]) for end in range(start+1,len(word)+1)
                   if tuple(word[start:end]) in lookup]
        if not matches: return None
        assert len(matches) == 1
        start, symbol = matches[0]; output.append(symbol)
    return output


def validate():
    p = base.prepare()
    config = json.loads(base.CONFIG.read_text()); source = json.loads(base.SOURCE.read_text())
    assert digest(config) == p['inventory_sha256'] and digest(source) == p['source_sha256']
    report = json.loads((base.OUT/'report.json').read_text())
    assert report['complete'] and report['prepared_sha256'] == digest(p)
    adapter = json.loads((base.OUT/'oracle-adapter.json').read_text())
    assert adapter['code_sha256'] == digest(Path('benchmarks/contraction_hidden_calibration_run.py').read_text())
    checks = 0; cases_checked = 0; prediction_words = 0; sat = 0; unresolved = 0; summaries = []; corrected_evaluations = []
    for name, f in p['fixtures'].items():
        assert normalized(base.natural_fixture(source['sources'][name], p['rules'], f['seed'])) == f
        for word in set(f['vocabulary']+f['held']):
            independent = independent_paths(word, p['rules'])
            actual = set(base.variants(word, p['rules']))
            assert actual == independent
            assert min(map(len,actual)) == minimum(word, p['rules'])[0]
            checks += len(actual)
    stages = {}
    for i in range(1,8):
        stage = json.loads((base.OUT/f'iteration-{i}.json').read_text()); stages[i] = stage
        assert stage['plan']['prepared_sha256'] == digest(p)
        if i > 1: assert stage['plan']['previous_sha256'] == digest(stages[i-1])
        for label, case in stage['cases'].items():
            reconstructed = base.make_case(p, case['source'], case['h'], case['mixed'], case['contracted'], i==5)
            assert normalized(reconstructed) == case
            cases_checked += 1
            q = HiddenRecoveryRequest.from_dict(case['request']); verify(q, case['truth'])
            seen = set()
            cursor = 0; truth_book = case['truth']['encoder']['codebook']
            for word in case['truth']['plaintext']['words']:
                for unit in word:
                    seen.add(tuple(truth_book[unit][case['truth']['choices'][cursor]])); cursor += 1
            for row in [r for r in stage['rows'] if r['name'].startswith(label+'-')]:
                effective = oracle_case(case) if row['oracle'] else case
                assert row['case_sha256'] == digest(effective)
                public_path = base.OUT/f'iteration-{i}'/f"{row['name']}-input.json"
                public = json.loads(public_path.read_text())
                assert set(public) == ({'request','oracle_segmentation'} if row['oracle'] else {'request'})
                assert public['request'] == case['control_request' if row['control'] else 'request']
                assert digest(public) == row['public_sha256']
                q = HiddenRecoveryRequest.from_dict(public['request']); verify(q,row['result'])
                if row['result']['status'] == 'SAT':
                    sat += 1
                    if row['oracle']:
                        assert row['result']['segmentation'] == public['oracle_segmentation']
                    expected = base.prediction(case,row['result'],p,row['control'])
                    expected = normalized(expected)
                    # Frozen runner compared lists to in-memory tuples for novelty.
                    # Preserve raw output, correct only this metadata independently.
                    for a,b in zip(expected['words'], row['prediction']['words']):
                        assert {k:v for k,v in a.items() if k!='novel_ciphertext'} == {k:v for k,v in b.items() if k!='novel_ciphertext'}
                    assert {k:v for k,v in expected.items() if k not in ('words','novel_words','novel_exact')} == {k:v for k,v in row['prediction'].items() if k not in ('words','novel_words','novel_exact')}
                    for cipher, word_score in zip(case['control_held_cipher' if row['control'] else 'held_cipher']['words'], expected['words']):
                        assert word_score['novel_ciphertext'] == (tuple(cipher) not in {tuple(w) for w in public['request']['ciphertext']['words']})
                    corrected_evaluations.append({'iteration':i,'name':row['name'],'prediction':expected})
                    field = 'control_held_cipher' if row['control'] else 'held_cipher'
                    for j,(cipher, saved) in enumerate(zip(case[field]['words'],row['prediction']['words'])):
                        decoded = independent_decode(cipher, row['result']['encoder'])
                        assert (decoded is not None) == saved['fully_decoded']
                        if decoded is not None:
                            spelling = ''.join(p['expansions'].get(u,u) for u in decoded)
                            assert spelling == saved['expanded_word']
                            if not row['control']: assert saved['exact'] == (spelling == case['held_plaintext'][j])
                        prediction_words += 1
                elif row['result']['status'] in ('UNKNOWN','WALL_TIMEOUT'):
                    unresolved += 1
        if i > 1:
            positives = [r for r in stage['rows'] if not r['control']]
            for row in positives:
                label = 'contracted' if row['name'].startswith('contracted') else 'letters'
                case = stage['cases'][label]
                pred = next((x['prediction'] for x in corrected_evaluations if x['iteration']==i and x['name']==row['name']), row['prediction']); words = pred.get('words',[])
                covered_exact = sum(w.get('exact',False) and w.get('generating_codes_seen',False) for w in words)
                summaries.append({'iteration': i, 'source': case['source'], 'arm': label,
                    'oracle': row['oracle'], 'h': case['h'], 'mixed': case['mixed'],
                    'status': row['result']['status'], 'exact': pred.get('exact'), 'novel_exact': pred.get('novel_exact'),
                    'generating_covered_words': sum(case['generating_covered_mask']),
                    'exact_among_covered': covered_exact if words else None,
                    'dictionary_excluded_words': sum(not x for x in case['held_dictionary_mask']),
                    'unit_saving': 1-case['training_units']/case['training_letters'],
                    'training_glyph_mean': case['training_glyphs']/32,
                    'fit_wall_seconds': row['fit_wall_seconds'],
                    'solver_seconds': row['result'].get('runtime_seconds')})
    assert report['solver_calls'] == sum(len(stage['rows']) for stage in stages.values()) == 17
    validation = {'verified': True, 'complete_path_checks': checks, 'cases_regenerated': cases_checked,
        'sat_witnesses': sat, 'unresolved': unresolved, 'independent_holdout_words_checked': prediction_words,
        'code_sha256': digest(Path(__file__).read_text()),
        'scope': 'Complete independent path enumeration and retained-cost comparison; all fixture/protocol hashes, regenerations, public input separation, SAT re-encoding, oracle offsets and independent heldout decoding. UNSAT statuses remain solver reports without independent proof certificates.'}
    write_json(base.OUT/'evaluations-corrected.json', {'rows':corrected_evaluations,
        'reason':'Normalize list/tuple representation before testing seen ciphertext words; original outputs retained. Exact words unchanged, corrected novelty cannot alter selected H2 replication family.'})
    for index in (2,3):
        ev=next(x['prediction'] for x in corrected_evaluations if x['iteration']==index and x['name']=='contracted-positive')
        assert ev['exact']>=6 and ev['novel_exact']>=4
    write_json(base.OUT/'validation.json', validation)
    write_json(base.OUT/'summary.json', {'prepared_sha256': digest(p), 'rows': summaries,
        'decision': 'Mixed-width hidden contraction gate remains unresolved; one-glyph H2 usefulness did not replicate across sources. Coverage and whole-word sign ambiguity require calibration before manuscript search. No larger inventory or timeout escalation justified.'})
    print(json.dumps(validation))
    return validation


if __name__ == '__main__': validate()
