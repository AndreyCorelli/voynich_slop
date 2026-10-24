"""Stress the frozen SV agreement diagnostic without selecting noise or settings."""
from pathlib import Path
from collections import defaultdict
import numpy as np
from benchmarks.grammar_relational_compatibility_iteration46 import OUT as PREVIOUS,SOURCE,ROOT,RESERVE,load,save,digest
from voynich_smt.construction_interventions import readings_key
from voynich_smt.relational_compatibility import sv_domains,sv_lattice
from voynich_smt.morphology_stress import schedule,perturb,encode,link_summary
OUT=ROOT/'iteration47'
RATES=(0.,.1,.25,.5,1.)
MODES=('extra','masked','deleted','substituted')
SEEDS=tuple(range(47001,47006))


def run():
    assert not OUT.exists()
    for p,h in load(PREVIOUS/'verification-manifest.json')['inputs'].items():assert digest(p)==h,p
    data=load(SOURCE);examples=load(PREVIOUS/'sv-lattices.json');lexicon=load(PREVIOUS/'sv-morphology-oracle.json');ids=sorted({e['sent_id'] for e in examples});reserve={r['sent_id'] for rows in load(RESERVE)['authors'].values() for r in rows};assert not set(ids)&reserve;keys={readings_key(t) for sid in ids for t in data[sid]['tokens']};plans={str(seed):schedule(lexicon,keys,seed) for seed in SEEDS}
    OUT.mkdir();paths=[Path(__file__),Path('src/voynich_smt/morphology_stress.py'),Path('src/voynich_smt/relational_compatibility.py'),PREVIOUS/'verification-manifest.json',PREVIOUS/'sv-lattices.json',PREVIOUS/'sv-morphology-oracle.json',PREVIOUS/'sv-wrong-fact-probes.json',SOURCE,RESERVE]
    save(OUT/'manifest.json',dict(inputs={str(p):digest(p) for p in paths},rates=RATES,modes=MODES,seeds=SEEDS,eligible_types=len(plans[str(SEEDS[0])]['order']),active_sentence_keys=len(keys),sentences=ids,
        scope='Frozen326 selected overt-subject examples from iteration46 and same oracle word-type morphology. No new source selection, old target-query or reserve scoring. No optimizer/training/setting selection.',
        channel='Perturb Number/Person only; Case/VerbForm/POS unchanged. Noun/propernoun Person3 retained as category rule. Perturbations shared by every occurrence of selected word/POS type. Eligibility requires a relevant nominal/finite reading that can yield a genuinely new number/person support state.',
        schedule='Five seeded type orders, nestedfloor(rate*eligible_types); one reference-independent original/false variant per type, same across rates and modes. Uses dictionary and observed word/POS keys only, no reference link or token-specific morphology.',
        extra='Retain every original reading and add one selected false number/person reading.',masked='Mask number/person in selected types (keep noun third person), expanding uncertainty.',deleted='Remove the selected original reading, possibly deleting the last role-eligible reading.',substituted='Replace that same original reading with exactly the false reading used in extra.',
        evaluation='Matched raw-vs-agreement link sets, exact reading vs link survival, unique correct/false, empty sets, fixed270 clean-common-ambiguous cohort. Reuse exact487 wrong-token probes from iteration46 and condition rejection on viable reference support. Separate source authors. Five perturbations reuse same examples, not independent extra sentences.'))
    save(OUT/'schedules.json',plans);save(OUT/'prediction-freeze.json',dict(inputs={str(p):digest(p) for p in OUT.glob('*.json')}));index=[]
    for seed in SEEDS:
        for mode in MODES:
            for rate in RATES:
                noisy,selected=perturb(lexicon,plans[str(seed)],rate,mode);pred={}
                for sid in ids:
                    domain=sv_domains(data[sid]['tokens'],noisy);pred[sid]={arm:encode(sv_lattice(domain,arm)) for arm in ('none','agreement')}
                filename=f'predictions-{seed}-{mode}-{rate}.json';save(OUT/filename,dict(seed=seed,mode=mode,rate=rate,selected_types=len(selected),sentences=pred));index.append(filename)
        print('Predicted seed',seed,flush=True)
    save(OUT/'prediction-index.json',index);save(OUT/'evaluation-freeze.json',dict(inputs={str(p):digest(p) for p in OUT.glob('*.json')}));evaluate()


