"""Post-primary source-sample sensitivity; no parameter or arm selection."""
import numpy as np
from benchmarks.grammar_predicate_case_iteration41 import OUT,load,save,metrics
from voynich_smt.predicate_case import fit,probability


def run():
    rec=load(OUT/'records-truth.json');source=rec['source']['oracle'];sids=sorted({r['sent_id'] for r in source});groups={sid:[r for r in source if r['sent_id']==sid] for sid in sids};rng=np.random.default_rng(41414);samples={a:[] for a in ('Jerome','Caesar')}
    for _ in range(2000):
        selected=rng.choice(sids,len(sids),replace=True);model=fit([r for sid in selected for r in groups[sid]],4.)
        for author in samples:
            rows=rec[author]['oracle'];p=[probability(model,r['predicate']) for r in rows];base=[model['base']]*len(rows);m=metrics(rows,p);b=metrics(rows,base);samples[author].append([m['accuracy']-b['accuracy'],b['log_loss']-m['log_loss']])
    result=dict(note='Post-primary source-only sentence-cluster bootstrap2000; refit fixed mass4 and its baseline each draw, fixed target queries. Sensitivity to source sampling, not combined uncertainty or new heldout validation.',source_sentences_with_eligible_in=len(sids),authors={a:dict(accuracy_gain95=np.quantile(v,[.025,.975],axis=0)[:,0].tolist(),logloss_reduction95=np.quantile(v,[.025,.975],axis=0)[:,1].tolist()) for a,v in samples.items()})
    save(OUT/'source-bootstrap.json',result);print(result)
if __name__=='__main__':run()
