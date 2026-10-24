"""A/B length contrasts matched on section and original line positions."""
from collections import Counter,defaultdict
import json
from pathlib import Path
import random
from benchmarks.manuscript_width_audit import clean
from benchmarks.eva_tokenization import grouped_word
from voynich_smt.data.corpus import digest,write_json
OUT=Path('experiments/results/currier-section-position')
SOURCE=Path('data/processed/zl-eva.json')
MIN_FOLIOS=5
MIN_TOKENS=10
DRAWS=1000

def line_role(body):
    start='<%>' in body;end='<$>' in body
    return 'single' if start and end else 'initial' if start else 'final' if end else 'unmarked'

def position(index,size):return 'single' if size==1 else 'first' if index==0 else 'last' if index==size-1 else 'interior'

def collect(records,cohort,unitization):
    loci=[]
    for r in records:
        key=r['folio'],r['locus']
        if not loci or loci[-1][0]!=key:loci.append((key,[]))
        loci[-1][1].append(r)
    result=[]
    for (folio,locus),rs in loci:
        label=rs[0].get('page_variables',{}).get('L');section=rs[0].get('section')
        if label not in ('A','B') or not section or 'P' not in locus.split(',')[-1]:continue
        valid=[clean(r) and not r.get('uncertain_space_in_locus') for r in rs]
        if cohort=='whole-clean-lines' and not all(valid):continue
        role=line_role(rs[0].get('raw_locus_text',''))
        for i,(r,yes) in enumerate(zip(rs,valid)):
            if not yes:continue
            word=tuple(r['tokens']);units=word if unitization=='atomic' else grouped_word(word)
            result.append({'folio':folio,'currier':label,'section':section,'line_role':role,'word_position':position(i,len(rs)),'length':len(units),'word':word})
    return result

def stats(rows):
    n=len(rows);return {'tokens':n,'folios':len({r['folio'] for r in rows}),'mean':sum(r['length'] for r in rows)/n if n else None}

def common_sections(rows):
    sections=[]
    for s in sorted({r['section'] for r in rows}):
        subsets={l:[r for r in rows if r['section']==s and r['currier']==l] for l in ('A','B')}
        if all(len({r['folio'] for r in subsets[l]})>=MIN_FOLIOS for l in subsets):sections.append(s)
    return sections

def standardize(rows,fields,sections):
    strata=defaultdict(lambda:{'A':[],'B':[]})
    for r in rows:
        if r['section'] in sections:strata[tuple(r[f] for f in fields)][r['currier']].append(r)
    support={s:ls for s,ls in strata.items() if all(len(xs)>=MIN_TOKENS and len({r['folio'] for r in xs})>=MIN_FOLIOS for xs in ls.values())}
    if not support:return None
    total=sum(len(xs) for ls in support.values() for xs in ls.values());weights={s:sum(map(len,ls.values()))/total for s,ls in support.items()}
    means={l:sum(weights[s]*stats(ls[l])['mean'] for s,ls in support.items()) for l in ('A','B')}
    folio_tables={l:defaultdict(lambda:defaultdict(lambda:[0,0])) for l in ('A','B')}
    for s,ls in support.items():
        for l,xs in ls.items():
            for r in xs:
                entry=folio_tables[l][r['folio']][s];entry[0]+=1;entry[1]+=r['length']
    rng=random.Random(101001);deltas=[];attempts=0
    while len(deltas)<DRAWS and attempts<10000:
        attempts+=1;boot={}
        for l in ('A','B'):
            keys=list(folio_tables[l]);sample=rng.choices(keys,k=len(keys));totals=defaultdict(lambda:[0,0])
            for f in sample:
                for s,(n,g) in folio_tables[l][f].items():totals[s][0]+=n;totals[s][1]+=g
            if any(not totals[s][0] for s in support):break
            boot[l]=sum(weights[s]*totals[s][1]/totals[s][0] for s in support)
        if len(boot)==2:deltas.append(boot['B']-boot['A'])
    assert len(deltas)==DRAWS
    selected_tokens={l:sum(len(ls[l]) for ls in support.values()) for l in ('A','B')}
    available={l:sum(r['currier']==l for r in rows) for l in ('A','B')}
    return {'fields':fields,'sections':sections,'standardized_means':means,'B_minus_A':means['B']-means['A'],
      'contrast_percentile_95_interval':[sorted(deltas)[24],sorted(deltas)[974]],'bootstrap_draws':DRAWS,'bootstrap_attempts':attempts,
      'included_tokens':selected_tokens,'fraction_of_all_cohort_tokens':{l:selected_tokens[l]/available[l] for l in ('A','B')},
      'included_folios':{l:len(folio_tables[l]) for l in ('A','B')},
      'strata':[{'key':list(s),'weight':weights[s],'A':stats(ls['A']),'B':stats(ls['B'])} for s,ls in sorted(support.items())]}

