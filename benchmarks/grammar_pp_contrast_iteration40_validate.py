"""Replay contrast scores; quantify component ablations and cluster uncertainty."""
from collections import defaultdict,Counter
from pathlib import Path
import math
import numpy as np
from benchmarks.grammar_pp_contrast_iteration40 import OUT,ROOT,RESERVE,load,save,digest,constructions,corruptions
from voynich_smt.pp_contrast import score,train


def validate():
    for filename in ('manifest.json','evaluation-freeze.json'):
        for p,h in load(OUT/filename)['inputs'].items():assert digest(p)==h,p
    manifest=load(OUT/'manifest.json');ids=manifest['split_ids'];reserve={r['sent_id'] for rows in load(RESERVE)['authors'].values() for r in rows};assert not set(sum(ids.values(),[]))&reserve
    assert not set(ids['source'])&(set(ids['Jerome'])|set(ids['Caesar']))
    data=load(OUT/'data-truth.json');model=load(OUT/'model.json');assert model==train([(data[sid],c) for sid in ids['source'] for c in constructions(data[sid])])
    rows=load(OUT/'predictions.json');matching=0;ablations={};whole={};frequencies=Counter(t['word'] for sid in ids['source'] for t in data[sid])
    for row in rows:
        tokens=data[row['sent_id']]
        for c,s in (('correct','correct_scores'),('corrupt','corrupt_scores')):assert score(model,tokens,row[c])==row[s]
        if row['family']=='attachment':
            a,b=row['correct']['head'],row['corrupt']['head'];assert tokens[a]['case']==tokens[b]['case'] and tokens[a]['pos']==tokens[b]['pos'];matching+=1
            bucket=lambda i:int(math.log2(1+frequencies[tokens[i]['word']]))
            assert abs(bucket(a)-bucket(b))<=1 and abs(b-row['correct']['prep'])<=12
        elif row['family']=='morphology':
            assert {k:v for k,v in row['correct'].items() if k!='case'}=={k:v for k,v in row['corrupt'].items() if k!='case'}
        else:
            assert row['correct']['head']==row['corrupt']['head'] and row['correct']['prep']==row['corrupt']['prep']
            assert abs(row['correct']['left']-row['corrupt']['left'])+abs(row['correct']['right']-row['corrupt']['right'])==1
    def value(row,side,arm):
        parts=row[side+'_scores']['components']
        if arm=='structural':return row[side+'_scores']['structural']
        if arm=='distance_only':return parts['distance']
        if arm=='boundary_only':return parts['boundary']
        return sum(v for k,v in parts.items() if k!=arm.removeprefix('without_'))
    arms=('structural','distance_only','boundary_only','without_government','without_distance','without_boundary','without_agreement')
    for author in ('Jerome','Caesar'):
        for family in ('attachment','morphology','boundary'):
            selected=[r for r in rows if (r['author'],r['family'])==(author,family)]
            for arm in arms:
                groups=defaultdict(list)
                for r in selected:groups[(r['sent_id'],r['construction'])].append(value(r,'correct',arm)>value(r,'corrupt',arm)+1e-12)
                bysent=defaultdict(list)
                for (sid,_),v in groups.items():bysent[sid].append(np.mean(v))
                sentence_ids=sorted(bysent);numerator=np.array([sum(bysent[s]) for s in sentence_ids]);denominator=np.array([len(bysent[s]) for s in sentence_ids]);rng=np.random.default_rng(40001);draws=rng.integers(0,len(sentence_ids),(10000,len(sentence_ids)));rates=numerator[draws].sum(axis=1)/denominator[draws].sum(axis=1)
                ablations[f'{author}/{family}/{arm}']=dict(strict_construction_mean=float(numerator.sum()/denominator.sum()),ci95=np.quantile(rates,[.025,.975]).tolist(),sentences=len(sentence_ids))
        groups=defaultdict(list)
        for row in rows:
            if row['author']==author:groups[(row['sent_id'],row['construction'])].append(row)
        eligible={k:v for k,v in groups.items() if {r['family'] for r in v}=={'attachment','morphology','boundary'}}
        for arm in arms:
            whole[f'{author}/{arm}']=dict(eligible=len(eligible),strictly_correct=sum(all(value(r,'correct',arm)>value(r,'corrupt',arm)+1e-12 for r in v) for v in eligible.values()))
    save(OUT/'component-audit.json',dict(note='Descriptive component ablations computed after primary outcomes; no weight tuning or policy selection. Cluster intervals resample eligible sentences; boundary negatives equally weighted within construction. Conditional on annotation-derived contrasts.',families=ablations,whole_construction=whole))
    failures=[]
    for r in rows:
        margin=r['correct_scores']['structural']-r['corrupt_scores']['structural']
        if margin<=1e-12:
            tokens=data[r['sent_id']];failures.append(dict(**r,sentence=' '.join(t['word'] for t in tokens),margin=margin,component_margins={k:r['correct_scores']['components'][k]-r['corrupt_scores']['components'][k] for k in r['correct_scores']['components']}))
    save(OUT/'failure-audit.json',failures);result=dict(replayed_pairs=len(rows),matched_attachment_pairs=matching,source_constructions=manifest['source_constructions'],reserved_unscored=len(reserve),failures=len(failures));save(OUT/'validation.json',result);print(result)
    print(whole)
if __name__=='__main__':validate()
