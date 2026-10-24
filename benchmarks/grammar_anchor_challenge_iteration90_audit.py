"""Replay every challenge and confirm controls reproduce iteration89."""
from benchmarks.grammar_anchor_challenge_iteration90 import *
from benchmarks.grammar_anchor_augmentation_iteration89_audit import compare

def run():
    for p,h in load(OUT/'design-freeze.json')['inputs'].items():assert digest(p)==h,p
    data=load(ROOT/'iteration44/annotations-truth.json');part=load(ROOT/'iteration49/manifest.json')['partitions']['0'];source=lambda split:[dict(sent_id=sid,**data[sid]) for sid in part[split]];catalogue=load(ROOT/'iteration85/anchor-budgets.json');patterns=load(OUT/'patterns.json');assert patterns==challenge_patterns(source('fit'),catalogue['20']);anchors=catalogue['195'];models={'original':load(BASE/'models.json'),'augmented':load(ROOT/'iteration89/models.json')};pol=load(BASE/'policies.json');assert load(ROOT/'iteration89/policies.json')['augmented']['robust_threshold']==CUTS['selected89'];cache=load(CACHE);decl=load(DECLARATION)['split_ids'];datasets={'source':source('test')};datasets.update({a:cached_sentences(cache,decl[a]) for a in AUTHORS});summary={};checked=0
    for name,sentences in datasets.items():
        public,labels=transfer_rows(sentences,anchors,'challenge90-'+name,models['original']['pos_classes']);baseline={}
        for pattern,replacements in patterns.items():
            changed=perturb(public,replacements,anchors);assert [t['id'] for s in changed for t in s['tokens']]==[t['id'] for s in public for t in s['tokens']];q=query_rows(changed,labels);affected=sum(x!=y for s,t in zip(public,changed) for x,y in zip(s['tokens'],t['tokens']))
            for arm,model in models.items():
                folder=OUT/(name.lower()+'-'+arm+'-'+pattern)
                for p,h in load(folder/'prediction-freeze.json')['inputs'].items():assert digest(p)==h,p
                rows=load(folder/'predictions.json');compare(infer85(q,model),rows)
                if pattern=='correct':baseline[arm]=rows
                result=evaluate_challenge(rows,baseline[arm],pol);result['affected_anchor_tokens']=affected;assert result==load(folder/'evaluation.json');summary[name+'/'+arm+'/'+pattern]=result
                if pattern in ('correct','rehearsed_in_et'):
                    previous_pattern='correct' if pattern=='correct' else 'swap_adp_conjunction'
                    oldpath=ROOT/'iteration89'/(name.lower()+'-'+previous_pattern)/'predictions.json' if arm=='augmented' else ROOT/'iteration87'/(name.lower()+'-195-'+previous_pattern)/'predictions.json';oldrows=load(oldpath);assert len(oldrows)==len(rows)
                    for r,t in zip(rows,oldrows):
                        assert (r['sid'],r['index'],r['labels'])==(t['sid'],t['index'],t['labels'])
                        for a in ARMS:assert math.isclose(r['scores'][a]['pp'],t['scores'][a]['pp'],rel_tol=1e-10,abs_tol=1e-12)
        print('replayed',name,flush=True)
    assert summary==load(OUT/'evaluation.json')
    for path in ROOT.glob('iteration*/verification-manifest.json'):
        if path.parent==OUT:continue
        for p,h in load(path).get('inputs',{}).items():assert digest(p)==h,(path,p);checked+=1
    save(OUT/'audit.json',dict(all48conditions_replayed=True,patterns_source_fit_only=True,opaque_type_ids_preserved=True,original_and_augmented_controls_reproduce=True,models_and_thresholds_unchanged=True,prior_input_hashes_verified=checked,reserve_unscored=True));print('audit passed',checked,'prior hashes')
if __name__=='__main__':run()
