"""Repeat-enriched matched training; ordinary pilot retained unchanged."""
import argparse
from collections import Counter,defaultdict
import hashlib
import json
from pathlib import Path
import random
from benchmarks import word_mapping_repeat_identity as experiment
from voynich_smt.data.corpus import digest,write_json
from voynich_smt.structural_oracle import StructuralOracle

OUT=Path('experiments/results/word-mapping/repeat-identity-enriched-calibration')

def examples_for(segments,entries,cloze,count,seed):
    rng=random.Random(seed);oracle=StructuralOracle(entries,{})
    anchors={w:w for s in segments for w in s if oracle.kind(w)=='fixed'}
    lexical={w for s in segments for w in s if oracle.kind(w)=='content' and w not in experiment.old.GLUE}
    pools=[defaultdict(list) for _ in range(3)]
    for si,s in enumerate(segments):
        for center,target in enumerate(s):
            if target not in lexical:continue
            pools[2][target].append((si,center))
            counts=Counter(s[max(0,center-12):min(len(s),center+13)])
            if counts[target]>=2:pools[0][target].append((si,center))
            if any(n>=2 and w!=target and w not in anchors for w,n in counts.items()):pools[1][target].append((si,center))
    if any(not pool for pool in pools):raise ValueError('Missing repetition training population')
    target_lists=[sorted(pool) for pool in pools];examples=[]
    for index in range(count):
        category=index%3;target=rng.choice(target_lists[category]);si,center=rng.choice(pools[category][target]);s=segments[si]
        fraction=rng.choice((0.,.1,.25,.5))
        visible=experiment.old.scaffold({w:w for w in s},anchors,target,fraction)
        # Preserve a repeated hidden witness in enriched categories. Both arms
        # receive the identical visible scaffold and masked inputs.
        window=s[max(0,center-12):min(len(s),center+13)]
        if category==1:
            witnesses=sorted(w for w,n in Counter(window).items() if n>=2 and w!=target and w not in anchors)
            visible.pop(rng.choice(witnesses),None)
        cloze.seed=seed+index*7919
        labels=cloze.visible_ids(target)
        ids,positions,identity=cloze.job(s,target,center,visible,len(labels))
        examples.append({'ids':ids,'positions':list(positions),'identity':identity,'labels':labels,'target':target,
            'segment':si,'center':center,'fraction':fraction,'category':('repeated_target','repeated_other','ordinary')[category]})
    return examples

def run(steps,evaluate=False,replay=False):
    experiment.OUT=OUT;experiment.examples_for=examples_for
    supplemental={'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'sampler':'one third repeated target, one third other repeated hidden type, one third ordinary lexical target; uniform types within category; repeated-other witness kept hidden',
        'seed':941,'steps':steps}
    path=OUT/'sampling-manifest.json'
    if evaluate or replay:
        assert json.loads(path.read_text())==supplemental
    else:
        if path.exists():raise ValueError('Existing enriched experiment')
        write_json(path,supplemental);experiment.train(steps)
    experiment.evaluate(replay)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--steps',type=int,default=400);p.add_argument('--evaluate',action='store_true');p.add_argument('--validate',action='store_true');a=p.parse_args();run(a.steps,a.evaluate,a.validate)
