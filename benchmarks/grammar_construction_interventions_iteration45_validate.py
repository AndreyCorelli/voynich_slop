"""Replay lattices and factorization; audit minimal revelations and wide domains."""
from collections import Counter,defaultdict
from copy import deepcopy
import numpy as np
from benchmarks.grammar_construction_interventions_iteration45 import OUT,PREVIOUS,RESERVE,load,save,digest
from voynich_smt.construction_interventions import FIELDS,domains,morphology,lattice,interventions,summarize,value


def minimal_sets(summaries):
    winners=[set(fs) for fs in interventions() if summaries['none' if not fs else '+'.join(fs)]['uniquely_correct']]
    return [s for s in winners if not any(t<s for t in winners)]


def validate():
    hashes=0
    for name in ('manifest.json','evaluation-freeze.json'):
        for p,h in load(OUT/name)['inputs'].items():assert digest(p)==h,p;hashes+=1
    data=load(PREVIOUS/'annotations-truth.json');reserve={r['sent_id'] for rows in load(RESERVE)['authors'].values() for r in rows};assert not set(data)&reserve
    lexicon=morphology(s['tokens'] for s in data.values());assert lexicon==load(OUT/'morphology-oracle.json');examples=load(OUT/'lattices.json');records=load(OUT/'interventions.json');byexample=defaultdict(dict)
    for r in records:byexample[(r['sent_id'],r['construction'],r['arm'])][r['intervention']]=r['summary']
    wide=load(OUT/'wide-lattices.json');wideindex={(r['sent_id'],r['construction'],r['arm']):r for r in wide};factorized=0;replayed=0;unachievable=[];minimum={};wide_result={};failures=[]
    for e in examples:
        tokens=data[e['sent_id']]['tokens'];ref=e['reference'];assert ref[2] in e['domains']['heads'] and ref[:2] in e['domains']['boundaries'] and ref[4] in e['domains']['predicates'];assert ref[0]<=ref[2]<=ref[1] and (ref[4] is None or ref[4]<ref[0] or ref[4]>ref[1])
        altered=deepcopy(tokens)
        for t in altered:t['head']=None;t['rel']='CORRUPTED';t['features']={'Case':'CORRUPTED'}
        for arm,mask in (('oracle_word_type',False),('hidden_case',True)):
            candidates,stages=lattice(tokens,e['prep'],e['domains'],lexicon,mask);assert candidates==e['arms'][arm]['candidates'] and stages==e['arms'][arm]['stages'];assert lattice(altered,e['prep'],e['domains'],lexicon,mask)==(candidates,stages)
            assert len({tuple(c) for c in candidates})==len(candidates)
            blocks=defaultdict(set)
            for c in candidates:blocks[tuple(c[:4])].add(c[4])
            assert all(v==set(e['domains']['predicates']) for v in blocks.values());factorized+=1
            if mask:
                candidates_set={tuple(c) for c in candidates};assert all(tuple(c[:3]+['Abl' if c[3]=='Acc' else 'Acc']+[c[4]]) in candidates_set for c in candidates)
            key=(e['sent_id'],e['construction'],arm);summaries={}
            for fs in interventions():
                k='none' if not fs else '+'.join(fs);s=summarize(candidates,ref,fs);assert s==byexample[key][k];summaries[k]=s;replayed+=1
                for f in FIELDS:
                    if f not in fs:
                        more=summarize(candidates,ref,tuple(g for g in FIELDS if g in set(fs)|{f}));assert more['remaining']<=s['remaining']
            if not summaries['none']['reference_retained']:
                failures.append(dict(sent_id=e['sent_id'],author=e['author'],construction=e['construction'],arm=arm,reference=ref,stages=stages,sentence=' '.join(t['word'] for t in tokens),reference_tokens=tokens[ref[0]:ref[1]+1]))
            minimal=minimal_sets(summaries);m=minimum.setdefault(arm,dict(minimum_facts=Counter(),minimal_sets=Counter()))
            if minimal:
                m['minimum_facts'][str(min(map(len,minimal)))]+=1
                for fs in minimal:m['minimal_sets']['none' if not fs else '+'.join(f for f in FIELDS if f in fs)]+=1
            else:m['minimum_facts']['reference_pruned']+=1
            big=wideindex[key];wc,ws=lattice(tokens,e['prep'],big['domains'],lexicon,mask);assert ws==big['stages'];assert set(map(tuple,candidates))<=set(map(tuple,wc))
            for fs in interventions():
                k='none' if not fs else '+'.join(fs);assert summarize(wc,ref,fs)==big['summaries'][k];replayed+=1
                cohort=summaries['none']['reference_retained'] and summaries['none']['remaining']>1
                if cohort:
                    out=wide_result.setdefault(f'{arm}/{k}',dict(n=0,primary_unique=0,wide_unique=0,primary_remaining=[],wide_remaining=[]));out['n']+=1;out['primary_unique']+=summaries[k]['uniquely_correct'];out['wide_unique']+=big['summaries'][k]['uniquely_correct'];out['primary_remaining'].append(summaries[k]['remaining']);out['wide_remaining'].append(big['summaries'][k]['remaining'])
    for v in wide_result.values():
        for k in ('primary_remaining','wide_remaining'):v['median_'+k]=float(np.median(v.pop(k)))
    minimum={arm:{k:dict(v) for k,v in result.items()} for arm,result in minimum.items()};save(OUT/'minimal-revelations.json',minimum);save(OUT/'wide-evaluation.json',wide_result);save(OUT/'reference-pruning-audit.json',failures);result=dict(hash_checks=hashes,examples=len(examples),matrix_replays=replayed,predicate_factorization_checks=factorized,hidden_case_symmetry_checks=len(examples),reserved_unscored=len(reserve),reference_pruned_by_arm=dict(Counter(f['arm'] for f in failures)))
    save(OUT/'validation.json',result);print(result);print('Minimum',minimum)
if __name__=='__main__':validate()
