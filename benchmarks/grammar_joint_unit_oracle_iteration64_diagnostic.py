"""Describe rejected source targets and verify the coordination-only correction."""
from pathlib import Path
from collections import Counter,defaultdict
from benchmarks.grammar_joint_unit_oracle_iteration64b import OUT,SOURCE,load,save
from voynich_smt.copular_head_oracle import in_adp_phrase


def run():
    data=load(SOURCE);initial=load(OUT.parent/'iteration64'/'frame-predictions.json');corrected=load(OUT/'frame-predictions.json');old={(r['sid'],r['subject']):r for r in initial};changed=Counter();checks=0
    for r in corrected:
        previous=old[(r['sid'],r['subject'])]
        for field in ('joint_pipeline','joint_oracle_endpoint','joint_true_type'):
            for arm,prediction in r[field].items():
                if arm not in ('sv_coord','adjective_coord','oracle_full'):assert prediction==previous[field][arm];checks+=1
                elif prediction!=previous[field][arm]:changed[field+'/'+arm]+=1
    groups=defaultdict(list)
    for r in corrected:
        v=r['arms']['carrierfit_carriercal']['f1']
        if v is not None and not r['carrier_ambiguous']:groups[(r['sid'],v)].append(r)
    group_counts=Counter()
    for (_,v),group in groups.items():
        if len(group)<2:continue
        group_counts['multi_subject_predicted_groups']+=1
        mistakes=sum(r['unit_gold'] is None or r['unit_gold'][2]!=v for r in group)
        group_counts['groups_with_wrong_endpoint']+=mistakes>0
        group_counts['groups_with_only_correct_endpoints']+=mistakes==0
    save(OUT/'predicted-group-diagnostic.json',dict(group_counts))
    feasibility=load(OUT/'gold-feasibility.json');cases=[]
    for r in feasibility:
        arms=r['arms']
        for strict,permissive in (('sv_strict','sv_coord'),('adjective_strict','adjective_coord')):
            assert set(arms[permissive]['local_reasons'])<=set(arms[strict]['local_reasons'])
            assert not arms[strict]['gold_feasible'] or arms[permissive]['gold_feasible']
        if not (arms['gold_role_clause']['local_reasons'] or arms['adjective_coord']['local_reasons']):continue
        tokens=data[r['sid']]['tokens'];s,h,v,_=r['gold']
        cases.append(dict(sid=r['sid'],gold=r['gold'],sentence=' '.join(t['word'] for t in tokens),tokens={str(i):tokens[i] for i in sorted({s,h,v})},head_in_adp_phrase=in_adp_phrase(tokens,h),role_reasons=arms['gold_role_clause']['local_reasons'],adjective_reasons=arms['adjective_coord']['local_reasons']))
    save(OUT/'counterexamples.json',dict(scope='Source annotations retained verbatim. No manual relabeling; diagnostic cases, not a new validation set.',cases=cases))
    save(OUT/'correction-validation.json',dict(non_coordination_decisions_unchanged=checks,coordination_gold_masks_monotone=True,changed_decisions=dict(changed)))
    print('Correction checks',checks,dict(changed));print('Counterexamples',len(cases))
if __name__=='__main__':run()
