"""Frozen fit replay, independent gold/count checks and channel-isolation audit."""
from collections import Counter
import hashlib
import json
import numpy as np
from benchmarks.grammar_cipher_relations_iteration23 import OUT,TREEBANK,RESERVE,load,KEYS,LABEL_MAP,relation_matrix,number_matrix,strings
from benchmarks.grammar_cipher_relations_iteration23_evaluate import relation_metrics,number_metrics,paired_interval,fingerprint
from benchmarks.scalable_latin_caesar import words
from benchmarks.grammar_cipher_relations_iteration23_transfer import calculate as transfer
from benchmarks.grammar_cipher_relations_iteration23_transfer_control import calculate as transfer_control
from voynich_smt.cipher_relations import ARMS,LABELS,RADIUS,views,encrypt,probabilities,decode


def source_check(data):
    byid={s['sent_id']:s for ss in data.values() for s in ss};found=set()
    for block in TREEBANK.read_text().split('\n\n'):
        lines=block.splitlines();sid=next((l.split(' = ',1)[1] for l in lines if l.startswith('# sent_id = ')),None)
        if sid not in byid:continue
        raw=[l.split('\t') for l in lines if l and not l.startswith('#') and l.split('\t')[0].isdigit()]
        kept=[r for r in raw if r[3]!='PUNCT'];index={r[0]:i for i,r in enumerate(kept)};rawindex={r[0]:r for r in raw};record=byid[sid]
        assert [words(r[1])[0] for r in kept]==record['tokens']
        edges=[];numbers=[]
        for i,r in enumerate(kept):
            head=r[6];seen=set()
            while head!='0' and head not in index:
                assert head not in seen;seen.add(head);head=rawindex[head][6]
            relation=r[7].split(':')[0]
            label=1 if relation=='nsubj' else 2 if relation in ('obj','iobj') else 3 if relation in ('amod','det') else 4 if relation=='conj' else None
            if head in index and label is not None:edges.append([i,index[head],label])
            features=dict(x.split('=',1) for x in r[5].split('|') if '=' in x)
            if features.get('Number') in ('Sing','Plur'):numbers.append([i,int(features['Number']=='Plur')])
        assert record['edges']==edges and record['numbers']==numbers;found.add(sid)
    assert found==set(byid)


def validate():
    manifest=load(OUT/'manifest.json')
    for p,h in {**manifest['inputs'],**manifest['prior_declarations'],**load(OUT/'fit-freeze.json')['inputs']}.items():assert hashlib.sha256(open(p,'rb').read()).hexdigest()==h,p
    data=load(OUT/'datasets.json');lattice=load(OUT/'morphology-lattice.json');models=load(OUT/'models.json');tuning=load(OUT/'tuning.json');saved=load(OUT/'predictions.json');evaluation=load(OUT/'evaluation.json')
    reserved={r['sent_id'] for group in load(RESERVE)['authors'].values() for r in group};assert len(reserved)==200
    groups=[{s['sent_id'] for s in ss} for ss in data.values()]
    assert all(not a&b for i,a in enumerate(groups) for j,b in enumerate(groups) if i<j)
    assert all(not group&reserved for group in groups)
    prior=set().union(*(set(strings(load(__import__('pathlib').Path(p)))) for p in manifest['prior_declarations']))
    assert all(s['sent_id'] not in prior for split in ('tune','test_jerome','test_caesar') for s in data[split])
    assert {s['author'] for s in data['train']}=={'Jerome','Palladius'} and {s['author'] for s in data['test_caesar']}=={'Caesar'}
    source_check(data)
    majority=int(np.argmax(np.bincount([y for s in data['train'] for p,y in s['numbers']],minlength=2)))
    for arm in ARMS:
        best=max(tuning[arm],key=lambda r:(r['f1'],r['threshold']));assert models[arm]['threshold']==best['threshold']
    query_count=0
    for split in ('test_jerome','test_caesar'):
        v=views(data[split],KEYS[split],lattice);predictions_by_arm={}
        for arm in ARMS:
            x,_,slices,pairs=relation_matrix(data[split],v,arm);scores=probabilities(x,models[arm]['relation'])
            rows=[r for r in saved if r['split']==split and r['arm']==arm];predictions_by_arm[arm]=rows
            for row,s,(a,b),pair in zip(rows,data[split],slices,pairs):
                assert row['sent_id']==s['sent_id']
                guessed=decode(pair,scores[a:b],models[arm]['threshold']);assert row['edges']==guessed
                assert len({e[0] for e in guessed})==len(guessed)
                assert all(c!=p and abs(c-p)<=RADIUS and 1<=label<len(LABELS) for c,p,label,confidence in guessed)
            metrics=relation_metrics(rows,data[split]);assert metrics==evaluation[split][arm]['relations']
            # Independent set accounting includes all reference edges, including
            # those outside the candidate radius.
            tp=predicted=gold=0
            for row,s in zip(rows,data[split]):
                actual=set(tuple(e[:3]) for e in row['edges']);target=set(map(tuple,s['edges']));tp+=len(actual&target);predicted+=len(actual);gold+=len(target)
            assert metrics['micro']['f1']==2*tp/max(1,predicted+gold)
            nx,ny,queries=number_matrix(data[split],v,arm);number=load(OUT/f'number-{split}-{arm}.json');guessed=np.argmax(probabilities(nx,models[arm]['number']),axis=1).tolist()
            assert number==dict(queries=queries,predicted=guessed)
            assert number_metrics(guessed,ny,majority)==evaluation[split][arm]['masked_number'];query_count+=len(queries)
            # New keys must alter token names while preserving features. Number
            # contexts are also invariant under renaming.
            other=views(data[split],710,lattice);xx,_,_,_=relation_matrix(data[split],other,arm);nn,_,_=number_matrix(data[split],other,arm)
            assert fingerprint(xx)==fingerprint(x) and fingerprint(nn)==fingerprint(nx)
        for a,b in [('repetition','geometry'),('ending_blind','repetition'),('ending_exposed','ending_blind'),('dictionary','ending_blind')]:
            assert paired_interval(predictions_by_arm[a],predictions_by_arm[b],data[split])==evaluation[split]['paired_comparisons'][f'{a}-minus-{b}']
    tm,tr=transfer(data,lattice,models)
    assert tm==load(OUT/'agreement-transfer.json') and tr==load(OUT/'agreement-transfer-predictions.json')
    assert transfer_control(data,tr)==load(OUT/'agreement-transfer-control.json')
    assert len(saved)==1000 and len(load(OUT/'rekey-checks.json'))==20
    print(f'1000 sentence/arm predictions and {query_count} Number queries replayed; source labels and frozen thresholds verified; cipher-key invariance checked; 200 reserved sentences unscored')

if __name__=='__main__':validate()
