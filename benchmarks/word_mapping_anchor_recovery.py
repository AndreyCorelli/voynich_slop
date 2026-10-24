"""Recovery with supplied function-word anchors versus paired unanchored search."""
import argparse
from collections import Counter,defaultdict
from concurrent.futures import ProcessPoolExecutor
from itertools import accumulate
import hashlib
import json
import math
from pathlib import Path
import random

from voynich_smt.data.corpus import digest,write_json
from voynich_smt.structural_language import StructuralLanguageModel
from voynich_smt.structural_oracle import StructuralOracle
from voynich_smt.structural_search import ProfileScorer,ProfileSearch
from voynich_smt.word_mapping.corpora import WordStream

PARENT=Path('experiments/results/word-mapping/widening-calibration')
INVENTORY=Path('experiments/results/latin-large-dictionary')
OUT=Path('experiments/results/word-mapping/anchor-recovery-calibration')
TARGETS=(500,2000,8000)
FRACTIONS=(0.,.5,1.)
SEEDS=(101,202)


def resource_entries():
    cached=json.loads((PARENT/'morphology.json').read_text())['entries']
    records=[json.loads(line) for line in (INVENTORY/'forms-100000.jsonl').open()]
    entries={}
    for record in records:
        entries[record['surface']]=[{'enclitic':enclitic,'inflections':[{'part_of_speech':pos,'features':dict(features)}]}
                                  for pos,enclitic,features in record['signatures']]
    entries.update(cached)
    return entries,records


def foundation():
    entries,records=resource_entries()
    train=WordStream.load(PARENT/'splits/train.json')
    model=StructuralLanguageModel(entries).fit(train.segments())
    counts=Counter(w for segment in train.segments() for w in segment)
    forms=[r['surface'] for r in records]
    publics={};anchor_words={}
    # Truth enters here only to supply the explicitly requested function anchors.
    # All content-word assignments remain absent from the worker inputs.
    for target in TARGETS:
        public=json.loads((PARENT/f'public/fit-{target}.json').read_text())
        truth=json.loads((PARENT/f'truth/fit-{target}.json').read_text())
        oracle=StructuralOracle(entries,truth['decoding'])
        anchors={c:w for c,w in truth['decoding'].items() if oracle.kind(w)=='fixed'}
        forms.extend(w for w in anchors.values() if w not in forms)
        publics[target]=public['segments'];anchor_words[target]=anchors
    forms=sorted(set(forms),key=lambda w:(-counts[w],w))
    profiles=[];members=[];index={};form_profile={};mass=[]
    for form in forms:
        profile=model.emissions(form)
        if profile not in index:
            index[profile]=len(profiles);profiles.append(profile);members.append([]);mass.append(0.)
        p=index[profile];members[p].append(form);form_profile[form]=p;mass[p]+=counts[form]
    write_json(OUT/'catalog.json',{'forms':forms,'profiles':profiles,'members':members,
        'training_mass':mass,'source_inventory_sha256':hashlib.sha256((INVENTORY/'forms-100000.jsonl').read_bytes()).hexdigest(),
        'additional_supplied_function_forms':sorted(set(forms)-{r['surface'] for r in records})})
    jobs=[]
    for target,segments in publics.items():
        word_counts=Counter(w for s in segments for w in s)
        keys=sorted(word_counts,key=lambda c:(-word_counts[c],c))
        if len(keys)>len(forms):raise ValueError('Insufficient distinct forms')
        initial_forms=dict(zip(keys,forms))
        ordered=sorted(anchor_words[target]);random.Random(191).shuffle(ordered)
        for fraction in FRACTIONS:
            selected=ordered[:math.ceil(len(ordered)*fraction)]
            anchors={c:anchor_words[target][c] for c in selected}
            assignments=dict(initial_forms);owners={w:c for c,w in assignments.items()}
            for c,gold in anchors.items():
                old=assignments[c];other=owners.get(gold)
                if other is not None and other!=c:
                    assignments[other]=old;owners[old]=other
                else:owners.pop(old,None)
                assignments[c]=gold;owners[gold]=c
            base={'target':target,'fraction':fraction,'segments':segments,
                'initial':{c:form_profile[w] for c,w in assignments.items()},
                'anchors':{c:form_profile[w] for c,w in anchors.items()},'anchor_forms':anchors,
                'anchor_tokens':sum(word_counts[c] for c in anchors),'anchor_types':len(anchors)}
            for seed in SEEDS:jobs.append({**base,'seed':seed})
    return model,profiles,members,mass,jobs,entries,train.identity


