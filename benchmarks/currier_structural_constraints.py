"""Necessary length/repetition constraints and folio sampling sensitivity."""
from collections import Counter,defaultdict,deque
import json
from pathlib import Path
import random
from statistics import mean,median
from benchmarks.manuscript_width_audit import clean,input_counts
from benchmarks.eva_tokenization import grouped_word
from voynich_smt.data.corpus import digest,write_json
OUT=Path('experiments/results/currier-structural-constraints')
SOURCE=Path('data/processed/zl-eva.json')
WIDTHS={'fixed-1':(1,),'fixed-2':(2,),'fixed-3':(3,),'mixed-1-2':(1,2),'mixed-1-2-3':(1,2,3),'mixed-2-3':(2,3)}
BOOTSTRAPS=1000

def extract(records,cohort):
    loci=[]
    for r in records:
        key=r.get('folio'),r.get('locus')
        if not loci or loci[-1][0]!=key:loci.append((key,[]))
        loci[-1][1].append(r)
    folios={'A':defaultdict(list),'B':defaultdict(list)};runs={'A':[],'B':[]};counts=Counter();pending=[];current=None
    def flush():
        nonlocal pending
        if pending and current:runs[current[1]].append(pending)
        pending=[]
    for (folio,locus),rs in loci:
        label=rs[0].get('page_variables',{}).get('L');eligible=label in ('A','B') and 'P' in locus.split(',')[-1]
        key=(folio,label)
        if key!=current:flush();current=key
        if not eligible:flush();continue
        counts[label+'-paragraph-records']+=len(rs)
        valid=[clean(r) and not r.get('uncertain_space_in_locus') for r in rs]
        if cohort=='whole-clean-lines' and not all(valid):valid=[False]*len(rs)
        for r,ok in zip(rs,valid):
            if not ok:flush();counts[label+'-excluded']+=1;continue
            word=tuple(r['tokens']);folios[label][folio].append(word);pending.append(word);counts[label+'-included']+=1
    flush()
    return folios,runs,dict(counts)

def repeat_stats(words):
    freq=Counter(words);n=len(words);pairs=n*(n-1)//2;equal=sum(c*(c-1)//2 for c in freq.values())
    return {'tokens':n,'types':len(freq),'type_token_ratio':len(freq)/n,'repeat_pairs':equal,'possible_pairs':pairs,
        'repeat_pair_rate':equal/pairs if pairs else None,'frequency_spectrum':dict(sorted(Counter(freq.values()).items())),
        'most_frequent_word_share':max(freq.values())/n}

def bootstrap(folios,seed):
    # Resample folios as clusters; repeats use sums of within-folio pairs only.
    # Never concatenate duplicated folios into a new global repeat spectrum.
    entries=[]
    for words in folios.values():
        lengths=Counter(map(len,words));r=repeat_stats(words)
        entries.append((lengths,r['repeat_pairs'],r['possible_pairs']))
    rng=random.Random(seed);values=defaultdict(list)
    for _ in range(BOOTSTRAPS):
        sample=[rng.choice(entries) for _ in entries];hist=Counter()
        for h,_,_ in sample:hist.update(h)
        n=sum(hist.values());m=sum(k*v for k,v in hist.items())/n
        values['mean_word_length'].append(m)
        values['word_length_variance'].append(sum(v*(k-m)**2 for k,v in hist.items())/n)
        values['one_unit_word_fraction'].append(hist[1]/n)
        values['odd_length_fraction'].append(sum(v for k,v in hist.items() if k%2)/n)
        values['within_folio_repeat_pair_rate'].append(sum(r for _,r,_ in sample)/sum(p for _,_,p in sample))
    return {k:{'percentile_95_interval':[sorted(v)[24],sorted(v)[974]],'draws':BOOTSTRAPS} for k,v in values.items()}

