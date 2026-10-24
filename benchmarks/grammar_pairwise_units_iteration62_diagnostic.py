"""Post-evaluation training-only diagnosis; no model or policy changes."""
import numpy as np
from benchmarks.grammar_pairwise_units_iteration62 import OUT,MORPH,SOURCE,LOSSES,load,save,prepare
from voynich_smt.pairwise_units import pairs
from voynich_smt.typed_predicate_units import select


def run():
    data=load(SOURCE);parts=load(MORPH/'manifest.json')['partitions'];models=load(OUT/'models.json');result={}
    for f in range(5):
        frames,_=prepare(parts[str(f)]['fit'],data);records=models[str(f)];base=records['unweighted']['model']['weights'];result[str(f)]={}
        for mode in ('pair_all','pair_hard'):
            d,p,_=pairs(frames,mode,base);comparisons={}
            for loss in ('unweighted',mode):
                weights=np.asarray(records[loss]['model']['weights']);margin=d@weights
                comparisons[loss]=dict(weighted_pair_correct=float(p@(margin>1e-10)/p.sum()),weighted_pair_tied=float(p@(np.abs(margin)<=1e-10)/p.sum()))
            result[str(f)][mode]=dict(pair_evaluation=comparisons,full_candidate_fit_accuracy={})
            for loss in ('unweighted',mode):
                weights=np.asarray(records[loss]['model']['weights']);correct=0
                for r in frames:
                    correct+=select(r['x']@weights,r['options'],r['gold'][0],r['gold'][2])==r['gold']
                result[str(f)][mode]['full_candidate_fit_accuracy'][loss]=dict(correct=correct,n=len(frames))
    save(OUT/'training-diagnostics.json',dict(posthoc=True,scope='fit frames only; no retuning',folds=result));print(result)
if __name__=='__main__':run()
