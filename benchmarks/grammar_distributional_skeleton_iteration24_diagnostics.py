"""Descriptive cluster information audit; no refitting or policy changes."""
from collections import Counter,defaultdict
import math
import numpy as np
from benchmarks.grammar_distributional_skeleton_iteration24 import OUT,load,save,phase_views,property_label,readout_key
from voynich_smt.distributional_grammar import attach_profiles


def mutual_information(classes,labels):
    n=len(labels);cx=Counter(classes);cy=Counter(labels);joint=Counter(zip(classes,labels));mi=0.
    for (x,y),count in joint.items():mi+=count/n*math.log(count*n/(cx[x]*cy[y]))
    entropy=-sum(count/n*math.log(count/n) for count in cy.values())
    return mi/entropy if entropy else 0.


def calculate(data,lattice,prototypes):
    result={}
    for split in ('train','test_jerome','test_caesar'):
        raw,offset=phase_views(data,split,lattice);rows={}
        for arm in ('baseline','profiles','shuffled_profiles'):
            vv=attach_profiles(raw,prototypes[arm],shuffle=arm=='shuffled_profiles')[offset:] if arm in prototypes else raw[offset:]
            properties={}
            for property in ('upos','case','number'):
                clusters=[];labels=[]
                for s,v in zip(data[split],vv):
                    for pos in range(len(s['tokens'])):
                        label=property_label(s,pos,property)
                        if label is None:continue
                        clusters.append(readout_key(v,pos,arm));labels.append(label)
                counts=Counter(clusters);observed=mutual_information(clusters,labels);rng=np.random.default_rng(24077)
                null=[mutual_information(clusters,rng.permutation(labels).tolist()) for _ in range(100)]
                properties[property]=dict(queries=len(labels),occupied_classes=len(counts),largest_class_share=max(counts.values())/len(labels),
                    normalized_label_information=observed,shuffled_label_mean=float(np.mean(null)),
                    permutation_fraction_ge=(1+sum(x>=observed-1e-12 for x in null))/101,
                    caveat='Descriptive token permutation with fixed clusters; ignores sentence dependence and is not a generalization estimate.')
            rows[arm]=properties
        result[split]=rows
    return result

if __name__=='__main__':
    if (OUT/'class-diagnostics.json').exists():raise ValueError('Preserve saved diagnostics')
    result=calculate(load(OUT/'datasets.json'),load(OUT/'morphology-lattice.json'),load(OUT/'prototypes.json'))
    save(OUT/'class-diagnostics.json',result)
    for split,rows in result.items():
        print(split,{a:{p:round(v['normalized_label_information'],3) for p,v in props.items()} for a,props in rows.items()})