def run():
    raw=json.loads(SOURCE.read_text());deps=[Path(__file__),Path('benchmarks/manuscript_width_audit.py'),Path('benchmarks/eva_tokenization.py')]
    p={'source_sha256':digest(raw),'code_sha256':{str(f):digest(f.read_text()) for f in deps},'minimum_folios_per_class':MIN_FOLIOS,'minimum_tokens_per_stratum_class':MIN_TOKENS,'bootstrap_draws':DRAWS,
      'protocol':'A/B paragraph metadata; broader clean-word primary and whole-clean-line sensitivity; atomic primary/grouped sensitivity. Raw I section, paragraph line-role explicit <%>/<$> markers(initial/final/single/unmarked), original parsed-record first/interior/last/single word position before filtering. Section eligibility5distinct folios per class; each supported stratum needs5folios and10tokens per class. Pooled A+B token weights fixed before folio bootstrap1000 valid draws, resample classes separately; skip draws missing any fixed stratum, report attempts. Compare unadjusted, section-standardized, section+word-position, section+line-role+word-position, and predeclared H herbal withinsection. No learned score, manuscript causal model, key recovery, permutation of confounded labels, null significance claim or Z3. Intervals describe exchangeable-folio heterogeneity, not transcription/section-label uncertainty.'}
    path=OUT/'prepared.json'
    if path.exists():assert json.loads(path.read_text())==p
    else:write_json(path,p)
    results=[]
    for cohort in ('clean-words','whole-clean-lines'):
        for units in ('atomic','existing-grouped'):
            rows=collect(raw['records'],cohort,units);sections=common_sections(rows);means={l:stats([r for r in rows if r['currier']==l]) for l in ('A','B')}
            counts=[{'section':s,**{l:stats([r for r in rows if r['section']==s and r['currier']==l]) for l in ('A','B')}} for s in sorted({r['section'] for r in rows})]
            adjustments={name:standardize(rows,fields,sections) for name,fields in [
              ('section',['section']),('section+word-position',['section','word_position']),('section+line-role+word-position',['section','line_role','word_position'])]}
            adjustments['herbal+line-role+word-position']=standardize(rows,['section','line_role','word_position'],['H']) if 'H' in sections else None
            result={'cohort':cohort,'unitization':units,'unadjusted':means,'unadjusted_B_minus_A':means['B']['mean']-means['A']['mean'],'section_census':counts,'adjustments':adjustments}
            results.append(result);print(cohort,units,'sections',sections,'unadjusted',round(result['unadjusted_B_minus_A'],3),flush=True)
            for name,a in adjustments.items():print(name,None if a is None else (round(a['B_minus_A'],3),a['contrast_percentile_95_interval']),flush=True)
    write_json(OUT/'report.json',{'prepared_sha256':digest(p),'results':results,'complete':True,'solver_calls':0})

if __name__=='__main__':run()
