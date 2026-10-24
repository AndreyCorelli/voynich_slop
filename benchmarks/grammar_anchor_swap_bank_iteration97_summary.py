"""Verify aggregate outcome summaries without changing frozen policies."""
from benchmarks.grammar_anchor_swap_bank_iteration97 import *

def summarize():
    result={}
    for name in ('source','Jerome','Caesar'):
        items=[(path.parent.name,load(path),load(path.parent/'actions.json')) for path in sorted((OUT/name.lower()).glob('swap_*/evaluation.json'))];result[name]={}
        for arm in PAIR_ARMS:
            rr=[d[arm] for case,d,a in items];hits=sum(r['pair']['hit'] for r in rr);wrong=sum(r['pair']['false_pair'] for r in rr);stats=dict(cases=len(rr),correct_pairs=hits,wrong_pairs=wrong,abstentions=sum(r['pair']['selected'] is None for r in rr),observed_pair_precision=hits/(hits+wrong) if hits+wrong else None,reference_supported=sum(r['pair']['reference_supported'] for r in rr),reference_absent=sum(not r['pair']['reference_present'] for r in rr),zero_affected=sum(a['affected_tokens']==0 for case,d,a in items),wrong_reference_unsupported=sum(r['pair']['false_pair'] and not r['pair']['reference_supported'] for r in rr),pp={})
            for model,cuts in PP_SETTINGS.items():
                for policy in cuts:
                    es=[r['pp'][model][policy] for r in rr];cs=[e['changes'] for e in es];stats['pp'][model+'/'+policy]=dict(new_tp=sum(c['new_tp'] for c in cs),lost_tp=sum(c['lost_tp'] for c in cs),new_fp=sum(c['new_fp'] for c in cs),removed_fp=sum(c['removed_fp'] for c in cs),cases_net_tp_loss=sum(e['after']['tp']<e['before']['tp'] for e in es),cases_net_fp_increase=sum(e['after']['fp']>e['before']['fp'] for e in es),abstentions_preserve_pp=all(not any(r['pp'][model][policy]['changes'].values()) for r in rr if r['pair']['selected'] is None),hits_reproduce_clean_decisions=all(r['pp'][model][policy]['different_from_clean']==0 for r in rr if r['pair']['hit']))
            result[name][arm]=stats
    return result


def detail_summaries():
    all_ev=load(OUT/'evaluation.json');wrong=[];strata={}
    for name in ('source','Jerome','Caesar'):
        lookup={t['id']:t['anchor'] for sentence in load(OUT/name.lower()/'public-clean.json') for t in sentence['tokens'] if t['anchor']};strata[name]={}
        for case in load(OUT/'bank.json'):
            if not case.startswith('swap_'):continue
            result=all_ev[name+'/'+case];pair=result['joint_context']['pair'];key='supported' if pair['reference_supported'] else 'present_unsupported' if pair['reference_present'] else 'absent';group=strata[name].setdefault(key,dict(cases=0,hits=0,wrong=0,abstain=0));group['cases']+=1;group['hits']+=pair['hit'];group['wrong']+=pair['false_pair'];group['abstain']+=pair['selected'] is None
            for arm,arm_result in result.items():
                if arm_result['pair']['false_pair']:wrong.append(dict(dataset=name,case=case,arm=arm,recommended_original_types=[lookup[opaque] for opaque in arm_result['pair']['selected']],reference_supported=arm_result['pair']['reference_supported'],reference_present=arm_result['pair']['reference_present'],pp=arm_result['pp']))
    return wrong,strata

if __name__=='__main__':
    assert summarize()==load(OUT/'summary.json')
    wrong,strata=detail_summaries();assert wrong==load(OUT/'wrong-repairs.json') and strata==load(OUT/'reference-strata.json')
    save(OUT/'summary-audit.json',dict(all_aggregate_counts_and_damage_metrics_verified=True,wrong_repair_and_reference_strata_verified=True,policies_unchanged=True));print('Summary audit passed')
