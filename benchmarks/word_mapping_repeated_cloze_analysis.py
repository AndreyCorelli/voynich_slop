"""Paired retrieval analysis, including a post-hoc copula/glue-word sensitivity."""
from collections import defaultdict
import hashlib
import json
from pathlib import Path
from benchmarks import word_mapping_repeated_cloze as b
from voynich_smt.data.corpus import digest,write_json

# A sensitivity category chosen after primary results: not an extra scoring rule.
GLUE=frozenset({'non','ita','sum','es','est','sumus','estis','sunt','esse',
                'eram','eras','erat','eramus','eratis','erant','ero','eris','erit','erimus','eritis','erunt',
                'sim','sis','sit','simus','sitis','sint','essem','esses','esset','essemus','essetis','essent',
                'fui','fuisti','fuit','fuimus','fuistis','fuerunt','fuisse'})


def run():
    report=json.loads((b.OUT/'report.json').read_text())
    manifest=json.loads((b.OUT/'manifest.json').read_text())
    rows=[json.loads((b.OUT/'cases'/f'{c}.json').read_text()) for c in manifest['protocol']['targets']]
    assert [digest(row) for row in rows]==report['case_sha256']
    groups={'known_content':[r for r in rows if r['gold_kind']=='content'],
            'lexical_content_sensitivity':[r for r in rows if r['gold_kind']=='content' and r['gold'] not in GLUE],
            'frequent_known':[r for r in rows[:18] if r['gold_kind']=='content'],
            'random_known':[r for r in rows[18:] if r['gold_kind']=='content']}
    comparisons=[]
    for population,selected in groups.items():
        for candidates in ('all_candidates','content_candidates'):
            metrics={}
            for label in ('training_frequency','no_anchors/pooled','function_only/first_occurrence','function_only/pooled','decoded_context/pooled'):
                values=[r['rankings'][label][candidates] for r in selected]
                metrics[label]={key:sum(v[key] for v in values) for key in ('compatible_top1','compatible_top10','exact_top1','exact_top10')}
            paired={}
            for comparison in ('training_frequency','no_anchors/pooled','function_only/first_occurrence'):
                pairs=[(r['rankings']['function_only/pooled'][candidates]['compatible_top10'],r['rankings'][comparison][candidates]['compatible_top10']) for r in selected]
                paired[comparison]={'wins':sum(a and not c for a,c in pairs),'losses':sum(c and not a for a,c in pairs),'both':sum(a and c for a,c in pairs)}
            comparisons.append({'population':population,'candidate_set':candidates,'types':len(selected),'metrics':metrics,'paired_top10':paired})
    result={'report_sha256':digest(report),'posthoc_excluded_glue_forms':sorted(GLUE),
            'comparisons':comparisons,'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    write_json(b.OUT/'analysis.json',result)
    lines=['# Cloze candidate examples','',
        'Function-word anchors supplied; all other words masked. Every occurrence of each type is pooled. These are proposals, not a recovered dictionary.',
        '', '| Original | Occurrences | Function-context top 5 content candidates | Exact rank | Compatible in top 10 |',
        '|---|---:|---|---:|:---:|']
    for row in rows:
        values=row['rankings']['function_only/pooled']['content_candidates']
        lines.append(f"| {row['gold']} | {row['occurrences']} | {', '.join(v['word'] for v in values['top10'][:5])} | {values['gold_rank'] if values['gold_rank'] is not None else 'absent'} | {'yes' if values['compatible_top10'] else 'no'} |")
    (b.OUT/'examples.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps(comparisons,indent=2))


if __name__=='__main__':run()
