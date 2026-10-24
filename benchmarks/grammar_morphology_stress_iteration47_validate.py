"""Replay perturbations/supports and verify nested uncertainty/deletion behavior."""
from collections import Counter
from benchmarks.grammar_morphology_stress_iteration47 import OUT,PREVIOUS,SOURCE,RESERVE,RATES,MODES,SEEDS,load,save,digest
from voynich_smt.construction_interventions import readings_key
from voynich_smt.relational_compatibility import sv_domains,sv_lattice,sv_summary
from voynich_smt.morphology_stress import schedule,perturb,encode,decode,link_summary


def subset(a,b):
    right={(s,v):mask for s,v,mask in b}
    return all(mask&right.get((s,v),0)==mask for s,v,mask in a)


def validate():
    hashes=0
    for name in ('manifest.json','prediction-freeze.json','evaluation-freeze.json'):
        for p,h in load(OUT/name)['inputs'].items():assert digest(p)==h,p;hashes+=1
    data=load(SOURCE);examples=load(PREVIOUS/'sv-lattices.json');lexicon=load(PREVIOUS/'sv-morphology-oracle.json');plans=load(OUT/'schedules.json');ids=load(OUT/'manifest.json')['sentences'];reserve={r['sent_id'] for rows in load(RESERVE)['authors'].values() for r in rows};assert not set(ids)&reserve;keys={readings_key(t) for sid in ids for t in data[sid]['tokens']};decoded=0;pred_replays=0;summary_replays=0;support_checks=0
    for seed in SEEDS:
        plan=plans[str(seed)];assert plan==schedule(lexicon,keys,seed);previous={};bymode={}
        for mode in MODES:
            for rate in RATES:
                noisy,selected=perturb(lexicon,plan,rate,mode);saved=load(OUT/f'predictions-{seed}-{mode}-{rate}.json');assert len(selected)==saved['selected_types']==int(rate*len(plan['order']))
                for key in selected:
                    original=lexicon[key];new=noisy[key]
                    if mode in ('extra','substituted'):assert plan['plans'][key]['extra'] in new
                    if mode in ('deleted','substituted'):assert plan['plans'][key]['original'] not in new
                    assert all((r[0],r[3]) in {(v[0],v[3]) for v in original} for r in new)
                    if key.split('\t')[1] in ('NOUN','PROPN'):assert all(r[2]=='3' for r in new)
                for sid in ids:
                    domain=sv_domains(data[sid]['tokens'],noisy)
                    for arm in ('none','agreement'):
                        candidates=sv_lattice(domain,arm);blocks=encode(candidates);assert blocks==saved['sentences'][sid][arm];assert set(map(tuple,decode(blocks)))==set(map(tuple,candidates));assert encode(decode(blocks))==blocks;decoded+=sum(mask.bit_count() for s,v,mask in blocks);pred_replays+=1
                        if rate and mode in ('extra','masked','deleted'):
                            old=previous[mode]['sentences'][sid][arm]
                            assert subset(old,blocks) if mode!='deleted' else subset(blocks,old)
                            support_checks+=1
                for e in examples:
                    for arm in ('none','agreement'):
                        blocks=saved['sentences'][e['sent_id']][arm];s=link_summary(blocks,e['reference']);expected=sv_summary(decode(blocks),e['reference']);assert s['reference_exact']==expected['reference_retained'] and s['reference_link']==expected['reference_link_retained'];assert s['unique_correct']==expected['unique_link_correct'] and s['false_unique']==expected['false_unique_link'];summary_replays+=1
                previous[mode]=saved;bymode[mode,rate]=saved
        # Matched extra/substitution differ solely in retaining the removed reading.
        for rate in RATES:
            for sid in ids:
                for arm in ('none','agreement'):
                    d=bymode['deleted',rate]['sentences'][sid][arm];s=bymode['substituted',rate]['sentences'][sid][arm];x=bymode['extra',rate]['sentences'][sid][arm];m=bymode['masked',rate]['sentences'][sid][arm];assert subset(d,s) and subset(s,x) and subset(x,m);support_checks+=1
    # Aggregate counts are checked against per-cell integer results, not decoded totals.
    cells=load(OUT/'evaluation-cells.json');aggregate=load(OUT/'evaluation.json')['conditions']
    for mode in MODES:
        for rate in RATES:
            selected=[r for r in cells if r['mode']==mode and r['rate']==rate];assert len(selected)==5
            for cohort in ('all','clean_ambiguous'):
                for arm in ('none','agreement'):
                    for metric,summary in aggregate[f'{mode}/{rate}'][cohort][arm].items():assert abs(summary['mean']-sum(c['groups']['pooled/'+cohort][arm][metric] for c in selected)/5)<1e-10
    result=dict(hash_checks=hashes,cells=len(cells),prediction_replays=pred_replays,summary_replays=summary_replays,decoded_readings=decoded,nested_support_checks=support_checks,reserved_unscored=len(reserve),prior_queries_scored=0);save(OUT/'validation.json',result);print(result)
if __name__=='__main__':validate()
