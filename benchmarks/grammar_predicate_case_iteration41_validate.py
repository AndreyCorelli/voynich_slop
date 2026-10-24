"""Reproduce frozen source models, predictions, shuffle controls, and case edits."""
from collections import Counter
import numpy as np
from benchmarks.grammar_predicate_case_iteration41 import OUT,ROOT,RESERVE,load,save,digest,PRIMARY,STRENGTHS,SEEDS,metrics
from voynich_smt.predicate_case import fit,probability


def validate():
    hashes=0
    for filename in ('manifest.json','prediction-freeze.json','evaluation-freeze.json'):
        for p,h in load(OUT/filename)['inputs'].items():assert digest(p)==h,p;hashes+=1
    rec=load(OUT/'records-truth.json');models=load(OUT/'models.json');pred=load(OUT/'predictions.json');shuffles=load(OUT/'shuffled-predictions.json');manifest=load(OUT/'manifest.json');reserved={r['sent_id'] for rows in load(RESERVE)['authors'].values() for r in rows};ids=manifest['split_ids'];assert not set(sum(ids.values(),[]))&reserved;assert not set(ids['source'])&(set(ids['Jerome'])|set(ids['Caesar']))
    for mode in ('oracle','nearest'):
        for strength in STRENGTHS:assert models[f'{mode}/{strength}']==fit(rec['source'][mode],strength)
    replay=0;audit=[];source_counts=Counter(r['case'] for r in rec['source']['oracle']);details={}
    for author in ('Jerome','Caesar'):
        rows=rec[author]['oracle'];near=rec[author]['nearest'];assert [(r['sent_id'],r['construction'],r['case']) for r in rows]==[(r['sent_id'],r['construction'],r['case']) for r in near]
        for arm,probs in pred[author].items():
            if arm=='baseline':expected=[models['oracle/4.0']['base']]*len(rows)
            else:
                mode='nearest' if arm.startswith('nearest') else 'oracle';modelkey='nearest/4.0' if arm=='nearest_matched' else ('oracle/4.0' if arm=='nearest_oracle_model' else arm);expected=[probability(models[modelkey],r['predicate']) for r in (near if mode=='nearest' else rows)]
            assert probs==expected;replay+=len(rows)
        null=sum(r['predicate'] is None for r in rows);unseen_nonnull=sum(r['predicate'] is not None and r['predicate'] not in models['oracle/4.0']['counts'] for r in rows);details[author]=dict(missing_predicate=null,unseen_nonmissing=unseen_nonnull)
        for i,r in enumerate(rows):
            p=pred[author]['oracle/4.0'][i];base=pred[author]['baseline'][i];gold=r['case']=='Acc';a=base>.5;b=p>.5
            if r['predicate'] not in models['oracle/4.0']['counts']:assert p==base
            audit.append(dict(author=author,**r,p_acc=p,baseline_p_acc=base,source_predicate_counts=models['oracle/4.0']['counts'].get(r['predicate'],{}),corrected=a!=gold and b==gold,spoiled=a==gold and b!=gold,nearest_p_acc=pred[author]['nearest_oracle_model'][i]))
    source=rec['source']['oracle']
    for seed,saved in zip(SEEDS,shuffles):
        assert seed==saved['seed'];order=np.random.default_rng(seed).permutation(len(source));fake=[dict(r,predicate=source[int(j)]['predicate']) for r,j in zip(source,order)];assert Counter(r['predicate'] for r in source)==Counter(r['predicate'] for r in fake);model=fit(fake,PRIMARY)
        assert model['base']==models['oracle/4.0']['base']
        for author in ('Jerome','Caesar'):
            expected=[probability(model,r['predicate']) for r in rec[author]['oracle']];assert expected==saved['predictions'][author];replay+=len(expected)
    save(OUT/'case-audit.json',audit);result=dict(hash_checks=hashes,prediction_replays=replay,source_cases=dict(source_counts),target_coverage=details,reserved_unscored=len(reserved));save(OUT/'validation.json',result);print(result)
    print('Edits',dict(Counter((r['author'],'corrected' if r['corrected'] else 'spoiled') for r in audit if r['corrected'] or r['spoiled'])))
if __name__=='__main__':validate()
