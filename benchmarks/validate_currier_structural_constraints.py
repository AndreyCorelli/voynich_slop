"""Direct corpus census and invariant audit, independent of cohort extractor."""
from collections import Counter,defaultdict
import json
from pathlib import Path
from benchmarks import currier_structural_constraints as experiment
from benchmarks.manuscript_width_audit import clean
from benchmarks.eva_tokenization import grouped_word
from voynich_smt.data.corpus import digest,write_json

def reachable(length,widths):
    # Independent dynamic program: unit-count reachable totals.
    states={0:{0}}
    for total in range(1,length+1):
        states[total]={count+1 for width in widths for count in states.get(total-width,set())}
    return states[length]

def validate():
    out=experiment.OUT;p=json.loads((out/'prepared.json').read_text());r=json.loads((out/'report.json').read_text());raw=json.loads(experiment.SOURCE.read_text())
    assert digest(raw)==p['source_sha256'] and digest(p)==r['prepared_sha256']
    for path,sha in p['code_sha256'].items():assert digest(Path(path).read_text())==sha
    loci=defaultdict(list)
    for record in raw['records']:loci[record['folio'],record['locus']].append(record)
    results={};examples=[]
    for cohort in ('whole-clean-lines','clean-words'):
        expected={'A':defaultdict(list),'B':defaultdict(list)}
        for (folio,locus),rs in loci.items():
            label=rs[0].get('page_variables',{}).get('L')
            if label not in expected or 'P' not in locus.split(',')[-1]:continue
            eligible=[clean(x) and not x.get('uncertain_space_in_locus') for x in rs]
            if cohort=='whole-clean-lines' and not all(eligible):continue
            for x,yes in zip(rs,eligible):
                if yes:expected[label][folio].append(tuple(x['tokens']))
        for unitization in ('atomic','existing-grouped'):
            for label in ('A','B'):
                row=next(x for x in r['rows'] if (x['cohort'],x['unitization'],x['currier'])==(cohort,unitization,label));s=row['summary']
                fs={f:[grouped_word(w) if unitization!='atomic' else w for w in ws] for f,ws in expected[label].items()}
                words=[w for ws in fs.values() for w in ws];freq=Counter(words);hist=Counter(map(len,words));n=len(words)
                assert s['tokens']==n and s['folios']==len(fs)
                assert s['token_length_histogram']=={str(k):v for k,v in hist.items()}
                assert s['type_length_histogram']=={str(k):v for k,v in Counter(map(len,freq)).items()}
                spectrum=Counter(freq.values());assert s['global_repetition']['frequency_spectrum']=={str(k):v for k,v in spectrum.items()}
                assert sum(k*v for k,v in spectrum.items())==n
                repeat=sum(v*(v-1)//2 for v in freq.values());assert s['global_repetition']['repeat_pairs']==repeat
                assert abs(s['global_repetition']['repeat_pair_rate']-repeat/(n*(n-1)/2))<1e-12
                within=sum(sum(c*(c-1)//2 for c in Counter(ws).values()) for ws in fs.values());pairs=sum(len(ws)*(len(ws)-1)//2 for ws in fs.values())
                assert abs(s['within_folio_repeat_pair_rate']-within/pairs)<1e-12
                assert abs(s['mean_word_length']-sum(k*v for k,v in hist.items())/n)<1e-12
                for name,widths in experiment.WIDTHS.items():
                    profile=s['width_constraints'][name];counts={k:reachable(k,widths) for k in hist}
                    assert profile['incompatible_word_occurrences']==sum(v for k,v in hist.items() if not counts[k])
                    assert profile['candidate_minimum_input_units']==sum(v*min(counts[k]) for k,v in hist.items() if counts[k])
                    assert profile['candidate_maximum_input_units']==sum(v*max(counts[k]) for k,v in hist.items() if counts[k])
                assert sum(s['window_22_total_units_histogram'].values())==s['contiguous_22_word_windows']
                assert sum(s['window_22_exact_repeat_pair_histogram'].values())==s['contiguous_22_word_windows']
                assert all(0<=int(k)<=231 for k in s['window_22_exact_repeat_pair_histogram'])
                results[cohort,unitization,label]=s
                odd=next(w for w in words if len(w)%2)
                examples.append({'cohort':cohort,'unitization':unitization,'currier':label,'fixed2_impossible_word':list(odd),'units':len(odd)})
        for label in ('A','B'):
            a=results[cohort,'atomic',label];g=results[cohort,'existing-grouped',label]
            assert a['global_repetition']==g['global_repetition'] and a['within_folio_repeat_pair_rate']==g['within_folio_repeat_pair_rate']
            assert a['window_22_exact_repeat_pair_histogram']==g['window_22_exact_repeat_pair_histogram']
    write_json(out/'validation.json',{'validated':True,'prepared_sha256':digest(p),'rows':len(r['rows']),'width_witnesses':examples,'checks':'Frozen provenance; direct independent locus/filter census; token/type histograms and frequency spectra; exact global/within-folio pair counts; independent reachable-unit dynamic program; window count totals; atomic/grouped exact repetition identity; explicit fixed2 counterexamples.'})
    print('Validated8 Currier/cohort/unitization summaries')

if __name__=='__main__':validate()
