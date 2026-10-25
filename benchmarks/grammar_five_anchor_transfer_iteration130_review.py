"""Audit fixed five-anchor author transfer and scored-prefix isolation."""
from benchmarks.grammar_five_anchor_transfer_iteration130 import *
from voynich_smt.paired_anchor_class import target_features

def run():
    hashes=0
    for name in ['design-freeze','input-freeze','predictions-freeze']:
        for p,h in load(OUT/(name+'.json'))['inputs'].items():assert digest(p)==h,p;hashes+=1
    allowed={r['type'] for r in load(ROOT/'iteration129/anchor-ranking.json')[:5]};words=load(ROOT/'iteration93/types.json')['candidates'];anchors=load(ROOT/'iteration85/anchor-budgets.json')['195'];predictions=load(OUT/'predictions.json');selection=load(OUT/'selection.json');cohorts=load(OUT/'cohorts.json');scores=load(OUT/'scores.json');summary=load(OUT/'class-summary.json');evaluation=load(OUT/'evaluation.json');volume=load(OUT/'volume-comparison.json');model=load(ROOT/'iteration124/models.json')['final'];cal=load(ROOT/'iteration124/calibrator.json');ppmodel=load(BASE/'models.json');reserved={r['sent_id'] for rr in load('experiments/holdouts/grammar-construction-next.json')['authors'].values() for r in rr};typechecks=vectors=checks=0;diagnostic={}
    for author,paths in INPUTS.items():
        publics={v:load(p) for v,p in paths.items()};assert publics['expanded'][:100]==publics['base'];lookup={t['anchor']:t['id'] for public in publics.values() for s in public for t in s['tokens'] if t['anchor'] in words};targets=set(lookup.values());labels=load(LABELS[author]);flat=[t for s in publics['base'] for t in s['tokens']];assert cohorts[author]==dict(all=list(range(len(flat))),original_unmapped=[i for i,t in enumerate(flat) if t['anchor'] is None],targets=[i for i,t in enumerate(flat) if t['id'] in targets],other_original_anchors=[i for i,t in enumerate(flat) if t['anchor'] is not None and t['id'] not in targets])
        for phase,public in publics.items():
            key=author+'-'+phase;assert not {s['sent_id'] for s in public}&reserved;masked=[]
            for s in public:
                ts=[]
                for t in s['tokens']:
                    expected=dict(t)
                    if t['id'] in targets or t['anchor'] not in allowed:expected.update(anchor=None,tag='X')
                    ts.append(expected)
                masked.append(dict(s,tokens=ts))
            rr=target_features(masked,targets);q=ag.predict([r['features'] for r in rr],model);rows=predictions[key];assert selection[key]['lookup']==lookup;assert selection[key]['missing_types']==sorted(set(words)-{r['type'] for r in rows});tags={}
            for r in rows:
                ix=[i for i,t in enumerate(rr) if t['word']==r['opaque']];raw=float(q[ix,1].mean());assert r['n']==len(ix) and r['sentences']==len({rr[i]['sid'] for i in ix});assert abs(raw-r['probabilities']['raw'])<1e-12;assert abs(float(apply_offset([raw],cal)[0])-r['probabilities']['balanced124'])<1e-12;tags[r['opaque']]='CCONJ' if r['probabilities']['balanced124']>.5 else 'ADP';typechecks+=1
            for group,ms in summary[key].items():
                rs=[r for r in rows if group=='all' or r['supported']]
                for arm,m in ms.items():
                    p=np.array([r['probabilities'][arm] for r in rs]);y=np.array([anchors[r['type']]=='CCONJ' for r in rs]);assert m['correct']==int(((p>.5)==y).sum());assert abs(m['nll']-float(-np.log(np.where(y,p,1-p)).mean()))<1e-12
                    if y.any() and (~y).any():assert m['auc']==float(np.mean((p[y,None]>p[~y][None,:])+.5*(p[y,None]==p[~y][None,:])))
            for arm,assign in [('unknown',{}),('hard',tags)]:
                view=load(OUT/('public-'+key+'-'+arm+'.json'));assert view==inject(masked[:100],targets,assign);assert [(s['sent_id'],i) for s in view for i,t in enumerate(s['tokens'])]==[(r['sid'],r['index']) for r in labels];expected=[r['scores']['pooled_pos']['pp'] for r in infer85(query_rows(view,labels),ppmodel)];assert np.allclose(expected,scores[key][arm],rtol=1e-12,atol=1e-12);vectors+=1
                for co,ii in cohorts[author].items():
                    a=np.array(expected)[ii]>=.8;b=np.array(scores[key]['unknown'])[ii]>=.8;y=np.array([labels[i]['labels']['pp'] for i in ii],bool);e=evaluation[key][arm][co];m=e['metrics'];assert [m[k] for k in ['tp','fp','fn','tn']]==[int((a&y).sum()),int((a&~y).sum()),int((~a&y).sum()),int((~a&~y).sum())];assert e['changes_from_unknown']==dict(new_tp=int((a&~b&y).sum()),new_fp=int((a&~b&~y).sum()),lost_tp=int((~a&b&y).sum()),removed_fp=int((~a&b&~y).sum()));checks+=1
            diagnostic[key]=dict(predicted_ADP=[r['type'] for r in rows if tags[r['opaque']]=='ADP'],wrong_types=[r['type'] for r in rows if tags[r['opaque']]!=anchors[r['type']]],maximum_hard_pp_score=max(scores[key]['hard']))
        assert np.allclose(scores[author+'-base']['unknown'],scores[author+'-expanded']['unknown'],rtol=1e-12,atol=1e-12)
        before={r['type']:r for r in predictions[author+'-base']};after={r['type']:r for r in predictions[author+'-expanded']};common=sorted(set(before)&set(after));v=volume[author];correct=lambda r:(r['probabilities']['balanced124']>.5)==(anchors[r['type']]=='CCONJ');assert v['common_types']==common;assert v['common_correct_before']==sum(correct(before[w]) for w in common);assert v['common_correct_after']==sum(correct(after[w]) for w in common);assert v['lost']==[w for w in common if correct(before[w]) and not correct(after[w])];assert v['gained']==[w for w in common if not correct(before[w]) and correct(after[w])]
    save(OUT/'diagnostic.json',diagnostic);save(OUT/'audit.json',dict(input_hashes_verified=hashes,type_probabilities_recomputed=typechecks,pp_vectors_recomputed=vectors,metric_transition_groups=checks,original100_prefix_scoring_verified=True,unknown_baselines_context_invariant=True,no_author_tuning_or_reserve=True));print(load(OUT/'audit.json'));print(diagnostic)
if __name__=='__main__':run()
