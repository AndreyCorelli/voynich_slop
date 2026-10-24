"""Reproduce descriptive merger diagnostics without changing the frozen core."""
from benchmarks.grammar_anchor_test_length_iteration100 import *


def run():
    values=load(OUT/'evaluation.json');blocks=load(OUT/'blocks.json');core=load(OUT/'core.json');data=load(ROOT/'iteration44/annotations-truth.json');perblock={};wrong={};ex={}
    for block,ids in blocks.items():
        rows=[v['core_errors_fixed_candidates'] for k,v in values.items() if k.startswith(block+'/') and 'core_errors_fixed_candidates' in v];perblock[block]=aggregate(rows);lookup={__import__('hashlib').sha256(('testlength100-'+block+'|'+w).encode()).hexdigest():w for w in core};wrong[block]=[]
        for key,arms in values.items():
            if key.startswith(block+'/') and 'core_errors_fixed_candidates' in arms:
                r=arms['core_errors_fixed_candidates']
                if r['wrong']:wrong[block].append(dict(case=key.split('/')[1],selected=[lookup[i] for i in r['selected']]))
        ex[block]=dict(ex_tokens=sum(t['word']=='ex' for sid in ids for t in data[sid]['tokens']),ex_sentences=sum(any(t['word']=='ex' for t in data[sid]['tokens']) for sid in ids),wrong_pairs=len(wrong[block]),wrong_involving_ex=sum('ex' in r['selected'] for r in wrong[block]))
    assert perblock==load(OUT/'core-per-block.json');assert wrong==load(OUT/'wrong-core-recommendations.json');assert ex==load(OUT/'ex-eligibility-diagnostic.json');checked=0
    for key,value in load(ROOT/'iteration97/evaluation.json').items():
        name,case=key.split('/')
        if name!='source':continue
        a=values['770-0/'+case]['all'];b=value['joint_context']['pair'];assert (a['hit'],a['wrong'],a['abstain'])==(b['hit'],b['false_pair'],b['selected'] is None);checked+=1
    assert load(OUT/'prior-comparison-audit.json')==dict(shared_770_source_cases_match97=checked);save(OUT/'summary-audit.json',dict(descriptive_block_wrong_partner_and_occurrence_diagnostics_verified=True,prior97_shared_cases_verified=checked,core_and_policies_unchanged=True));print('Supplementary analysis verified')
if __name__=='__main__':run()
