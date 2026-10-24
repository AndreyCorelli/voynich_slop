"""One reversible EVA grouping sensitivity; length/repetition filters, no SMT calls."""
from collections import Counter, deque
import hashlib
import json
from pathlib import Path

from benchmarks.historical_word_lengths import (caesar_segments, latin_segments,
    italian_segments, czech_segments, german_sources, checksum)
from benchmarks.expanded_medieval_latin import WORKS, load_work
from benchmarks.latin_contractions import unitizations

GROUPS = ('cth','ckh','cph','cfh','ch','sh')
SOURCE_URL = 'https://www.voynich.nu/transcr.html'
OUT = Path('experiments/results/eva-tokenization')


def grouped_word(word):
    """Longest-match within a word; source must be atomic lower-case EVA."""
    if any(len(s)!=1 or not s.isascii() or not s.islower() for s in word):
        raise ValueError('Expected atomic lowercase EVA')
    text=''.join(word);out=[];i=0
    while i<len(text):
        match=next((g for g in GROUPS if text.startswith(g,i)),text[i])
        out.append(match);i+=len(match)
    if ''.join(out)!=text:raise RuntimeError('EVA round trip failed')
    return tuple(out)


def repetition_pairs(words):
    return [(i,j) for i in range(len(words)) for j in range(i+1,len(words)) if words[i]==words[j]]


def screen(segments,cipher_words,rules=()):
    """Necessary L1–3 length bounds and expanded-word equality only."""
    lengths=tuple(map(len,cipher_words));pairs=repetition_pairs(cipher_words)
    cache={};hist=Counter();windows=length_ok=repeat_ok=both=0
    for segment in segments:
        queue=deque(maxlen=len(lengths))
        for word in segment:
            if word is None:queue.clear();continue
            if word not in cache:cache[word]=tuple(unitizations(word,rules))
            queue.append(word)
            if len(queue)!=len(lengths):continue
            windows+=1;hist[sum(min(cache[w]) for w in queue)]+=1
            legal=all(any(k<=c<=3*k for k in cache[w]) for w,c in zip(queue,lengths))
            # Same ciphertext requires same expanded plaintext with reversible units.
            repeated=all(queue[i]==queue[j] for i,j in pairs)
            length_ok+=legal;repeat_ok+=repeated;both+=legal and repeated
    total=sum(lengths)
    return {'windows':windows,'minimum_unit_total_histogram':dict(sorted(hist.items())),
            'total_ceiling_compatible':sum(n for k,n in hist.items() if k<=total),
            'positionwise_length_compatible':length_ok,'repetition_compatible':repeat_ok,
            'length_and_repetition_compatible':both}


def corpora():
    s,m=caesar_segments();yield 'caesar',s,[m],''
    for identifier,file,start in [('aquinas','latin-aquinas-ente.html','Quia parvus error'),
                                   ('caroli','latin-caroli.html','Secundis sedentibus')]:
        s,m=latin_segments(file,start);yield identifier,s,[m],''
    for work in WORKS:
        s,m,_=load_work(work);yield work['id'],s,m,''
    for identifier,s,m in german_sources():
        yield identifier,s,[m],'Legacy historical-length normalization retained for paired sensitivity only; bracket-fragment and short-form audits were not applied to this stream. No corrected German lexicon claim.'
    s,m=italian_segments();yield 'italian',s,m,''
    s,m=czech_segments('diplomatic');yield 'czech-diplomatic',s,[m],''


def run():
    baseline=json.loads(Path('experiments/results/conflict-selection.json').read_text())
    request=baseline['baseline_request']
    if checksum({'request':request,'codeword_domains':'observed'})!=baseline['baseline_input_sha256']:
        raise ValueError('Baseline hash mismatch')
    atomic=tuple(tuple(w) for w in request['ciphertext']['words']);grouped=tuple(grouped_word(w) for w in atomic)
    assert len(atomic)==22 and sum(map(len,atomic))==104
    assert repetition_pairs(atomic)==repetition_pairs(grouped)
    inventory=json.loads(Path('experiments/configs/latin-contractions.json').read_text())
    report={'source_url':SOURCE_URL,'source_accessed':'2026-10-09','grouped_sequences':list(GROUPS),
            'baseline_sha256':checksum(baseline),'inventory_sha256':checksum(inventory),
            'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'ciphertext':{'atomic':atomic,'grouped':grouped},
            'ciphertext_lengths':{'atomic':list(map(len,atomic)),'grouped':list(map(len,grouped))},
            'ceilings':{k:{'total_units':sum(map(len,w)),'mean_units':sum(map(len,w))/len(w)} for k,w in [('atomic',atomic),('grouped',grouped)]},
            'repetition_pairs_unchanged':True,'rows':[],'solver_calls':0,
            'semantics':'One greedy reversible grouping, not full Currier conversion or established semantic units. Preserved word boundaries. L1–3 now counts grouped units, so this is a different cipher family, not a relabeling of old solver witnesses. Necessary passage filters only; no key-fit, language-likelihood or historical-cipher conclusion.'}
    for identifier,segments,metadata,caveat in corpora():
        profiles=('letters','bounded-seven') if identifier in {'caesar','aquinas','caroli','einhard','gesta','bury','dante'} else ('letters',)
        for profile in profiles:
            rules=[r for r in inventory['rules'] if r['id'] in inventory['profiles'][profile]]
            row={'source_id':identifier,'profile':profile,'sources':metadata,
                 'records_sha256':checksum(segments),'normalization_caveat':caveat,
                 'atomic':screen(segments,atomic,rules),'grouped':screen(segments,grouped,rules)}
            if row['atomic']['repetition_compatible']!=row['grouped']['repetition_compatible']:
                raise RuntimeError('Reversible grouping changed repetition filter')
            report['rows'].append(row)
            print(identifier,profile,'length survivors',row['atomic']['positionwise_length_compatible'],'->',row['grouped']['positionwise_length_compatible'],'combined',row['grouped']['length_and_repetition_compatible'],flush=True)
    report['complete']=True
    OUT.mkdir(parents=True,exist_ok=True);(OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    return report


if __name__=='__main__':run()
