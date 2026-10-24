"""Descriptive equal-window repetition diagnostics; no cipher fitting."""
from collections import Counter, defaultdict, deque
import hashlib
import json
from pathlib import Path
import re

from benchmarks.eva_tokenization import corpora, grouped_word
from benchmarks.historical_word_lengths import checksum

SIZE = 22
OUT = Path('experiments/results/word-repetition')
SELECTION = Path('experiments/results/cross-window-passages/selection.json')


def pattern(words):
    first={}
    return tuple(first.setdefault(w,i) for i,w in enumerate(words))


def metrics(words):
    positions=defaultdict(list)
    for i,w in enumerate(words):positions[w].append(i)
    multiplicities=Counter(map(len,positions.values()))
    distances=Counter(j-i for indices in positions.values() for k,i in enumerate(indices) for j in indices[k+1:])
    return {'distinct_words':len(positions),'repeat_excess':len(words)-len(positions),
            'repeated_types':sum(n for k,n in multiplicities.items() if k>1),
            'max_multiplicity':max(multiplicities,default=0),'equal_word_pairs':sum(distances.values()),
            'multiplicity_histogram':dict(sorted(multiplicities.items())),
            'pair_distance_histogram':dict(sorted(distances.items())),
            'nearest_repeat_distance':min(distances,default=None)}


def windows(segments,size=SIZE):
    for segment_index,segment in enumerate(segments):
        pending=deque(maxlen=size);run_position=0
        for word in segment:
            if word is None:pending.clear();run_position=0;continue
            pending.append(word);run_position+=1
            if len(pending)==size:
                yield tuple(pending),(run_position-size)%size==0


def thematic():
    folder=Path('data/processed/historical-comparanda')
    manifest=json.loads((folder/'frequencies.json').read_text())
    for entry in manifest['texts']:
        path=folder/(entry['id']+'.txt');raw=path.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=entry['sha256']:raise ValueError('Comparandum text hash mismatch')
        text=raw.decode();text=re.sub(r'\b\d+[a-z]?\b','',text)
        words=re.findall(r"[^\W\d_]+(?:['’][^\W\d_]+)*",text.lower())
        if len(words)!=entry['tokens']:raise ValueError('Frequency tokenizer count mismatch')
        yield entry['id'],[words],{'language':entry['language'],'source':entry['source'],
            'text_sha256':entry['sha256'],'normalization':manifest['method'],
            'caveat':'Uses existing frequency-text extraction, including headings, removed numbers and flattened book/chapter boundaries; not the barrier-preserving passage parser. Turba recension compilation/OCR uncertain; Emerald short; English later supplement; Greek accents retained.'}


def summarize(hist):
    count=sum(hist.values())
    if not count:return {'windows':0}
    def rank(index):
        cumulative=0
        for value,n in sorted(hist.items()):
            cumulative+=n
            if index<cumulative:return value
    def quantile(p):
        i=(count-1)*p;a=int(i);b=min(a+1,count-1)
        return rank(a)+(rank(b)-rank(a))*(i-a)
    return {'windows':count,'minimum':min(hist),'p05':quantile(.05),'median':quantile(.5),
            'p95':quantile(.95),'maximum':max(hist),'histogram':dict(sorted(hist.items()))}


def compare(segments,targets):
    keys=('distinct_words','repeat_excess','repeated_types','max_multiplicity','equal_word_pairs')
    h={k:Counter() for k in keys};nonoverlap={k:Counter() for k in keys}
    distances=Counter();nearest=Counter();no_repeats=0
    implication=Counter();exact=Counter();non_implication=Counter();non_exact=Counter()
    target_patterns={name:pattern(words) for name,words in targets.items()}
    pairs={name:[(i,j) for i in range(SIZE) for j in range(i+1,SIZE) if words[i]==words[j]] for name,words in targets.items()}
    for words,non in windows(segments):
        m=metrics(words)
        for k in keys:
            h[k][m[k]]+=1
            if non:nonoverlap[k][m[k]]+=1
        distances.update(m['pair_distance_histogram'])
        if m['nearest_repeat_distance'] is None:no_repeats+=1
        else:nearest[m['nearest_repeat_distance']]+=1
        signature=pattern(words)
        for name in targets:
            ok=all(words[i]==words[j] for i,j in pairs[name]);same=signature==target_patterns[name]
            implication[name]+=ok;exact[name]+=same
            if non:non_implication[name]+=ok;non_exact[name]+=same
    total=sum(h[keys[0]].values());non_total=sum(nonoverlap[keys[0]].values())
    comparisons=[]
    for name,words in targets.items():
        m=metrics(words)
        comparisons.append({'window_id':name,'equal_ciphertext_implies_equal_plaintext_matches':implication[name],
            'fraction':implication[name]/total if total else None,
            'exact_equality_partition_matches':exact[name],
            'nonoverlapping_implication_matches':non_implication[name],
            'nonoverlapping_exact_partition_matches':non_exact[name],
            'marginal_ranks':{k:{'below':sum(n for value,n in h[k].items() if value<m[k]),
                'equal':h[k][m[k]],'above':sum(n for value,n in h[k].items() if value>m[k])} for k in keys}})
    return {'windows':total,'nonoverlapping_windows':non_total,'no_repeat_windows':no_repeats,
            'distributions':{k:summarize(v) for k,v in h.items()},
            'nonoverlapping_distributions':{k:summarize(v) for k,v in nonoverlap.items()},
            'pooled_pair_distances':dict(sorted(distances.items())),
            'nearest_repeat_distance':summarize(nearest),'comparisons':comparisons}


def run():
    selection=json.loads(SELECTION.read_text());targets={w['id']:tuple(map(tuple,w['atomic_words'])) for w in selection['windows']}
    for words in targets.values():
        if pattern(words)!=pattern(tuple(grouped_word(w) for w in words)):
            raise RuntimeError('Reversible EVA grouping changed repetition pattern')
    # Include the earlier opening block as an explicitly separate reference.
    baseline=json.loads(Path('experiments/results/conflict-selection.json').read_text())
    targets['opening-reference']=tuple(map(tuple,baseline['baseline_request']['ciphertext']['words']))
    report={'selection_sha256':checksum(selection),'opening_baseline_sha256':checksum(baseline),
        'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'window_words':SIZE,'target_metrics':{name:metrics(words) for name,words in targets.items()},
        'rows':[],'complete':False,'solver_calls':0,
        'semantics':'Descriptive distributions, not p-values or language probabilities. Sliding windows overlap; nonoverlapping sensitivity separately recorded. Distances are all equal-word pairs in token positions, not glyph distances. Exact partitions are diagnostics only: different ciphertext words can decode to the same plaintext under homophony. Implication filter is necessary for globally unique decoding, not for every cipher family. EVA grouped inventory preserves these statistics. Source normalizations remain separate.'}
    sources=[(i,s,{'sources':m,'normalization_caveat':c}) for i,s,m,c in corpora()]+list(thematic())
    OUT.mkdir(parents=True,exist_ok=True)
    for identifier,segments,metadata in sources:
        row={'source_id':identifier,'records_sha256':checksum(segments),'metadata':metadata,**compare(segments,targets)}
        report['rows'].append(row)
        (OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
        opening=next(c for c in row['comparisons'] if c['window_id']=='opening-reference')
        print(identifier,'windows',row['windows'],'median distinct',row['distributions']['distinct_words'].get('median'),
            'opening implication matches',opening['equal_ciphertext_implies_equal_plaintext_matches'],flush=True)
    report['complete']=True
    (OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    return report


if __name__=='__main__':run()
