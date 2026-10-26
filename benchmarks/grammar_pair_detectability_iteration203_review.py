"""Independent count-product Case scoring, permutations and corrected tails."""
import random,math
from collections import Counter,defaultdict
from benchmarks.grammar_pair_detectability_iteration203 import OUT,BASE,LABEL,SLOTS,AUTHORS,SEEDS,ALPHA,EPS,CASES,Path,load,save,digest
from benchmarks.grammar_case_applicability_iteration180_review import close

def observed_stat(edges,cases):
    result=[]
    for edge in edges:
        fractions=[]
        for frame in edge['frames']:
            a=Counter(cases[i] for i in frame['a_positions']);b=Counter(cases[i] for i in frame['b_positions']);matching=sum(a[c]*b[c] for c in CASES);fractions.append(matching/(len(frame['a_positions'])*len(frame['b_positions'])))
        result.append(sum(fractions)/len(fractions))
    return result

def pvalue(null,real):return (1+len([x for x in null if x>=real-EPS]))/(len(null)+1)

def run():
    assert not (OUT/'audit.json').exists();hashes=0
    for p,h in load(OUT/'design-freeze.json')['inputs'].items():assert digest(Path(p))==h;hashes+=1
    for p,h in load(OUT/'selection-freeze.json').items():assert digest(OUT/p)==h;hashes+=1
    for folder in [LABEL,SLOTS]:
        for p,h in load(folder/'verification-manifest.json').items():assert digest(Path(p))==h;hashes+=1
    source201=load(LABEL/'evaluation-selections.json');source202=load(SLOTS/'selections.json');fixed=load(OUT/'fixed-lists.json');graphs=load(BASE/'graphs.json');refs=load(LABEL/'development-references.json');labels=load(LABEL/'labels.json');matrices=load(OUT/'null-surplus-matrices.json');details=load(OUT/'edge-details.json');summary=load(OUT/'summary.json');liststats=load(OUT/'fixed-list-detectability.json');edges=groups=0
    for author in AUTHORS:
        assert fixed[author]=={**{'201/'+n:ix for n,ix in source201[author].items()},**{'202/'+n:ix for n,ix in source202[author].items()}}
        g=graphs[author];ref=refs[author];dd=g['descriptors'];expected=[r['expected_frame_macro_joint_matching'] for r in labels[author]];observed=[v-e for v,e in zip(observed_stat(dd,ref['case']),expected)];close(observed,[r['surplus'] for r in labels[author]])
        buckets=defaultdict(list)
        for i,p in enumerate(g['positions']):
            if p:buckets[(g['ids'][i],ref['pos'][i])].append(i)
        regenerated=[]
        for seed in SEEDS:
            rng=random.Random(seed);cases=ref['case'].copy()
            for key,positions in sorted(buckets.items()):
                original=[ref['case'][i] for i in positions];values=original.copy();rng.shuffle(values)
                for i,v in zip(positions,values):cases[i]=v
                assert Counter(cases[i] for i in positions)==Counter(original)
            regenerated.append([v-e for v,e in zip(observed_stat(dd,cases),expected)])
        close(regenerated,matrices[author]);maxima=[max(row) for row in regenerated];means=[sum(row)/len(row) for row in regenerated];computed=[]
        for i,label in enumerate(labels[author]):
            null=[row[i] for row in regenerated];mean=sum(null)/len(null);var=sum((x-mean)**2 for x in null)/len(null);raw=pvalue(null,observed[i]);adjusted=pvalue(maxima,observed[i]);assert adjusted+EPS>=raw
            computed.append(dict(edge=i,a=label['a'],b=label['b'],surplus=observed[i],positive_surplus=observed[i]>EPS,raw_tail=raw,max_stat_tail=adjusted,raw_detected=raw<=ALPHA and observed[i]>EPS,adjusted_detected=adjusted<=ALPHA and observed[i]>EPS,null_min=min(null),null_max=max(null),null_mean=mean,sampled_null_variance=var,sampled_zero_variance=var<=1e-24))
        close(computed,details[author]);edgecount=len(dd);o=sum(observed)/len(observed);raw=[r for r in computed if r['raw_detected']];adj=[r for r in computed if r['adjusted_detected']];computedsummary=dict(edges=edgecount,positive_surplus=sum(x>EPS for x in observed),negative_surplus=sum(x<-EPS for x in observed),zero_surplus=sum(abs(x)<=EPS for x in observed),raw_detected=len(raw),max_stat_detected=len(adj),raw_detected_endpoint_types=len({r[k] for r in raw for k in ['a','b']}),adjusted_detected_endpoint_types=len({r[k] for r in adj for k in ['a','b']}),sampled_zero_variance=sum(r['sampled_zero_variance'] for r in computed),aggregate_mean_surplus=o,aggregate_tail=pvalue(means,o),null_aggregate_min=min(means),null_aggregate_max=max(means),null_max_stat_min=min(maxima),null_max_stat_max=max(maxima));close(computedsummary,summary[author])
        for name,ix in fixed[author].items():
            rr=[computed[i] for i in ix];stats=dict(selected=len(ix),positive_surplus=sum(r['positive_surplus'] for r in rr),raw_detected=sum(r['raw_detected'] for r in rr),max_stat_detected=sum(r['adjusted_detected'] for r in rr),sampled_zero_variance=sum(r['sampled_zero_variance'] for r in rr),mean_surplus=sum(r['surplus'] for r in rr)/len(ix) if ix else None);close(stats,liststats[author][name]);groups+=1
        edges+=edgecount
    save(OUT/'audit.json',dict(passed=True,hashes_verified=hashes,real_edges_replayed=edges,null_seeds_per_author=len(SEEDS),null_edges_replayed=edges*len(SEEDS),fixed_list_groups_replayed=groups,all_case_word_pos_profiles_preserved=True,all_raw_and_maxstat_tails_replayed=True,maxstat_tails_never_smaller_than_raw=True,no_fitting_new_gold_or_reserved_data=True))
    print(load(OUT/'audit.json'))
if __name__=='__main__':run()
