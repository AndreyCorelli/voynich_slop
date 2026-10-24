"""Audit nested sizes, public-count matching, all decisions and new joint-mask scores."""
from benchmarks.grammar_anchor_length_curve_iteration99 import *
from benchmarks.grammar_repair_abstention_iteration98_audit import joint_only

def run():
    for p,h in load(OUT/'design-freeze.json')['inputs'].items():assert digest(p)==h,p
    data=load(ROOT/'iteration44/annotations-truth.json');oldblocks=load(PREVIOUS/'blocks.json');blocks=load(OUT/'blocks.json');assert blocks==length_blocks(oldblocks);words=load(ROOT/'iteration93/types.json')['candidates'];anchors=load(ROOT/'iteration85/anchor-budgets.json')['195'];models=load(ROOT/'iteration93/models.json');bank=load(PREVIOUS/'calibration-bank.json');cut=load(ROOT/'iteration95/policies.json')['joint_context']['threshold'];hundreds=[[dict(sent_id=sid,**data[sid]) for sid in oldblocks['scored']['sparse'+str(i)]] for i in range(8)];matched=load(OUT/'matched-words.json');assert matched==sorted(set.intersection(*(supported_words(ss,words) for ss in hundreds)));first800={sid for i in range(8) for sid in oldblocks['scored']['sparse'+str(i)]}
    for n in (100,200,400,800):
        level=[ids for b,ids in blocks.items() if b.startswith(str(n)+'-')];assert all(len(ids)==n for ids in level);assert len([sid for ids in level for sid in ids])==800 and {sid for ids in level for sid in ids}==first800
    evaluation={};computed=0;reused=0
    for block,ids in blocks.items():
        size,index=block.split('-');reuse=PREVIOUS/('sparse'+index if size=='100' else 'full') if size in ('100','829') else None;salt=('cal98-sparse'+index if size=='100' else 'cal98-full') if reuse else 'length99-'+block;public=ag.public_sentences([dict(sent_id=sid,**data[sid]) for sid in ids],anchors,salt);matched_ids={t['id'] for s in public for t in s['tokens'] if t['anchor'] in matched};cache={}
        for case,replacements in bank.items():
            path=OUT/block/(case+'.json')
            for p,h in load(OUT/block/(case+'.freeze.json'))['inputs'].items():assert digest(p)==h,p
            stored=load(path);scores=stored['scores']
            if reuse:
                assert scores==load(reuse/(case+'.json'))['scores'];assert stored['origin']==dict(reused=str(reuse/(case+'.json')));reused+=1
            else:
                changed=perturb(public,replacements,anchors);sig=signature(changed)
                if sig not in cache:cache[sig]=joint_only(changed,words,models)
                aa={tuple(r['pair']):r for r in scores};bb={tuple(r['pair']):r for r in cache[sig]};assert aa.keys()==bb.keys()
                for pair,r in aa.items():assert r['supported']==bb[pair]['supported'];assert math.isclose(r['gain'],bb[pair]['gain'],rel_tol=1e-10,abs_tol=1e-12)
                assert stored['origin']==dict(computed=True);computed+=1
            ref=reference_for(public,replacements,case.startswith('swap_'),scores,words);arms={'all':curve_metrics(scores,ref,cut)}
            if not ref['error'] or set(replacements)<=set(matched):
                arms['matched_errors_all_candidates']=curve_metrics(scores,ref,cut);restricted=[r for r in scores if set(r['pair'])<=matched_ids];arms['matched_errors_fixed_candidates']=curve_metrics(restricted,ref,cut)
                if ref['error']:assert arms['matched_errors_fixed_candidates']['reference_supported']
            evaluation[block+'/'+case]=arms
        print('replayed block',block,flush=True)
    assert computed==469 and reused==603;assert evaluation==load(OUT/'evaluation.json');assert summarize99(evaluation)==load(OUT/'summary.json');checked=0
    for path in ROOT.glob('iteration*/verification-manifest.json'):
        if path.parent==OUT:continue
        for p,h in load(path).get('inputs',{}).items():assert digest(p)==h,(path,p);checked+=1
    save(OUT/'audit.json',dict(all1072scenario_decisions_replayed=True,new469probability_cases_replayed=True,reused603cases_match_frozen98=True,public_support_matching_and_nested_blocks_verified=True,classifier_and_cutoff_unchanged=True,prior_input_hashes_verified=checked,reserve_and_authors_unscored=True));print('audit passed',checked,'prior hashes')
if __name__=='__main__':run()