def worker(job,model,profiles,members,mass,steps,out):
    scorer=ProfileScorer(model,profiles,job['segments'],job['initial'])
    anchors={scorer.ids[c]:p for c,p in job['anchors'].items()}
    search=ProfileSearch(scorer,[len(m) for m in members],mass,anchors,seed=job['seed'],steps=steps)
    for _ in range(4):search.advance(math.ceil(steps/4))
    def render(assignments):
        mapping=dict(job['anchor_forms']);reserved=set(mapping.values())
        word_counts=Counter(w for s in job['segments'] for w in s)
        grouped=defaultdict(list)
        for c in scorer.keys:
            if c not in mapping:grouped[int(assignments[scorer.ids[c]])].append(c)
        for p,keys in grouped.items():
            available=[w for w in members[p] if w not in reserved]
            keys.sort(key=lambda c:(-word_counts[c],c))
            if len(available)<len(keys):raise ValueError('Cannot render injective profile map')
            mapping.update(zip(keys,available))
        if len(set(mapping.values()))!=len(mapping):raise ValueError('Rendered map is not injective')
        return mapping
    best,initial=render(search.best),render(search.initial)
    # Independent Python forward calculation checks the compiled/incremental result.
    for mapping,score in ((best,search.best_score),(initial,search.initial_score)):
        full=model.score(tuple(tuple(mapping[c] for c in s) for s in job['segments']))
        if not math.isclose(full,score,abs_tol=1e-7,rel_tol=1e-12):raise ValueError('Python full-score mismatch')
    row={k:job[k] for k in ('target','fraction','seed','anchor_tokens','anchor_types')}
    row.update({'steps':steps,'initial_score':search.initial_score,'best_score':search.best_score,
        'statistics':dict(search.statistics),'trace':search.trace,'initial_mapping':initial,'best_mapping':best,
        'supplied_anchors':job['anchor_forms']})
    label=f"{job['target']}/anchors-{job['fraction']}/seed-{job['seed']}"
    write_json(Path(out)/'runs'/label/'report.json',row)
    return row


def evaluate(rows,entries):
    result=[]
    for row in rows:
        target=row['target']
        public=json.loads((PARENT/f'public/fit-{target}.json').read_text())
        truth=json.loads((PARENT/f'truth/fit-{target}.json').read_text())
        oracle=StructuralOracle(entries,truth['decoding'])
        counts=Counter(w for s in public['segments'] for w in s)
        content={c for c,w in truth['decoding'].items() if oracle.kind(w)=='content'}
        functions={c for c,w in truth['decoding'].items() if oracle.kind(w)=='fixed'}
        def metrics(mapping):
            def subset(keys,permissive=False):
                tokens=sum(counts[c] for c in keys)
                if not tokens:return {'tokens':0}
                compatible=sum(counts[c] for c in keys if oracle.status(c,mapping[c],permissive=permissive)=='compatible')
                return {'tokens':tokens,'compatible':compatible/tokens,
                    'exact':sum(counts[c] for c in keys if mapping[c]==truth['decoding'][c])/tokens}
            return {'all':oracle.evaluate(public['segments'],mapping),
                    'content_strict':subset(content),'content_permissive':subset(content,True),
                    'functions':subset(functions)}
        result.append({k:row[k] for k in ('target','fraction','seed','anchor_tokens','anchor_types','steps','initial_score','best_score')}|
            {'initial':metrics(row['initial_mapping']),'best':metrics(row['best_mapping'])})
    return result


def run(steps=10000,workers=4,validate=False):
    model,profiles,members,mass,jobs,entries,train_sha=foundation()
    paths=[Path(__file__),Path('src/voynich_smt/structural_search.py'),Path('src/voynich_smt/structural_search_kernel.cpp'),
           Path('src/voynich_smt/structural_language.py'),Path('src/voynich_smt/structural_oracle.py')]
    protocol={'steps':steps,'targets':TARGETS,'fractions':FRACTIONS,'seeds':SEEDS,'training_sha256':train_sha,
        'catalog_sha256':digest(json.loads((OUT/'catalog.json').read_text())),
        'jobs_sha256':digest(jobs),'code_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        'objective':'unchanged morphological sequence model, capacity-constrained emission classes',
        'scope':'explicit supplied-function oracle control; unanchored paired baseline; final test unscored'}
    manifest={'protocol':protocol,'sha256':digest(protocol)}
    if validate:
        if json.loads((OUT/'manifest.json').read_text())!=manifest:raise ValueError('Protocol changed')
        old=json.loads((OUT/'report.json').read_text())
    else:
        if (OUT/'manifest.json').exists():raise ValueError('Output already exists')
        write_json(OUT/'manifest.json',manifest)
    rows=[]
    if workers==1:
        for job in jobs:
            rows.append(worker(job,model,profiles,members,mass,steps,OUT))
            print('completed',job['target'],job['fraction'],job['seed'],flush=True)
    else:
        # Independent CPU workers; every worker sees only public input and its supplied anchors.
        with ProcessPoolExecutor(max_workers=workers) as pool:
            futures=[pool.submit(worker,job,model,profiles,members,mass,steps,OUT) for job in jobs]
            for job,future in zip(jobs,futures):
                rows.append(future.result());print('completed',job['target'],job['fraction'],job['seed'],flush=True)
    report={'manifest_sha256':manifest['sha256'],'runs':len(rows),'proposals':steps*len(rows),
        'evaluations':evaluate(rows,entries),'run_sha256':[digest(row) for row in rows]}
    if validate:
        if report!=old:raise ValueError('Replay differs')
        write_json(OUT/'validation.json',{'deterministic_replay':True,'report_sha256':digest(report),'runs':len(rows)})
    else:write_json(OUT/'report.json',report)
    print('complete',len(rows),'runs',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--steps',type=int,default=10000)
    parser.add_argument('--workers',type=int,default=4);parser.add_argument('--validate',action='store_true')
    args=parser.parse_args();run(args.steps,args.workers,args.validate)
