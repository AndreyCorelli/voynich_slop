"""Necessary length/repetition checks with at most two ciphertext boundary edits."""
import argparse
from bisect import bisect_left,bisect_right
from collections import Counter
from functools import lru_cache
import hashlib
import json
from pathlib import Path

from benchmarks.expanded_medieval_latin import WORKS,load_work
from benchmarks.historical_word_lengths import latin_segments
from benchmarks.latin_contractions import CONFIG,checksum,unitizations,validate_inventory

OUT=Path('experiments/results/word-boundary-edits')


def emission_lengths(word,rules):
    return tuple(sorted({n for k in unitizations(word,rules) for n in range(k,3*k+1)}))


def alignments(words,cipher_words,emissions,budget=2):
    """Enumerate complete word alignments; edits are symmetric difference of cuts."""
    if not cipher_words or not words or budget not in (0,1,2):
        raise ValueError('Nonempty words/ciphertext and edit budget 0–2 required')
    stream=''.join(cipher_words);size=len(stream)
    original=[];position=0
    for w in cipher_words[:-1]:
        position+=len(w);original.append(position)
    original_set=set(original)
    low_words=max(1,len(cipher_words)-budget);high_words=len(cipher_words)+budget
    words=words[:high_words]
    @lru_cache(None)
    def transitions(i,start,cost):
        if i>=len(words):return ()
        result=[]
        for length in emissions[words[i]]:
            end=start+length
            if end>size:break
            removed=bisect_left(original,end)-bisect_right(original,start)
            added=int(end<size and end not in original_set)
            next_cost=cost+removed+added
            if next_cost<=budget:result.append((end,next_cost))
        return tuple(result)
    @lru_cache(None)
    def reachable(i,start,cost):
        if start==size:return low_words<=i<=high_words
        if i>=len(words):return False
        return any(reachable(i+1,end,c) for end,c in transitions(i,start,cost))
    def walk(i,start,cost,cuts,seen,conflicts):
        if start==size:
            if low_words<=i<=high_words:
                yield {'word_count':i,'edits':cost,'cuts':list(cuts[:-1]),
                       'added_cuts':sorted(set(cuts[:-1])-original_set),
                       'removed_cuts':sorted(original_set-set(cuts[:-1])),
                       'ciphertext_words':[stream[a:b] for a,b in zip((0,)+cuts[:-1],cuts)],
                       'plaintext':words[:i], 'repetition_compatible':not conflicts,
                       'repetition_conflicts':conflicts}
            return
        for end,next_cost in transitions(i,start,cost):
            if not reachable(i+1,end,next_cost):continue
            cipher=stream[start:end];plain=words[i]
            extra=[]
            if cipher in seen and seen[cipher][1]!=plain:
                extra=[{'ciphertext_word':cipher,'left_position':seen[cipher][0]+1,
                        'right_position':i+1,'left_plaintext':seen[cipher][1],'right_plaintext':plain}]
            next_seen=seen.copy();next_seen.setdefault(cipher,(i,plain))
            yield from walk(i+1,end,next_cost,cuts+(end,),next_seen,conflicts+extra)
    if reachable(0,0,0):
        yield from walk(0,0,0,(),{},[])


def uninterrupted(segments):
    offset=0
    for segment in segments:
        run=[];start=offset
        for i,word in enumerate(segment):
            if word is None:
                if run:yield start,run
                run=[];start=offset+i+1
            else:run.append(word)
        if run:yield start,run
        offset+=len(segment)