def evaluate():
    examples=load(PREVIOUS/'sv-lattices.json');probes=[r for r in load(PREVIOUS/'sv-wrong-fact-probes.json') if r['arm']=='none'];byexample=defaultdict(list)
    for r in probes:byexample[r['sent_id'],r['subject'],r['predicate']].append(r)
    common={(e['sent_id'],e['subject'],e['predicate']) for e in examples if e['arms']['none']['summaries']['none']['reference_retained'] and e['arms']['agreement']['summaries']['none']['reference_retained'] and e['arms']['none']['summaries']['none']['links']>1};cells=[]
    for filename in load(OUT/'prediction-index.json'):
        predictions=load(OUT/filename);groups={}
        for author in ('pooled','Cicero','Palladius'):
            for cohort in ('all','clean_ambiguous'):
                chosen=[e for e in examples if (author=='pooled' or e['author']==author) and (cohort=='all' or (e['sent_id'],e['subject'],e['predicate']) in common)];result={}
                for arm in ('none','agreement'):
                    scores=[link_summary(predictions['sentences'][e['sent_id']][arm],e['reference']) for e in chosen];result[arm]=dict(n=len(scores),reference_exact=sum(s['reference_exact'] for s in scores),reference_link=sum(s['reference_link'] for s in scores),unique_correct=sum(s['unique_correct'] for s in scores),false_unique=sum(s['false_unique'] for s in scores),empty=sum(s['links']==0 for s in scores),mean_links=float(np.mean([s['links'] for s in scores])) if scores else None,new_predicates=sum(s['new_opposite']['subject'] for s in scores),new_subjects=sum(s['new_opposite']['predicate'] for s in scores))
                groups[f'{author}/{cohort}']=result
        wrong={f:dict(n=0,raw_feasible=0,agreement_feasible=0,covered_raw_feasible=0,covered_rejected=0) for f in ('subject','predicate')}
        for e in examples:
            pairs={arm:{tuple(c[:2]) for c in predictions['sentences'][e['sent_id']][arm]} for arm in ('none','agreement')};covered=link_summary(predictions['sentences'][e['sent_id']]['agreement'],e['reference'])['reference_exact']
            for probe in byexample[e['sent_id'],e['subject'],e['predicate']]:
                f=probe['field'];pair=(probe['wrong_value'],e['predicate']) if f=='subject' else (e['subject'],probe['wrong_value']);raw=pair in pairs['none'];agreed=pair in pairs['agreement'];r=wrong[f];r['n']+=1;r['raw_feasible']+=raw;r['agreement_feasible']+=agreed;r['covered_raw_feasible']+=covered and raw;r['covered_rejected']+=covered and raw and not agreed
        cells.append(dict(seed=predictions['seed'],mode=predictions['mode'],rate=predictions['rate'],groups=groups,wrong=wrong))
    save(OUT/'evaluation-cells.json',cells);pooled={}
    for mode in MODES:
        for rate in RATES:
            selected=[c for c in cells if c['mode']==mode and c['rate']==rate];key=f'{mode}/{rate}';pooled[key]={}
            for cohort in ('all','clean_ambiguous'):
                pooled[key][cohort]={}
                for arm in ('none','agreement'):
                    r=[c['groups']['pooled/'+cohort][arm] for c in selected];pooled[key][cohort][arm]={metric:dict(mean=float(np.mean([v[metric] for v in r])),min=min(v[metric] for v in r),max=max(v[metric] for v in r)) for metric in r[0]}
            pooled[key]['wrong']={f:{metric:float(np.mean([c['wrong'][f][metric] for c in selected])) for metric in selected[0]['wrong'][f]} for f in ('subject','predicate')}
    save(OUT/'evaluation.json',dict(conditions=pooled,note='Means/ranges across5 word-type perturbations of the same326 constructions; ranges are not confidence intervals. Clean-ambiguous cohort270 is fixed, not reselected after corruption.'))
    for key,r in pooled.items():
        if key.endswith('/0.0') or key.endswith('/0.5') or key.endswith('/1.0'):print(key,{k:round(v['mean'],2) for k,v in r['all']['agreement'].items()},'ambiguous_unique',r['clean_ambiguous']['agreement']['unique_correct'])
if __name__=='__main__':run()
