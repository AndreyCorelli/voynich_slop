"""Replay frozen-core source-test length replication without recertifying candidates."""
from benchmarks.grammar_anchor_test_length_iteration100 import *
from benchmarks.grammar_repair_abstention_iteration98_audit import joint_only


def run():
    for p,h in load(OUT/'design-freeze.json')['inputs'].items():assert digest(p)==h,p
    data=load(ROOT/'iteration44/annotations-truth.json');part=load(ROOT/'iteration49/manifest.json')['partitions']['0'];blocks=load(OUT/'blocks.json');assert blocks==test_blocks(part['test']);assert set(part['test']).isdisjoint(part['fit']) and set(part['test']).isdisjoint(part['calibration']);core=load(OUT/'core.json');assert core==load(PREVIOUS/'matched-words.json');anchors=load(ROOT/'iteration85/anchor-budgets.json')['195'];words=load(ROOT/'iteration93/types.json')['candidates'];models=load(ROOT/'iteration93/models.json');bank=load(ROOT/'iteration98/calibration-bank.json');cut=load(ROOT/'iteration95/policies.json')['joint_context']['threshold'];hundreds=[[dict(sent_id=sid,**data[sid]) for sid in blocks['100-'+str(i)]] for i in range(4)];common=sorted(set(core)&set.intersection(*(supported_words(ss,words) for ss in hundreds)));assert load(OUT/'secondary-common-support.json')==dict(words=common,not_reselected_candidates=True);evaluation={};availability={};count=0
    for block,ids in blocks.items():
        assert set(ids)<=set(part['test']);sentences=[dict(sent_id=sid,**data[sid]) for sid in ids];public=ag.public_sentences(sentences,anchors,'testlength100-'+block);core_ids={t['id'] for s in public for t in s['tokens'] if t['anchor'] in core};availability[block]=dict(core_supported=sorted(set(core)&supported_words(sentences,words)),n_sentences=len(ids));cache={}
        for case,replacements in bank.items():
            path=OUT/block/(case+'.json')
            for p,h in load(OUT/block/(case+'.freeze.json'))['inputs'].items():assert digest(p)==h,p
            changed=perturb(public,replacements,anchors);sig=signature(changed)
            if sig not in cache:cache[sig]=joint_only(changed,words,models)
            scores=load(path)['scores'];aa={tuple(r['pair']):r for r in scores};bb={tuple(r['pair']):r for r in cache[sig]};assert aa.keys()==bb.keys()
            for pair,r in aa.items():assert r['supported']==bb[pair]['supported'];assert math.isclose(r['gain'],bb[pair]['gain'],rel_tol=1e-10,abs_tol=1e-12)
            ref=reference_for(public,replacements,case.startswith('swap_'),scores,words);arms={'all':curve_metrics(scores,ref,cut)}
            if not ref['error'] or set(replacements)<=set(core):
                restricted=[r for r in scores if set(r['pair'])<=core_ids];arms['core_errors_all_candidates']=curve_metrics(scores,ref,cut);arms['core_errors_fixed_candidates']=curve_metrics(restricted,ref,cut)
                if not ref['error'] or set(replacements)<=set(common):arms['common_support_errors_fixed_core']=curve_metrics(restricted,ref,cut)
            evaluation[block+'/'+case]=arms;count+=1
        print('replayed test block',block,flush=True)
    assert count==603;assert availability==load(OUT/'availability.json');assert evaluation==load(OUT/'evaluation.json');assert summarize100(evaluation)==load(OUT/'summary.json');checked=0
    for path in ROOT.glob('iteration*/verification-manifest.json'):
        if path.parent==OUT:continue
        for p,h in load(path).get('inputs',{}).items():assert digest(p)==h,(path,p);checked+=1
    save(OUT/'audit.json',dict(all603probability_cases_and_decisions_replayed=True,core_classifier_cutoff_frozen=True,source_test_disjoint_from_fit_cal=True,common_support_is_evaluation_stratum_not_reselected_core=True,source_test_only_no_authors_or_reserve=True,prior_input_hashes_verified=checked));print('audit passed',checked,'prior hashes')
if __name__=='__main__':run()
