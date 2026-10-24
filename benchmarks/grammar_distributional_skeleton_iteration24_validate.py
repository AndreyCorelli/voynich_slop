"""Frozen replay, independent forests/fragment checks and source isolation."""
from collections import Counter
import hashlib
from pathlib import Path
import numpy as np
from benchmarks.grammar_distributional_skeleton_iteration24 import (OUT,PREVIOUS,TREEBANK,RESERVE,ARMS,SEEDS,load,strings,phase_views,
    relation_matrix,fit_readouts,calibrate)
from benchmarks.grammar_distributional_skeleton_iteration24_evaluate import score_phase,fragments
from benchmarks.grammar_distributional_skeleton_iteration24_diagnostics import calculate as diagnose
from benchmarks.grammar_distributional_skeleton_iteration24_alignment import calculate as align
from benchmarks.scalable_latin_caesar import words
from voynich_smt.distributional_grammar import observations,fit_prototypes,attach_profiles,consensus
from voynich_smt.cipher_relations import probabilities


def source_check(data):
    lookup={s['sent_id']:s for ss in data.values() for s in ss};found=set()
    for block in TREEBANK.read_text().split('\n\n'):
        lines=block.splitlines();sid=next((l.split(' = ',1)[1] for l in lines if l.startswith('# sent_id = ')),None)
        if sid not in lookup:continue
        s=lookup[sid];raw=[l.split('\t') for l in lines if l and not l.startswith('#') and l.split('\t')[0].isdigit()];kept=[r for r in raw if r[3]!='PUNCT']
        assert [words(r[1])[0] for r in kept]==s['tokens'];found.add(sid)
        if 'properties' not in s:assert 'edges' not in s;continue
        fs=[dict(x.split('=',1) for x in r[5].split('|') if '=' in x) for r in kept]
        assert s['properties']==dict(upos=[r[3] for r in kept],case=[f.get('Case') for f in fs],number=[f.get('Number') for f in fs])
        positions={r[0]:i for i,r in enumerate(kept)};byid={r[0]:r for r in raw};edges=[]
        for c,r in enumerate(kept):
            h=r[6];seen=set()
            while h!='0' and h not in positions:
                assert h not in seen;seen.add(h);h=byid[h][6]
            label={'nsubj':1,'obj':2,'iobj':2,'amod':3,'det':3,'conj':4}.get(r[7].split(':')[0])
            if h in positions and label is not None:edges.append([c,positions[h],label])
        assert edges==s['edges']
    assert found==set(lookup)


def check_rows(rows,data,models):
    lookup={s['sent_id']:s for ss in data.values() for s in ss}
    for r in rows:
        s=lookup[r['sent_id']];edges=r['edges'];heads={e[0]:e[1] for e in edges};assert len(heads)==len(edges)
        policy=models[r['arm']]['operating'][r['mode']]
        if not policy['enabled']:assert edges==[]
        for c,p,label,confidence,margin in edges:
            assert 0<=c<len(s['tokens']) and 0<=p<len(s['tokens']) and c!=p and 1<=label<=4
            assert confidence>=policy['threshold'] and margin>=policy['margin']
        for c in heads:
            visited=set();p=c
            while p in heads:
                assert p not in visited;visited.add(p);p=heads[p]
        independent={(a[0],a[1],b[0]) for a in edges for b in edges if a[1]==b[1] and a[2]==1 and b[2]==2 and a[0]!=b[0]}
        assert independent==fragments(edges)


def validate():
    manifest=load(OUT/'manifest.json')
    for p,h in {**manifest['inputs'],**manifest['prior_declarations'],**load(OUT/'fit-freeze.json')['inputs']}.items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h,p
    data=load(OUT/'datasets.json');lattice=load(OUT/'morphology-lattice.json');prototypes=load(OUT/'prototypes.json');models=load(OUT/'models.json');readouts=load(OUT/'readouts.json')
    reserved={r['sent_id'] for ss in load(RESERVE)['authors'].values() for r in ss};assert len(reserved)==200
    groups=[{s['sent_id'] for s in ss} for ss in data.values()]
    assert all(not a&b for i,a in enumerate(groups) for j,b in enumerate(groups) if i<j) and all(not g&reserved for g in groups)
    prior=set().union(*(set(strings(load(Path(p)))) for p in manifest['prior_declarations']))
    assert all(s['sent_id'] not in prior for split,ss in data.items() if split!='train' for s in ss)
    previous={s['sent_id']:s for s in load(PREVIOUS/'datasets.json')['train']}
    assert all(s['tokens']==previous[s['sent_id']]['tokens'] and s['edges']==previous[s['sent_id']]['edges'] for s in data['train'])
    assert all('edges' not in s and 'properties' not in s for split,ss in data.items() if split.startswith('background') for s in ss)
    assert all(s['author']!='Caesar' for split in ('train','tune') for s in data[split]);source_check(data)
    raw,_=phase_views(data,'train',lattice);tune,tune_offset=phase_views(data,'tune',lattice)
    calibration=load(OUT/'calibration.json')
    for arm in ARMS:
        if arm in prototypes:
            fitted=fit_prototypes(observations(raw,shuffle=arm=='shuffled_profiles'));assert fitted==prototypes[arm]
            vv=attach_profiles(raw,fitted,shuffle=arm=='shuffled_profiles');tv=attach_profiles(tune,fitted,shuffle=arm=='shuffled_profiles')[tune_offset:]
        else:vv=raw;tv=tune[tune_offset:]
        if arm!='dictionary':assert fit_readouts(data['train'],vv,arm)==readouts[arm]
        x,y,slices,pairs=relation_matrix(data['train'],vv,arm)
        for seed,bag,member in zip(SEEDS,models[arm]['bags'],models[arm]['members']):
            assert np.random.default_rng(seed).integers(len(data['train']),size=len(data['train'])).tolist()==bag
            labels=np.concatenate([np.asarray(y)[a:b] for i in bag for a,b in [slices[i]]])
            assert np.bincount(labels,minlength=5).tolist()==member['training_class_counts']
        tx,_,ts,tp=relation_matrix(data['tune'],tv,arm);p=[probabilities(tx,m) for m in models[arm]['members']]
        agreed=[consensus(pair,[v[a:b] for v in p]) for (a,b),pair in zip(ts,tp)];grid,policies=calibrate(agreed,data['tune'])
        assert calibration[arm]==dict(grid=grid,consensus=agreed) and models[arm]['operating']==policies
    saved=load(OUT/'predictions.json');allrows=[];result=load(OUT/'evaluation.json')
    for split in ('test_jerome','test_caesar'):
        scores,rows,hashes=score_phase(data,split,lattice,models,prototypes,readouts);allrows.extend(rows)
        assert scores==result[split];check_rows(rows,data,models)
        _,other,otherhash=score_phase(data,split,lattice,models,prototypes,readouts,key=607)
        assert hashes==otherhash and rows==other
        rekey=next(r for r in load(OUT/'rekey-checks.json') if r['split']==split);assert rekey['matrices']==hashes
    assert allrows==saved and len(saved)==3200
    assert diagnose(data,lattice,prototypes)==load(OUT/'class-diagnostics.json')
    assert align(data,lattice,prototypes,readouts)==load(OUT/'alignment-diagnostic.json')
    print('3200 sentence/arm/policy outputs replayed; train-only prototypes, bootstrap members and tuning calibration verified; all outputs acyclic; fresh data and 200-sentence reservation disjoint')

if __name__=='__main__':validate()
