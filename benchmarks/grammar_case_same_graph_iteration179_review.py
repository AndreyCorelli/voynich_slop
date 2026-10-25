"""Independent subset sampling, direct metric arithmetic and baseline replay."""
from benchmarks.grammar_case_pair_selection_iteration178_review import independent_metrics
from benchmarks.grammar_case_same_graph_iteration179 import *

def run():
    hashes=groups=0
    for name in ['design-freeze','selection-freeze']:
        for p,h in load(OUT/(name+'.json'))['inputs'].items():assert digest(p)==h;hashes+=1
    selections=load(OUT/'selections.json');summary=load(OUT/'summary.json');contrasts=load(OUT/'contrasts.json');hist=load(OUT/'random-case-edge-inventory.json');features=load(ROOT/'iteration178/features.json');oldsel=load(ROOT/'iteration178/selections.json');baseline=load(ROOT/'iteration178/summary.json');rows=load(ROOT/'iteration172/details.json')
    for pool,nn in selections.items():
        n=len(features[pool]['original']);assert nn['all']==list(range(n))
        for name in ['support10','frequency10']:assert nn[name]==oldsel[pool]['original'][name] and len(nn[name])==10
        assert set(nn)=={'support10','frequency10','all',*('random'+str(seed) for seed in SUBSET_SEEDS)}
        for seed in SUBSET_SEEDS:
            drawn=np.random.default_rng(seed).choice(n,size=10,replace=False);ix=nn['random'+str(seed)];assert ix==sorted(int(i) for i in drawn);assert len(ix)==len(set(ix))==10 and all(0<=i<n for i in ix)
        for name,ix in nn.items():
            for g,rr in rows[pool]['original'].items():
                computed=independent_metrics([rr[i] for i in ix],588 if pool=='earlier' else 857);assert computed==summary[pool][name][g];groups+=1
                if not name.startswith('random'):assert computed==baseline[pool]['original'][name][g]
        for g in GROUPS:assert hist[pool][g]==dict(Counter(str(summary[pool]['random'+str(seed)][g]['case_edges']) for seed in SUBSET_SEEDS))
        for name in ['support10','frequency10']:
            for g in GROUPS:
                for metric in COMPARE:
                    a=summary[pool][name][g][metric];values=[summary[pool]['random'+str(seed)][g][metric] for seed in SUBSET_SEEDS if summary[pool]['random'+str(seed)][g][metric] is not None];tail=sum(v>=a for v in values) if a is not None else None
                    assert contrasts[pool][name][g][metric]==dict(actual=a,nonempty=len(values),mean=sum(values)/len(values) if values else None,min=min(values) if values else None,max=max(values) if values else None,at_least_actual=tail,descriptive_corrected_tail=(1+tail)/(1+len(SUBSET_SEEDS)) if a is not None and len(values)==len(SUBSET_SEEDS) else None)
    save(OUT/'audit.json',dict(input_selection_hashes_verified=hashes,random_subsets_verified=1998,unique_without_replacement_and_frozen_candidates=True,metric_groups_verified=groups,all178_fixed_baselines_exact=True,case_edge_histograms_and_all_contrasts=True))
    print('audit passed',groups,flush=True)
if __name__=='__main__':run()
