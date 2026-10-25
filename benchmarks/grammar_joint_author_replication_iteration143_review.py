"""Audit untouched joint-model parameters and additional-author replication."""
from benchmarks.grammar_joint_author_replication_iteration143 import *
from benchmarks.grammar_joint_scalars_iteration142_review import combined

def run():
    hashes=0
    for name in ['design-freeze','input-freeze','predictions-freeze']:
        for p,h in load(OUT/(name+'.json'))['inputs'].items():assert digest(p)==h,p;hashes+=1
    corepath=ROOT/'iteration139/common-core.json';assert digest(corepath)==load(ROOT/'iteration139/verification-manifest.json')['inputs'][str(corepath)];save(OUT/'reference-provenance.json',dict(common_core_path=str(corepath),sha256=digest(corepath),preexisting139_frozen_hash_verified=True));core=set(load(corepath));models=load(ROOT/'iteration142/models.json');streams=load(OUT/'streams.json');selection=load(OUT/'selection.json');transforms=load(OUT/'transforms.json');saved=load(OUT/'features.json');pred=load(OUT/'predictions.json');summary=load(OUT/'summary.json');contrasts=load(OUT/'contrasts.json');anchors=load(ROOT/'iteration85/anchor-budgets.json')['195'];words=load(ROOT/'iteration93/types.json')['candidates'];old=load('experiments/results/scalable-latin-trigram/v1/design.json');assert set(WORKS)<=set(old['development']);types=probchecks=metricchecks=0;diagnostic={}
    for work in WORKS:
        tokens=(CORPUS/(work+'.txt')).read_text().split();meta=load(CORPUS/(work+'.json'));assert meta['split']=='development' and len(tokens)==meta['tokens'] and digest(CORPUS/(work+'.txt'))==meta['normalized_sha256'];lookup={w:hashlib.sha256(('raw143-'+work+'|'+w).encode()).hexdigest() for w in words};seq=[hashlib.sha256(('raw143-'+work+'|'+w).encode()).hexdigest() for w in tokens];assert seq==streams[work];assert selection[work]['lookup']==lookup;assert selection[work]['candidate_counts']=={w:tokens.count(w) for w in words};assert selection[work]['missing_types']==sorted(w for w in words if not tokens.count(w));assert len(transforms[work])==17
        for view,ix in transforms[work].items():
            if view=='original':assert ix is None;ids=seq
            else:
                seed=int(view[4:]);assert seed in NULL_SEEDS;assert ix==np.random.default_rng(seed).permutation(len(seq)).tolist();assert sorted(ix)==list(range(len(seq)));ids=[seq[i] for i in ix]
            assert Counter(ids)==Counter(seq);features=combined(ids,set(lookup.values()));assert set(features)==set(saved[work][view]);types+=len(features)
            for i in features:
                assert features[i]['n']==saved[work][view][i]['n']
                for c in ['corrected','role_similarity']:assert abs(features[i][c]-saved[work][view][i][c])<1e-11
            for name,rows in pred[work][view].items():
                assert {r['opaque'] for r in rows}==set(features)
                for r in rows:
                    assert r['n']==features[r['opaque']]['n'];q=predict_vector(features[r['opaque']],models[name]['final']);assert abs(q-r['probabilities']['raw'])<1e-10;probchecks+=1
                for group,mm in summary[work][view][name].items():
                    rr=[r for r in rows if group=='all' or group=='supported' and r['supported'] or group=='common14' and r['type'] in core]
                    for p,m in mm.items():
                        assert m['n']==len(rr)
                        if not rr:continue
                        q=np.array([r['probabilities'][p] for r in rr]);y=np.array([anchors[r['type']]=='CCONJ' for r in rr]);a=q>.5;assert m['correct']==int((a==y).sum());assert abs(m['nll']-float(-np.log(np.where(y,q,1-q)).mean()))<1e-12
                        if y.any() and (~y).any():assert m['auc']==float(np.mean((q[y,None]>q[~y][None,:])+.5*(q[y,None]==q[~y][None,:])))
                        metricchecks+=1
        for name,c in contrasts[work].items():
            actual=summary[work]['original'][name]['all']['raw'];null=[summary[work]['word'+str(seed)][name]['all']['raw'] for seed in NULL_SEEDS];assert c['actual']==actual;assert abs(c['null_mean_auc']-np.mean([r['auc'] for r in null]))<1e-12;assert c['null_max_auc']==max(r['auc'] for r in null);assert c['null_auc_at_least_actual']==sum(r['auc']>=actual['auc'] for r in null)
        rr=pred[work]['original']['joint'];diagnostic[work]=dict(wrong_types=[r['type'] for r in rr if (r['probabilities']['raw']>.5)!=(anchors[r['type']]=='CCONJ')],low_count_types=[r['type'] for r in rr if r['n']<5]);print('audited',work,flush=True)
    save(OUT/'diagnostic.json',diagnostic);save(OUT/'audit.json',dict(input_hashes_verified=hashes,preexisting_common_core_hash_verified=True,transformed_views_reconstructed=51,independent_feature_pairs=types,probabilities_replayed=probchecks,metric_groups=metricchecks,all_models_identical_to142=True,only_inspected_development_works_opened=True,no_fit_or_new_annotations=True));print(load(OUT/'audit.json'));print(diagnostic)
if __name__=='__main__':run()
