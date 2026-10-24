"""Replay sentence-bootstrap matrices, policy selection and cached-score equivalence."""
from benchmarks.grammar_pair_uncertainty_iteration102 import *
from voynich_smt.pair_uncertainty import selected


def run():
    checks=0
    for file in ['design-freeze.json','policy-freeze.json']:
        for path,h in load(OUT/file)['inputs'].items():assert digest(Path(path))==h,path;checks+=1
    data=load(ROOT/'iteration44/annotations-truth.json');anchors=load(ROOT/'iteration85/anchor-budgets.json')['195'];model=load(ROOT/'iteration93/models.json')['context'];cal=load(OUT/'calibration-cases.json');evaluation=load(OUT/'evaluation-cases.json');replayed=0;predictions=0
    for kind,blocks in [('cal',load(ROOT/'iteration98/blocks.json')['scored']),('eval',load(ROOT/'iteration100/blocks.json'))]:
        for bi,(block,ids) in enumerate(blocks.items()):
            folder=OUT/(block if kind=='cal' else 'eval-'+block);weights=np.load(folder/'weights.npz')['weights'];seed=(102000 if kind=='cal' else 103000)+bi;expected=np.random.default_rng(seed).multinomial(len(ids),np.full(len(ids),1/len(ids)),size=256);assert np.array_equal(weights,expected)
            rows=[c for c in (cal if kind=='cal' else evaluation) if c['block']==block]
            for c in rows:
                payload=np.load(folder/(c['case']+'.npz'));n=payload['counts'];q=payload['sums'];draws=[]
                for j,p in enumerate(c['pairs']):
                    gain=float(gains_from_totals(n[j].sum(0),q[j].sum(0),c['proposed'][j]));assert math.isclose(gain,p['gain'],rel_tol=1e-9,abs_tol=1e-10)
                    draws.append(gains_from_totals(weights@n[j],weights@q[j],c['proposed'][j]))
                draws=np.array(draws).T;assert np.array_equal(draws,payload['draws']);assert summarize(c['pairs'],draws)==c['features'];replayed+=1
            # Recompute every pair's classifier probabilities for the clean view in each block.
            clean=next(c for c in rows if c['case']=='correct');base=ag.public_sentences([dict(sent_id=sid,**data[sid]) for sid in ids],anchors,('cal98-' if kind=='cal' else 'testlength100-')+block);payload=np.load(folder/'correct.npz')
            for j,p in enumerate(clean['pairs']):
                n,q=sentence_totals(base,p['pair'],model);assert np.array_equal(n,payload['counts'][j]);assert np.allclose(q,payload['sums'][j],rtol=1e-12,atol=1e-12);predictions+=1
    policies=load(OUT/'policies.json')
    for arm in ['stability','lower']:
        chosen,curve=calibrate102(cal,arm);assert chosen['policy']==policies[arm];assert curve==load(OUT/('curve-'+arm+'.json'))
    for name,rows in [('calibration',cal),('evaluation',evaluation)]:assert {a:evaluate102(rows,p) for a,p in policies.items()}==load(OUT/(name+'-summary.json'))
    # Check original references/features against prior cases, independently of new selection.
    prior={(c['block'],c['case']):c for c in load(ROOT/'iteration98/calibration-cases.json')}
    for c in cal:
        old=prior[c['block'],c['case']];assert c['reference']==old['reference'];assert all(c['features'][k]==v for k,v in old['features'].items())
    prior_evaluation=load(ROOT/'iteration100/evaluation.json');baseline=load(OUT/'evaluation-summary.json')['frozen95']
    for block,stats in baseline.items():
        rows=[arms['core_errors_fixed_candidates'] for key,arms in prior_evaluation.items() if key.startswith(block+'/') and 'core_errors_fixed_candidates' in arms]
        assert len(rows)==stats['n'] and sum(r['hit'] for r in rows)==stats['hit'] and sum(r['wrong'] for r in rows)==stats['wrong']
    for path,h in load(ROOT/'iteration101/verification-manifest.json')['inputs'].items():assert digest(Path(path))==h,path;checks+=1
    save(OUT/'audit.json',dict(baseline_matches_iteration100=True,input_hashes_verified=checks,bootstrap_case_matrices_replayed=replayed,clean_pair_probability_recomputations=predictions,calibration_references_and_point_features_match_98=True,policies_refit_identically=True,no_reserve_or_new_annotations=True))
    print(load(OUT/'audit.json'))
if __name__=='__main__':run()
