"""Stronger assisted control: all function anchors plus known-content candidates."""
from concurrent.futures import ProcessPoolExecutor
from collections import Counter
import hashlib
import json
from pathlib import Path
from benchmarks import word_mapping_anchor_recovery as b
from voynich_smt.data.corpus import digest,write_json
from voynich_smt.structural_language import UNK

OUT=b.OUT/'known-content-only'


def run(validate=False):
    model,profiles,members,mass,jobs,entries,train_sha=b.foundation()
    steps=10000
    filtered=[]
    for job in jobs:
        if job['fraction']!=1:continue
        anchored=set(job['anchor_forms'].values())
        reduced=[];weights=[]
        for p,group in enumerate(members):
            content=profiles[p]!=(UNK,) and profiles[p][0][0]!='FUNCTION'
            kept=list(group) if content else [w for w in group if w in anchored]
            reduced.append(kept);weights.append(mass[p] if content else 0.)
        forms=[w for group in reduced for w in group if w not in anchored]
        training_counts=Counter(w for s in b.WordStream.load(b.PARENT/'splits/train.json').segments() for w in s)
        forms.sort(key=lambda w:(-training_counts[w],w))
        word_counts=Counter(c for s in job['segments'] for c in s)
        keys=sorted((c for c in word_counts if c not in job['anchors']),key=lambda c:(-word_counts[c],c))
        if len(keys)>len(forms):raise ValueError('Insufficient known-content candidates')
        ids={w:p for p,group in enumerate(reduced) for w in group}
        initial={**job['anchors'],**{c:ids[w] for c,w in zip(keys,forms)}}
        filtered.append(({**job,'initial':initial},reduced,weights))
    protocol={'steps':steps,'training_sha256':train_sha,'jobs_sha256':digest([j for j,_,_ in filtered]),
        'scope':'all function anchors supplied; unknown and unanchored function candidates forbidden; no content truth supplied',
        'code_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(__file__),Path(b.__file__),Path('src/voynich_smt/structural_search.py'),Path('src/voynich_smt/structural_search_kernel.cpp'))}}
    manifest={'protocol':protocol,'sha256':digest(protocol)}
    if validate:
        assert json.loads((OUT/'manifest.json').read_text())==manifest
        old=json.loads((OUT/'report.json').read_text())
    else:
        if (OUT/'manifest.json').exists():raise ValueError('Output exists')
        write_json(OUT/'manifest.json',manifest)
    with ProcessPoolExecutor(max_workers=4) as pool:
        futures=[pool.submit(b.worker,j,model,profiles,m,w,steps,OUT) for j,m,w in filtered]
        rows=[]
        for (job,_,_),future in zip(filtered,futures):
            rows.append(future.result());print('known-content completed',job['target'],job['seed'],flush=True)
    report={'manifest_sha256':manifest['sha256'],'proposals':steps*len(rows),
        'evaluations':b.evaluate(rows,entries),'run_sha256':[digest(row) for row in rows]}
    if validate:
        assert report==old
        write_json(OUT/'validation.json',{'deterministic_replay':True,'report_sha256':digest(report),'runs':len(rows)})
    else:write_json(OUT/'report.json',report)


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--validate',action='store_true');a=p.parse_args();run(a.validate)
