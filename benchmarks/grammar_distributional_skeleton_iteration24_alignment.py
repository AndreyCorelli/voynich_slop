"""Post-hoc labeled-readout ceiling; never used by relation/skeleton models.

Twenty target sentences supply property labels only for the class readout.
The remaining eighty are scored with source and adapted readouts, unchanged
profiles and fixed source-trained centroids. This is privileged adaptation.
"""
from benchmarks.grammar_distributional_skeleton_iteration24 import OUT,load,save,phase_views,fit_readouts
from benchmarks.grammar_distributional_skeleton_iteration24_evaluate import readout_metrics
from voynich_smt.distributional_grammar import attach_profiles


def calculate(data,lattice,prototypes,source_readouts):
    result={}
    for split in ('test_jerome','test_caesar'):
        raw,offset=phase_views(data,split,lattice);ss=data[split];rows={}
        for arm in ('baseline','profiles','shuffled_profiles'):
            vv=attach_profiles(raw,prototypes[arm],shuffle=arm=='shuffled_profiles')[offset:] if arm in prototypes else raw[offset:]
            adapted=fit_readouts(ss[:20],vv[:20],arm)
            rows[arm]=dict(adaptation_sentences=20,scored_sentences=80,
                source_mapping=readout_metrics(ss[20:],vv[20:],arm,source_readouts[arm]),
                labeled_target_mapping=readout_metrics(ss[20:],vv[20:],arm,adapted))
        result[split]=rows
    return result

if __name__=='__main__':
    if (OUT/'alignment-diagnostic.json').exists():raise ValueError('Preserve diagnostic')
    result=calculate(load(OUT/'datasets.json'),load(OUT/'morphology-lattice.json'),load(OUT/'prototypes.json'),load(OUT/'readouts.json'))
    save(OUT/'alignment-diagnostic.json',result)
    for split,rows in result.items():
        print(split,{a:{p:(round(v['balanced_accuracy'],3),round(rows[a]['labeled_target_mapping'][p]['balanced_accuracy'],3)) for p,v in rows[a]['source_mapping'].items()} for a in rows})