def summarize(folios,runs):
    words=[w for ws in folios.values() for w in ws];lengths=list(map(len,words));hist=Counter(lengths)
    n=len(words);m=mean(lengths);v=mean((x-m)**2 for x in lengths);repeats=repeat_stats(words)
    within=[repeat_stats(ws) for ws in folios.values()];profiles={}
    window_means=Counter();windows=0;window_frequencies=Counter();windows_by_model=Counter()
    for run in runs:
        for i in range(len(run)-21):
            selected=run[i:i+22];ls=list(map(len,selected));windows+=1;window_means[sum(ls)]+=1
            window_frequencies[repeat_stats(selected)['repeat_pairs']]+=1
            for name,widths in WIDTHS.items():
                if all(input_counts(x,widths) for x in ls):windows_by_model[name]+=1
    for name,widths in WIDTHS.items():
        illegal=[x for x in hist if not input_counts(x,widths)]
        profiles[name]={'incompatible_word_occurrences':sum(hist[x] for x in illegal),'incompatible_lengths':sorted(illegal),
          'compatible_22_word_windows':windows_by_model[name],
          'candidate_minimum_input_units':sum(hist[x]*min(input_counts(x,widths)) for x in hist if input_counts(x,widths)),
          'candidate_maximum_input_units':sum(hist[x]*max(input_counts(x,widths)) for x in hist if input_counts(x,widths)),
          'input_totals_scope':'Compatible occurrences only; not a whole-corpus bound if any occurrence is incompatible.'}
    return {'folios':len(folios),'tokens':n,'glyphs':sum(lengths),'token_length_histogram':dict(sorted(hist.items())),
      'type_length_histogram':dict(sorted(Counter(map(len,set(words))).items())),
      'mean_word_length':m,'median_word_length':median(lengths),'word_length_variance':v,
      'word_length_skewness':mean((x-m)**3 for x in lengths)/v**1.5 if v else None,
      'one_unit_word_fraction':hist[1]/n,'odd_length_fraction':sum(c for k,c in hist.items() if k%2)/n,
      'global_repetition':repeats,'within_folio_repeat_pair_rate':sum(x['repeat_pairs'] for x in within)/sum(x['possible_pairs'] for x in within),
      'folio_stats':[{'folio':f,'mean_word_length':mean(map(len,ws)),**repeat_stats(ws)} for f,ws in folios.items()],
      'contiguous_22_word_windows':windows,'window_22_total_units_histogram':dict(sorted(window_means.items())),
      'window_22_exact_repeat_pair_histogram':dict(sorted(window_frequencies.items())),
      'width_constraints':profiles}

def prepare():
    raw=json.loads(SOURCE.read_text());deps=[Path(__file__),Path('benchmarks/manuscript_width_audit.py'),Path('benchmarks/eva_tokenization.py')]
    p={'source_sha256':digest(raw),'code_sha256':{str(f):digest(f.read_text()) for f in deps},'bootstrap_draws':BOOTSTRAPS,'bootstrap_seed':81001,
      'protocol':'Currier metadata L=A/B,paragraph loci only. Two cohorts: whole-clean-lines(all records clean lowercase ASCII atomic and no uncertain spacing) or clean-words(same per-record filter,invalid records are window barriers). Separate A/B; atomic and existing greedy reversible EVA grouping. Windows22 never cross excluded records/loci or folios; may cross consecutive included lines in same folio. Folio cluster bootstrap1000draws for mean,variance,one-unit,odd fractions and within-folio exact-pair rate. Global word-frequency spectrum descriptive only; do not bootstrap concatenated duplicate folios. Percentile intervals describe folio heterogeneity under exchangeable-folio sampling, not scribal/normalization uncertainty or a random-manuscript confidence claim. Necessary bounds on plaintext unit counts only for preserved spaces,no deletions/nulls,width inventory; repetition inequalities require unique inverse mapping and same word alignment. No language scores, learned classifier,Z3 or new historical contraction inventory.'}
    path=OUT/'prepared.json'
    if path.exists():assert json.loads(path.read_text())==p
    else:write_json(path,p)
    return p,raw

def run():
    p,raw=prepare();rows=[]
    for ci,cohort in enumerate(('whole-clean-lines','clean-words')):
        folios,runs,counts=extract(raw['records'],cohort)
        for ui,unitization in enumerate(('atomic','existing-grouped')):
            for li,label in enumerate(('A','B')):
                transform=(lambda w:w) if unitization=='atomic' else grouped_word
                fs={f:[transform(w) for w in ws] for f,ws in folios[label].items()};rs=[[transform(w) for w in run] for run in runs[label]]
                summary=summarize(fs,rs);summary['bootstrap']=bootstrap(fs,81001+ci*4+ui*2+li)
                rows.append({'cohort':cohort,'unitization':unitization,'currier':label,'filter_counts':counts,'summary':summary})
                print(cohort,unitization,label,summary['tokens'],round(summary['mean_word_length'],3),round(summary['within_folio_repeat_pair_rate'],4),flush=True)
    write_json(OUT/'report.json',{'prepared_sha256':digest(p),'rows':rows,'complete':True,'solver_calls':0})

if __name__=='__main__':run()