def analyze(segments,rules,cipher_words,handle=None):
    emissions={w:emission_lengths(w,rules) for segment in segments for w in segment if w is not None}
    length_counts=Counter();repeat_counts=Counter();length_windows=Counter();repeat_windows=Counter()
    windows=Counter();examples={str(n):[] for n in range(3)};repeat_examples={str(n):[] for n in range(3)}
    for source_start,words in uninterrupted(segments):
        for n in range(len(cipher_words)-2,len(cipher_words)+3):
            windows[n]+=max(0,len(words)-n+1)
        for start in range(max(0,len(words)-(len(cipher_words)-2)+1)):
            lengths=set();repeats=set()
            for a in alignments(words[start:start+len(cipher_words)+2],cipher_words,emissions):
                edits=a['edits'];key=(a['word_count'],edits)
                length_counts[edits]+=1;lengths.add(key)
                a={'start_record':source_start+start,'end_record_exclusive':source_start+start+a['word_count'],**a}
                if handle is not None:handle.write(json.dumps(a,ensure_ascii=False)+'\n')
                if len(examples[str(edits)])<10:examples[str(edits)].append(a)
                if a['repetition_compatible']:
                    repeat_counts[edits]+=1;repeats.add(key)
                    if len(repeat_examples[str(edits)])<20:repeat_examples[str(edits)].append(a)
            for _,edits in lengths:length_windows[edits]+=1
            for _,edits in repeats:repeat_windows[edits]+=1
    return {'eligible_source_windows_by_word_count':dict(windows),
            'length_compatible_alignments_by_exact_edits':{str(n):length_counts[n] for n in range(3)},
            'repetition_compatible_alignments_by_exact_edits':{str(n):repeat_counts[n] for n in range(3)},
            'length_compatible_source_windows_by_exact_edits':{str(n):length_windows[n] for n in range(3)},
            'repetition_compatible_source_windows_by_exact_edits':{str(n):repeat_windows[n] for n in range(3)},
            'length_examples':examples,'repetition_examples':repeat_examples}


def run():
    config=json.loads(CONFIG.read_text());validate_inventory(config)
    baseline=json.loads(Path('experiments/results/conflict-selection.json').read_text());q=baseline['baseline_request']
    if checksum({'request':q,'codeword_domains':'observed'})!=baseline['baseline_input_sha256']:
        raise ValueError('Baseline hash mismatch')
    if len(q['ciphertext']['words'])!=22 or sum(map(len,q['ciphertext']['words']))!=104 or q['bounds']['min_code_length']!=1 or q['bounds']['max_code_length']!=3:
        raise ValueError('Expected fixed 22-word L1–3 block')
    corpora=[]
    for identifier,filename,incipit in [('aquinas','latin-aquinas-ente.html','Quia parvus error'),('caroli','latin-caroli.html','Secundis sedentibus')]:
        segments,meta=latin_segments(filename,incipit);corpora.append((identifier,segments,[meta]))
    for work in WORKS:
        segments,meta,_=load_work(work);corpora.append((work['id'],segments,meta))
    OUT.mkdir(parents=True,exist_ok=True);rows=[]
    for profile in ('letters','bounded-seven'):
        rules=[r for r in config['rules'] if r['id'] in config['profiles'][profile]]
        for identifier,segments,meta in corpora:
            path=OUT/f'{identifier}-{profile}-alignments.jsonl'
            with path.open('w') as handle:metrics=analyze(segments,rules,[''.join(w) for w in q['ciphertext']['words']],handle)
            rows.append({'source_id':identifier,'profile':profile,'sources':meta,'records_sha256':checksum(segments),
                         'alignments_path':str(path),'alignments_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),**metrics})
            print(identifier,profile,'length',metrics['length_compatible_alignments_by_exact_edits'],
                  'repetition',metrics['repetition_compatible_alignments_by_exact_edits'],flush=True)
    report={'schema_version':1,'inventory_sha256':checksum(config),'baseline_sha256':checksum(baseline),
            'analysis_code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'rows':rows,'complete':True,'solver_calls':0,
            'semantics':'At most two insertions/deletions of ciphertext word boundaries, with all 104 characters fixed. A moved boundary costs two edits. Source word order/boundaries and contraction inventory unchanged; 20–24-word attested passages. No crossing source gaps/books/chapters. Emission lengths consider every optional reversible unit count with L1–3. Exact modified ciphertext-word repetition checked. Necessary conditions only: no global key, prefix-free feasibility, or cycling constraint is solved.'}
    (OUT/'report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    return report


if __name__=='__main__':run()
