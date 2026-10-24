"""Full cached EVA width compatibility audit; arithmetic only, no solver."""
from collections import Counter, deque
import hashlib
import json
from pathlib import Path
from statistics import median
from benchmarks.eva_tokenization import grouped_word
from voynich_smt.data.corpus import digest, write_json

OUT = Path('experiments/results/manuscript-width-audit')
WIDTHS = {'fixed-1': (1,), 'fixed-2': (2,), 'fixed-3': (3,), 'mixed-1-2': (1,2), 'mixed-1-2-3': (1,2,3), 'mixed-2-3': (2,3)}


def input_counts(length, widths):
    """Possible nonempty input-unit counts when output widths may vary freely."""
    if length < 1 or not widths or any(w < 1 for w in widths): raise ValueError('Positive lengths required')
    reachable = [set() for _ in range(length+1)]; reachable[0].add(0)
    for total in range(1,length+1):
        for width in widths:
            if width <= total: reachable[total].update(n+1 for n in reachable[total-width])
    return sorted(reachable[length])


def clean(record):
    units = record['tokens']
    return record.get('excluded_reason') is None and bool(units) and all(len(s)==1 and s.isascii() and s.isalpha() and s.islower() for s in units)


def summarize(records, grouped=False, size=22):
    lengths=[]; queue=deque(maxlen=size); folio=None; window_counts=Counter(); window_ceiling_totals={name:Counter() for name in WIDTHS}
    cache={}; windows=0; excluded=0
    for record in records:
        if record.get('folio') != folio: queue.clear(); folio=record.get('folio')
        if not clean(record): excluded+=1; queue.clear(); continue
        word=grouped_word(record['tokens']) if grouped else record['tokens']; length=len(word); lengths.append(length)
        if length not in cache: cache[length]={name:input_counts(length,widths) for name,widths in WIDTHS.items()}
        queue.append(length)
        if len(queue)!=size: continue
        windows+=1
        for name in WIDTHS:
            possibilities=[cache[n][name] for n in queue]
            if all(possibilities):
                window_counts[name]+=1; window_ceiling_totals[name][sum(max(p) for p in possibilities)]+=1
    profiles={}
    for name in WIDTHS:
        accepted=[n for n in lengths if cache[n][name]]
        profiles[name]={'compatible_word_occurrences':len(accepted),'incompatible_word_occurrences':len(lengths)-len(accepted),
            'compatible_22_word_windows':window_counts[name],
            'maximum_input_units_across_compatible_words':sum(max(cache[n][name]) for n in accepted),
            'window_maximum_input_unit_total_histogram':dict(sorted(window_ceiling_totals[name].items()))}
    return {'included_word_occurrences':len(lengths),'excluded_records':excluded,'word_unit_total':sum(lengths),
            'mean_word_units':sum(lengths)/len(lengths),'median_word_units':median(lengths),
            'word_length_histogram':dict(sorted(Counter(lengths).items())), 'windows':windows,'profiles':profiles}


def calculate():
    path=Path('data/processed/zl-eva.json'); raw=json.loads(path.read_text())
    prior_paths=[Path('experiments/results/eva-tokenization/report.json'),Path('experiments/results/word-length-plausibility.json')]
    previous={str(p):{'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in prior_paths}
    pilot=json.loads(Path('experiments/results/conflict-selection.json').read_text())['baseline_request']['ciphertext']['words']
    profiles={}
    for unitization,words in [('atomic',pilot),('existing-grouped',[grouped_word(w) for w in pilot])]:
        profiles[unitization]={name:{'all_words_length_compatible':all(input_counts(len(w),widths) for w in words),
            'incompatible_positions_1based':[i+1 for i,w in enumerate(words) if not input_counts(len(w),widths)],
            'maximum_input_units':sum(max(input_counts(len(w),widths)) for w in words) if all(input_counts(len(w),widths) for w in words) else None} for name,widths in WIDTHS.items()}
    natural=json.loads(Path('experiments/results/latin-h2-natural-random/prepared.json').read_text())
    calibration=[{'record_start':b['record_start'],'training_mean_latin_letters':sum(map(len,b['train']))/len(b['train']),
                  'fixed2_training_mean_cipher_units':2*sum(map(len,b['train']))/len(b['train'])} for b in natural['passages']]
    return {'source_path':str(path),'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'normalization':raw['normalization'],
        'code_sha256':digest(Path(__file__).read_text()),'previous_artifacts':previous,
        'atomic':summarize(raw['records']),'existing-grouped':summarize(raw['records'],True),'original_22_word_pilot':profiles,
        'natural_fixed2_calibration_lengths':calibration,'solver_calls':0,
        'scope':'Necessary arithmetic only. Included records are clean lowercase atomic EVA, uncertainty/annotations retained as barriers; windows may cross lines within folio, not excluded records or folios. Existing grouping only. Output-unit counts are not established manuscript glyph counts. Fixed widths require divisibility in every word; mixed widths count freely varying output lengths without shared-key constraints. No codeword fit, language ranking or decryption. Input counts refer to plaintext units, not expanded letters if contractions are allowed.'}


if __name__ == '__main__':
    result=calculate(); path=OUT/'report.json'
    if path.exists(): assert json.loads(path.read_text())==result
    else: write_json(path,result)
    print(json.dumps({k:{'words':result[k]['included_word_occurrences'],'mean':result[k]['mean_word_units'],'median':result[k]['median_word_units'],'windows':result[k]['windows'],'profiles':{name:{key:value for key,value in row.items() if 'histogram' not in key} for name,row in result[k]['profiles'].items()}} for k in ('atomic','existing-grouped')},indent=2))
