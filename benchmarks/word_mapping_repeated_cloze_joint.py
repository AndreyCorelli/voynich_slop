"""Reserved-anchor retrieval and globally injective proposals from frozen scores."""
import hashlib
import importlib.metadata
import json
from pathlib import Path
from statistics import mean
import numpy as np
from scipy.optimize import linear_sum_assignment
from benchmarks import word_mapping_repeated_cloze as b
from benchmarks.word_mapping_repeated_cloze_analysis import GLUE
from voynich_smt.data.corpus import digest,write_json
from voynich_smt.structural_oracle import StructuralOracle


def run():
    public,anchors,selected,entries,forms,frequencies=b.prepare()
    truth=json.loads((b.anchor.PARENT/f'truth/fit-{b.TARGET}.json').read_text())
    base=json.loads((b.OUT/'report.json').read_text())
    rows=[json.loads((b.OUT/'cases'/f'{c}.json').read_text()) for c in selected]
    assert [digest(row) for row in rows]==base['case_sha256']
    oracle=StructuralOracle(entries,truth['decoding'])
    reserved=set(anchors.values())
    eligible=np.asarray([i for i,w in enumerate(forms) if w not in reserved],dtype=np.int32)
    occurrence=np.asarray([r['occurrences'] for r in rows],dtype=np.float64)
    methods=('training_frequency','no_anchors/pooled','function_only/pooled','decoded_context/pooled')
    outputs=[]
    for method in methods:
        scores=[]
        for cipher in selected:
            with np.load(b.OUT/'scores'/f'{cipher}.npz') as saved:scores.append(saved[method][eligible])
        scores=np.asarray(scores,dtype=np.float64)
        rids,cids=linear_sum_assignment(scores*occurrence[:,None],maximize=True)
        chosen={selected[r]:forms[eligible[c]] for r,c in zip(rids,cids)}
        assert len(chosen)==len(selected)==len(set(chosen.values()))
        assert not set(chosen.values()) & reserved
        per_type=[]
        for row,values in zip(rows,scores):
            cipher=row['cipher'];gold=row['gold']
            compatible={w for w in forms if oracle.status(cipher,w)=='compatible'}
            full=np.full(len(forms),-np.inf,dtype=np.float64);full[eligible]=values
            rank=b.ranking(full,forms,eligible,gold,compatible)
            per_type.append({'cipher':cipher,'gold':gold,'prediction':chosen[cipher],'gold_kind':row['gold_kind'],
                'joint_compatible':oracle.status(cipher,chosen[cipher])=='compatible','joint_exact':chosen[cipher]==gold,
                'reserved_filtered_rank':rank})
        populations={}
        for label,subset in [('known_content',[x for x in per_type if x['gold_kind']=='content']),
                             ('lexical_content_sensitivity',[x for x in per_type if x['gold_kind']=='content' and x['gold'] not in GLUE])]:
            populations[label]={'types':len(subset),'reserved_filtered_compatible_top10':sum(x['reserved_filtered_rank']['compatible_top10'] for x in subset),
                'joint_compatible':sum(x['joint_compatible'] for x in subset),'joint_exact':sum(x['joint_exact'] for x in subset)}
        outputs.append({'method':method,'populations':populations,'types':per_type})
    report={'source_report_sha256':digest(base),'candidate_count_after_anchor_reservation':len(eligible),
        'scope':'joint maximum-weight matching for 36 selected types only; all other hidden types remain undecoded; unknown pretraining exposure',
        'weighting':'mean piece log score pooled over occurrences multiplied by occurrence count; frozen independent cloze contexts',
        'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'scipy_version':importlib.metadata.version('scipy'),'results':outputs}
    path=b.OUT/'joint-report.json'
    if path.exists():
        assert json.loads(path.read_text())==report
        write_json(b.OUT/'joint-validation.json',{'deterministic_replay':True,'report_sha256':digest(report)})
    else:write_json(path,report)
    selected_result=next(row for row in outputs if row['method']=='function_only/pooled')
    mapping={**anchors,**{row['cipher']:row['prediction'] for row in selected_result['types']}}
    original=[w for s in truth['plaintext'] for w in s][:100]
    cipher=[c for s in public['segments'] for c in s][:100]
    prediction=[mapping.get(c,f'[{c}]') for c in cipher]
    lines=['# First 100 words: partial cloze assignment','',
        'Function-word answers are supplied. Jointly injective cloze proposals cover 36 repeated types; bracketed ciphertext types remain unresolved. This is not a complete decoding.',
        '', '## Original','',' '.join(original),'','## Partial assignment','',' '.join(prediction),'',
        '| Position | Original | Output | Source |','|---:|---|---|---|']
    for i,(gold,p,c) in enumerate(zip(original,prediction,cipher),1):
        source='supplied anchor' if c in anchors else 'cloze proposal' if c in mapping else 'unresolved'
        lines.append(f'| {i} | {gold} | {p} | {source} |')
    (b.OUT/'partial-first-100.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps([{k:v for k,v in row.items() if k!='types'} for row in outputs],indent=2))


if __name__=='__main__':run()
