"""Independent matched mean/coverage checks and grouping decomposition."""
from collections import Counter,defaultdict
import json
from pathlib import Path
from benchmarks import currier_section_position as experiment
from benchmarks.manuscript_width_audit import clean
from benchmarks.eva_tokenization import grouped_word,GROUPS
from voynich_smt.data.corpus import digest,write_json

def validate():
    out=experiment.OUT;p=json.loads((out/'prepared.json').read_text());report=json.loads((out/'report.json').read_text());raw=json.loads(experiment.SOURCE.read_text())
    assert digest(raw)==p['source_sha256'] and digest(p)==report['prepared_sha256']
    for path,sha in p['code_sha256'].items():assert digest(Path(path).read_text())==sha
    loci=defaultdict(list)
    for r in raw['records']:loci[r['folio'],r['locus']].append(r)
    rows_by_cohort={};decompositions=[]
    for cohort in ('clean-words','whole-clean-lines'):
        rows=[]
        for (folio,locus),rs in loci.items():
            label=rs[0].get('page_variables',{}).get('L');section=rs[0].get('section')
            if label not in ('A','B') or not section or 'P' not in locus.split(',')[-1]:continue
            valid=[clean(r) and not r.get('uncertain_space_in_locus') for r in rs]
            if cohort=='whole-clean-lines' and not all(valid):continue
            body=rs[0].get('raw_locus_text','');role='single' if '<%>' in body and '<$>' in body else 'initial' if '<%>' in body else 'final' if '<$>' in body else 'unmarked'
            for i,(r,ok) in enumerate(zip(rs,valid)):
                if ok:rows.append({'folio':folio,'currier':label,'section':section,'line_role':role,'word_position':'single' if len(rs)==1 else 'first' if i==0 else 'last' if i==len(rs)-1 else 'interior','word':tuple(r['tokens'])})
        rows_by_cohort[cohort]=rows
        for units in ('atomic','existing-grouped'):
            result=next(r for r in report['results'] if r['cohort']==cohort and r['unitization']==units)
            for label in ('A','B'):
                words=[r['word'] for r in rows if r['currier']==label]
                lengths=[len(w) if units=='atomic' else len(grouped_word(w)) for w in words]
                assert len(words)==result['unadjusted'][label]['tokens']
                assert abs(sum(lengths)/len(lengths)-result['unadjusted'][label]['mean'])<1e-12
            for name,a in result['adjustments'].items():
                if a is None:continue
                fields=a['fields'];n=defaultdict(int);totals=defaultdict(int);folios=defaultdict(set)
                for r in rows:
                    if r['section'] not in a['sections']:continue
                    key=tuple(r[f] for f in fields);label=r['currier'];n[key,label]+=1;folios[key,label].add(r['folio'])
                    totals[key,label]+=len(r['word']) if units=='atomic' else len(grouped_word(r['word']))
                keys={s for s,l in n if all(n[s,c]>=experiment.MIN_TOKENS and len(folios[s,c])>=experiment.MIN_FOLIOS for c in ('A','B'))}
                assert keys=={tuple(s['key']) for s in a['strata']}
                total=sum(n[s,c] for s in keys for c in ('A','B'))
                expected={c:sum((n[s,'A']+n[s,'B'])/total*totals[s,c]/n[s,c] for s in keys) for c in ('A','B')}
                assert all(abs(expected[c]-a['standardized_means'][c])<1e-12 for c in expected)
                assert abs(a['B_minus_A']-(expected['B']-expected['A']))<1e-12
                assert abs(sum(s['weight'] for s in a['strata'])-1)<1e-12
                for s in a['strata']:
                    k=tuple(s['key']);assert abs(s['weight']-(n[k,'A']+n[k,'B'])/total)<1e-12
                for c in ('A','B'):
                    assert sum(n[s,c] for s in keys)==a['included_tokens'][c]
                    assert len(set().union(*(folios[s,c] for s in keys)))==a['included_folios'][c]
                    assert abs(a['fraction_of_all_cohort_tokens'][c]-a['included_tokens'][c]/result['unadjusted'][c]['tokens'])<1e-12
        atomic=next(r for r in report['results'] if r['cohort']==cohort and r['unitization']=='atomic')['adjustments']['section+line-role+word-position']
        grouped=next(r for r in report['results'] if r['cohort']==cohort and r['unitization']=='existing-grouped')['adjustments']['section+line-role+word-position']
        contributions={};savings={}
        for c in ('A','B'):
            total=Counter()
            for s in atomic['strata']:
                subset=[r for r in rows if r['currier']==c and [r[f] for f in atomic['fields']]==s['key']]
                for r in subset:
                    for g in grouped_word(r['word']):
                        if g in GROUPS:total[g]+=s['weight']*(len(g)-1)/len(subset)
            contributions[c]=dict(total);savings[c]=sum(total.values())
            assert abs(savings[c]-(atomic['standardized_means'][c]-grouped['standardized_means'][c]))<1e-10
        assert abs(grouped['B_minus_A']-atomic['B_minus_A']-(savings['A']-savings['B']))<1e-10
        decompositions.append({'cohort':cohort,'weighted_units_saved_per_word':savings,'by_group':contributions,'grouped_minus_atomic_contrast':savings['A']-savings['B']})
    write_json(out/'validation.json',{'validated':True,'prepared_sha256':digest(p),'results':4,'checks':'Frozen provenance; independent raw-locus eligibility/original positions; unadjusted and matched means; exact common support, pooled weights and coverage; grouping saving decomposition identity. Bootstrap implementation tested separately with fixed strata and resampled folio totals.','grouping_decomposition':decompositions})
    print(json.dumps(decompositions,indent=2))

if __name__=='__main__':validate()
