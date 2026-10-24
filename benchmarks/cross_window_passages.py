"""Preselected cross-section passage filters, fixed inventories, no SMT calls."""
from collections import Counter, deque
import hashlib
import json
from pathlib import Path

from benchmarks.eva_tokenization import corpora, grouped_word, screen, repetition_pairs, GROUPS
from benchmarks.historical_word_lengths import checksum

CORPUS = Path('data/processed/zl-eva.json')
OUT = Path('experiments/results/cross-window-passages')


def select_windows(records, size=22):
    """One per section, plus one for each of two largest eligible sections."""
    candidates={};pending=deque(maxlen=size);previous=None
    for index,r in enumerate(records):
        key=(r.get('section'),r.get('folio'))
        if key!=previous:pending.clear()
        previous=key
        if not r['tokens'] or not key[0]:pending.clear();continue
        pending.append(index)
        if len(pending)==size:candidates.setdefault(key[0],[]).append(tuple(pending))
    if len(candidates)!=8:raise ValueError('Expected eight eligible section codes')
    largest=sorted(candidates,key=lambda s:(-len(candidates[s]),s))[:2]
    chosen=[];used=set()
    for section in sorted(candidates):
        pool=candidates[section];count=2 if section in largest else 1
        for j in range(count):
            target=((j+1)*len(pool))//(count+1)
            # Nearest deterministic fallback if the target overlaps a prior window.
            indices=next((pool[k] for k in sorted(range(len(pool)),key=lambda k:(abs(k-target),k))
                          if not used.intersection(pool[k])),None)
            if indices is None:raise ValueError('Unable to select nonoverlapping windows')
            used.update(indices)
            chosen.append({'id':f'{section}-{j+1}','section':section,
                'record_indices':list(indices),'folio':records[indices[0]]['folio'],
                'start_locus':records[indices[0]]['locus'],'end_locus':records[indices[-1]]['locus'],
                'atomic_words':[records[k]['tokens'] for k in indices]})
    if len(chosen)!=10:raise RuntimeError('Expected ten windows')
    return chosen


def run():
    corpus=json.loads(CORPUS.read_text());windows=select_windows(corpus['records'])
    selection={'corpus_sha256':checksum(corpus),'normalization':corpus['normalization'],
        'rule':'Eight section codes, one each; two largest eligible-candidate sections get a second. Candidate ranks at midpoint or thirds, same folio, no excluded-word bridging; deterministic nearest nonoverlap fallback. No length, repetition or language scores used.',
        'windows':windows}
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'selection.json').write_text(json.dumps(selection,ensure_ascii=False,indent=2)+'\n')
    # Freeze selection before examining any language corpus.
    inventory=json.loads(Path('experiments/configs/latin-contractions.json').read_text())
    sources=list(corpora())
    report={'selection_sha256':checksum(selection),'inventory_sha256':checksum(inventory),
        'grouped_sequences':list(GROUPS),'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'screen_code_sha256':hashlib.sha256(Path('benchmarks/eva_tokenization.py').read_bytes()).hexdigest(),
        'rows':[],'window_summary':[],'solver_calls':0,'complete':False,
        'semantics':'Necessary L1–3 passage length and reversible equality filters, not key fits or language probabilities. Eight section codes are metadata categories, not eight independent text genres. German legacy normalization caveat retained. One grouped inventory and fixed seven Latin contractions; no post-result selection.'}
    for window in windows:
        atomic=tuple(map(tuple,window['atomic_words']));grouped=tuple(grouped_word(w) for w in atomic)
        assert repetition_pairs(atomic)==repetition_pairs(grouped)
        for identifier,segments,metadata,caveat in sources:
            profiles=('letters','bounded-seven') if identifier in {'caesar','aquinas','caroli','einhard','gesta','bury','dante'} else ('letters',)
            for profile in profiles:
                rules=[r for r in inventory['rules'] if r['id'] in inventory['profiles'][profile]]
                row={'window_id':window['id'],'source_id':identifier,'profile':profile,
                     'records_sha256':checksum(segments),'sources':metadata,'normalization_caveat':caveat}
                for mode,cipher in [('atomic',atomic),('grouped',grouped)]:
                    metrics=screen(segments,cipher,rules)
                    # Keep compact paired counts; full histograms remain in prior fixed-block reports.
                    metrics.pop('minimum_unit_total_histogram')
                    row[mode]=metrics
                assert row['atomic']['repetition_compatible']==row['grouped']['repetition_compatible']
                report['rows'].append(row)
        rows=[r for r in report['rows'] if r['window_id']==window['id']]
        summary={'window_id':window['id'],'folio':window['folio'],
                 'repeated_word_pairs':len(repetition_pairs(atomic)),
                 'atomic_total':sum(map(len,atomic)),'grouped_total':sum(map(len,grouped)),
                 **{m+'_combined_survivors':sum(r[m]['length_and_repetition_compatible'] for r in rows) for m in ('atomic','grouped')}}
        report['window_summary'].append(summary)
        (OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
        print(summary,flush=True)
    report['complete']=True
    (OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    return report


if __name__=='__main__':run()
