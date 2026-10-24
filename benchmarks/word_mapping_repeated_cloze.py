"""100,000-candidate cloze retrieval with supplied function-word context."""
import argparse
from collections import Counter,defaultdict
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path
import random
from statistics import mean

import numpy as np
from benchmarks import word_mapping_anchor_recovery as anchor
from benchmarks.word_mapping_neural_model import DEFAULT_MODEL,file_hashes
from voynich_smt.data.corpus import digest,write_json
from voynich_smt.neural_scoring import WholeWordScorer
from voynich_smt.neural_cloze import ClozeCandidateBank,RepeatedCloze
from voynich_smt.structural_oracle import StructuralOracle
from voynich_smt.word_mapping.corpora import WordStream

OUT=Path('experiments/results/word-mapping/repeated-cloze-calibration')
TARGET=2000
CASES=36


def prepare():
    public=json.loads((anchor.PARENT/f'public/fit-{TARGET}.json').read_text())
    supplied=json.loads((anchor.OUT/f'runs/{TARGET}/anchors-1.0/seed-101/report.json').read_text())['supplied_anchors']
    counts=Counter(c for s in public['segments'] for c in s)
    repeated=sorted((c for c,n in counts.items() if n>=3 and c not in supplied),key=lambda c:(-counts[c],c))
    top=repeated[:CASES//2];remaining=[c for c in repeated if c not in top]
    if len(remaining)<CASES-len(top):raise ValueError('Insufficient repeated non-anchor types')
    targets=top+random.Random(417).sample(remaining,CASES-len(top))
    entries,records=anchor.resource_entries()
    forms=[r['surface'] for r in records]
    train=WordStream.load(anchor.PARENT/'splits/train.json')
    frequencies=Counter(w for s in train.segments() for w in s)
    return public,supplied,targets,entries,forms,frequencies


def ranking(scores,forms,eligible,gold,compatible):
    indices=np.asarray(eligible,dtype=np.int32)
    # Stable frozen inventory order resolves exact numeric ties.
    order=indices[np.argsort(-scores[indices],kind='stable')]
    lookup={forms[i]:int(rank) for rank,i in enumerate(order,1)}
    compatible_ranks=[lookup[w] for w in compatible if w in lookup]
    best=min(compatible_ranks) if compatible_ranks else None
    return {'gold_rank':lookup.get(gold),'best_compatible_rank':best,
        'exact_top1':lookup.get(gold)==1,'exact_top10':lookup.get(gold) is not None and lookup[gold]<=10,
        'compatible_top1':best==1,'compatible_top10':best is not None and best<=10,
        'top10':[{'word':forms[i],'score':float(scores[i]),'compatible':forms[i] in compatible} for i in order[:10]]}


def evaluate_case(case, scores,forms,eligible,entries,truth):
    cipher=case['cipher'];gold=truth['decoding'][cipher]
    oracle=StructuralOracle(entries,{cipher:gold})
    # Morphology unknown forms admit only exact identity, not assumed compatibility.
    compatible={w for w in forms if oracle.status(cipher,w)=='compatible'}
    content=np.asarray([i for i in eligible if oracle.kind(forms[i])=='content'],dtype=np.int32)
    metrics={}
    for label,values in scores.items():
        metrics[label]={'all_candidates':ranking(values,forms,eligible,gold,compatible),
                        'content_candidates':ranking(values,forms,content,gold,compatible)}
    return {**case,'gold':gold,'gold_kind':oracle.kind(gold),'gold_in_candidates':gold in {forms[i] for i in eligible},
            'compatible_candidate_count':len(compatible & {forms[i] for i in eligible}),'rankings':metrics}


def summarize(rows):
    groups=defaultdict(list)
    for row in rows:
        for metric,candidates in row['rankings'].items():
            for candidate_set,values in candidates.items():
                groups[metric,candidate_set,'all_selected'].append(values)
                if row['gold_kind']=='content':groups[metric,candidate_set,'known_content'].append(values)
    return [{'metric':metric,'candidates':candidate_set,'population':population,'types':len(values),
             **{key:mean(v[key] for v in values) for key in ('exact_top1','exact_top10','compatible_top1','compatible_top10')}}
            for (metric,candidate_set,population),values in sorted(groups.items())]


def run(resume=False,validate=False):
    public,supplied,targets,entries,forms,frequencies=prepare()
    model_root=DEFAULT_MODEL
    asset=json.loads((model_root/'manifest.json').read_text())
    if digest(asset['protocol'])!=asset['sha256'] or file_hashes(model_root)!=asset['protocol']['files_sha256']:
        raise ValueError('Pinned neural assets changed')
    paths=[Path(__file__),Path('src/voynich_smt/neural_cloze.py'),Path('src/voynich_smt/neural_scoring.py'),Path(anchor.__file__),Path('src/voynich_smt/structural_oracle.py')]
    protocol={'version':1,'target':TARGET,'targets':targets,'public_sha256':digest(public),'anchors_sha256':digest(supplied),
        'inventory_sha256':hashlib.sha256((anchor.INVENTORY/'forms-100000.jsonl').read_bytes()).hexdigest(),
        'training_frequency_sha256':digest(dict(frequencies)), 'model_sha256':asset['sha256'],'radius':12,
        'candidate_scoring':'every hypothesized subword length; target spelling absent from all contexts; other hidden words occupy one mask; mean log probability per piece pooled across all occurrences',
        'contexts':['no_anchors','function_only','decoded_context'],
        'selection':'public counts>=3; 18 highest counts and 18 seeded random other non-anchor types; no target morphology or gold inclusion used',
        'candidate_count':len(forms),'batch_size':16,'threads':4,'scope':'oracle function anchors; decoded-context positive control; no search, no final-test evaluation; pretrained Caesar exposure unknown',
        'packages':{name:importlib.metadata.version(name) for name in ('torch','transformers','tokenizers','numpy')},
        'code_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
    manifest={'protocol':protocol,'sha256':digest(protocol)}
    if (OUT/'manifest.json').exists():
        if not (resume or validate) or json.loads((OUT/'manifest.json').read_text())!=manifest:raise ValueError('Output exists or protocol differs')
    elif validate:raise ValueError('Missing experiment')
    else:write_json(OUT/'manifest.json',manifest)
    scorer=WholeWordScorer.load(model_root/'inference',batch_size=16,threads=4)
    bank=ClozeCandidateBank(scorer.tokenizer,forms)
    cloze=RepeatedCloze(scorer,bank,radius=12)
    eligible=[i for i in range(len(forms)) if i not in set(bank.excluded)]
    frequency=np.asarray([math.log(frequencies[w]+.1) for w in forms],dtype=np.float64)
    # Gold is loaded only for explicit decoded-context control and subsequent evaluation.
    truth=json.loads((anchor.PARENT/f'truth/fit-{TARGET}.json').read_text())
    rows=[]
    for case_number,cipher in enumerate(targets,1):
        path=OUT/'cases'/f'{cipher}.json'
        if path.exists() and resume and not validate:
            saved=json.loads(path.read_text());rows.append(saved);continue
        outputs={'training_frequency':frequency};occurrences=None
        for label,visible in [('no_anchors',{}),('function_only',supplied),
                              ('decoded_context',{c:w for c,w in truth['decoding'].items() if c!=cipher})]:
            result=cloze.rank_scores(public['segments'],cipher,visible)
            for aggregate in ('pooled','first_occurrence'):outputs[f'{label}/{aggregate}']=result[aggregate]
            occurrences=result['occurrences']
        # Scores preserved for independent rank/metric regeneration.
        if not validate:
            (OUT/'scores').mkdir(parents=True,exist_ok=True)
            np.savez_compressed(OUT/'scores'/f'{cipher}.npz',**outputs)
        else:
            with np.load(OUT/'scores'/f'{cipher}.npz') as original:
                for label,values in outputs.items():
                    if not np.allclose(original[label],values,atol=1e-6,rtol=0,equal_nan=True):raise ValueError('Neural replay score mismatch')
        case=evaluate_case({'cipher':cipher,'occurrences':occurrences},outputs,forms,eligible,entries,truth)
        if validate:
            if json.loads(path.read_text())!=case:raise ValueError('Neural rank replay differs')
        else:write_json(path,case)
        rows.append(case)
        print('completed',case_number,'/',len(targets),cipher,'occurrences',occurrences,'gold',case['gold'],flush=True)
    report={'manifest_sha256':manifest['sha256'],'types':len(rows),'candidate_count':len(forms),
        'excluded_candidates':[forms[i] for i in bank.excluded],
        'candidate_piece_lengths':{str(n):len(indices) for n,(indices,_) in bank.groups.items()},
        'total_target_occurrences':sum(r['occurrences'] for r in rows),
        'known_content_types':sum(r['gold_kind']=='content' for r in rows),'gold_covered_types':sum(r['gold_in_candidates'] for r in rows),
        'summary':summarize(rows),'case_sha256':[digest(row) for row in rows]}
    if validate:
        if json.loads((OUT/'report.json').read_text())!=report:raise ValueError('Neural report replay differs')
        write_json(OUT/'validation.json',{'neural_replay':True,'report_sha256':digest(report),'types':len(rows),'tolerance':1e-6})
    else:write_json(OUT/'report.json',report)
    print(json.dumps(report,indent=2),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--resume',action='store_true');parser.add_argument('--validate',action='store_true')
    args=parser.parse_args();run(args.resume,args.validate)
