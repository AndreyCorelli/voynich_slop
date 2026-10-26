"""Independent POS-field projection, stratum partitions and word/POS null replay."""
import re,random,itertools
from collections import Counter,defaultdict
from benchmarks.grammar_dante_pos_profile_iteration200 import OUT,BASE,COVER,SEEDS,Path,load,save,digest,GROUPS,TAGS
from benchmarks.grammar_case_applicability_iteration180_review import close
from benchmarks.grammar_consensus_core_iteration195_review import scalar_metrics
CASES={'Nom','Gen','Dat','Acc','Abl','Voc','Loc'}

def scalar_scores(dd,cc,tt):
    result={k:[] for k in GROUPS}
    for e in dd:
        bygroup={k:[] for k in GROUPS}
        for f in e['frames']:
            counts={k:[0,0,0] for k in GROUPS}
            for i in f['a_positions']:
                for j in f['b_positions']:
                    n=(tt[i] in {'PRON','DET'})+(tt[j] in {'PRON','DET'});family={0:'neither_pd',1:'exactly_one_pd',2:'both_pd'}[n];valid=cc[i] in CASES and cc[j] in CASES;match=valid and cc[i]==cc[j]
                    for group in ['all',family]+(['pd_involving'] if n else []):counts[group][0]+=1;counts[group][1]+=int(valid);counts[group][2]+=int(match)
            for k in range(3):
                assert counts['all'][k]==sum(counts[g][k] for g in ['both_pd','exactly_one_pd','neither_pd']);assert counts['pd_involving'][k]==counts['both_pd'][k]+counts['exactly_one_pd'][k]
            for g in GROUPS:bygroup[g].append(counts[g])
        for g,counts in bygroup.items():
            total=sum(c[0] for c in counts);valid=sum(c[1] for c in counts);matched=sum(c[2] for c in counts);fractions=[c[2]/c[1] for c in counts if c[1]]
            result[g].append(dict(a=e['a'],b=e['b'],shared_frames=e['shared_frames'],case_frames=len(fractions),all_occurrence_pairs=total,case_occurrence_pairs=valid,matching_case_pairs=matched,frame_macro_case_agreement=sum(fractions)/len(fractions) if fractions else None,no_case_conflicts=matched==valid if valid else None))
    return result

def aggregate(rows,ix):
    active=[rows[i] for i in ix if rows[i]['all_occurrence_pairs']>0];valid=[r for r in active if r['case_occurrence_pairs']>0];total=sum(r['all_occurrence_pairs'] for r in active);pairs=sum(r['case_occurrence_pairs'] for r in active);match=sum(r['matching_case_pairs'] for r in active);score=sum(r['frame_macro_case_agreement'] for r in valid)
    return dict(selected_graph_edges=len(ix),active_stratum_edges=len(active),case_edges=len(valid),case_edge_applicability=len(valid)/len(active) if active else None,active_endpoint_types=len(set(itertools.chain.from_iterable((r['a'],r['b']) for r in active))),case_endpoint_types=len(set(itertools.chain.from_iterable((r['a'],r['b']) for r in valid))),all_occurrence_pairs=total,case_occurrence_pairs=pairs,matching_case_pairs=match,case_pair_fraction=pairs/total if total else None,conditional_frame_case_equality=score/len(valid) if valid else None,pooled_case_equality=match/pairs if pairs else None,joint_yield_over_selected_graph_edges=score/len(ix) if ix else None)

def run():
    assert not (OUT/'audit.json').exists();hashes=0
    for p,h in load(OUT/'design-freeze.json')['inputs'].items():assert digest(Path(p))==h;hashes+=1
    for p,h in load(OUT/'selection-freeze.json').items():assert digest(OUT/p)==h;hashes+=1
    for p,h in load(BASE/'verification-manifest.json').items():assert digest(Path(p))==h;hashes+=1
    assert (OUT/'selection-freeze.json').stat().st_mtime_ns <= (OUT/'pos-references.json').stat().st_mtime_ns
    lists=load(OUT/'selections.json');assert lists==load(BASE/'selections.json');g=load(COVER/'graphs.json')['primary'];dd=g['descriptors'];cc=load(BASE/'case-references.json')['case_by_stream_position'];wanted={(r['path'],r['sent_id']) for r in load(COVER/'admitted-sentences.json')};pos={};counts=Counter()
    for path in sorted({p for p,s in wanted}):
        for block in Path(path).read_text().strip().split('\n\n'):
            lines=block.splitlines();sid=next((x.split('=',1)[1].strip() for x in lines if x.startswith('# sent_id =')),None)
            if (path,sid) not in wanted:continue
            for line in lines:
                m=re.match(r'^(\d+)\t(?:[^\t]*\t){2}([^\t]*)\t',line)
                if m:assert m[2] in TAGS;pos[(path,sid,int(m[1]))]=m[2];counts[m[2]]+=1
    tt=[pos[tuple(p)] if p else 'X' for p in g['positions']];assert load(OUT/'pos-references.json')==dict(pos_by_stream_position=tt,admitted_integer_rows=len(pos),raw_pos_counts=dict(counts),reference_only=True)
    rows=scalar_scores(dd,cc,tt);close(rows,load(OUT/'case-stratum-details.json'));close(rows['all'],load(BASE/'case-details.json'));summary={name:{s:aggregate(rows[s],ix) for s in GROUPS} for name,ix in lists.items()};close(summary,load(OUT/'summary.json'))
    expectedcomposition={};keys=['/'.join(pair) for pair in itertools.combinations_with_replacement(sorted(TAGS),2)]
    for name,ix in lists.items():
        comp={k:dict(all_pairs=0,case_pairs=0,matching_cases=0) for k in keys}
        for i in ix:
            for f in dd[i]['frames']:
                for a,b in itertools.product(f['a_positions'],f['b_positions']):
                    r=comp['/'.join(sorted([tt[a],tt[b]]))];r['all_pairs']+=1
                    if cc[a] in CASES and cc[b] in CASES:r['case_pairs']+=1;r['matching_cases']+=int(cc[a]==cc[b])
        expectedcomposition[name]=comp
    assert expectedcomposition==load(OUT/'pos-pair-composition.json')
    old=load(BASE/'summary.json')
    for name,ix in lists.items():close(scalar_metrics([rows['all'][i] for i in ix],old['eligible_candidate_endpoint_types']),old['lists'][name])
    buckets=defaultdict(list);byword=defaultdict(set)
    for i,p in enumerate(g['positions']):
        if p:buckets[(g['ids'][i],tt[i])].append(i);byword[g['ids'][i]].add(tt[i])
    assert load(OUT/'bucket-summary.json')==dict(lexical_word_types=len(byword),word_pos_buckets=len(buckets),multi_pos_word_types=sum(len(v)>1 for v in byword.values()),permutable_buckets=sum(len(set(cc[i] for i in pp))>1 for pp in buckets.values()))
    nulls=load(OUT/'word-pos-profile-nulls.json');assert set(nulls)==set(map(str,SEEDS));regenerated={}
    for seed in SEEDS:
        rng=random.Random(seed);pc=cc.copy()
        for key,pp in sorted(buckets.items()):
            vals=list(map(cc.__getitem__,pp));rng.shuffle(vals)
            for i,c in zip(pp,vals):pc[i]=c
            assert Counter(pc[i] for i in pp)==Counter(cc[i] for i in pp)
        nr=scalar_scores(dd,pc,tt);metrics={name:{s:aggregate(nr[s],ix) for s in GROUPS} for name,ix in lists.items()};close(metrics,nulls[str(seed)]);regenerated[str(seed)]=metrics
    comp={}
    for name,groups in summary.items():
        comp[name]={}
        for group,actual in groups.items():
            comp[name][group]={}
            for metric in ['case_edge_applicability','conditional_frame_case_equality','joint_yield_over_selected_graph_edges']:
                values=[n[name][group][metric] for n in regenerated.values() if n[name][group][metric] is not None];a=actual[metric];comp[name][group][metric]=dict(actual=a,nonempty_nulls=len(values),min=min(values) if values else None,max=max(values) if values else None,mean=sum(values)/len(values) if values else None,at_least_actual=sum(v>=a for v in values) if a is not None else None)
    close(comp,load(OUT/'null-comparisons.json'))
    save(OUT/'audit.json',dict(passed=True,hashes_verified=hashes,raw_pos_integer_rows_replayed=len(pos),real_stratum_edge_scores=len(dd)*len(GROUPS),real_stratum_metric_groups=len(lists)*len(GROUPS),pos_pair_composition_cells=len(lists)*len(keys),strict_null_seeds=len(SEEDS),null_stratum_metric_groups=len(SEEDS)*len(lists)*len(GROUPS),null_stratum_edge_scores=len(SEEDS)*len(dd)*len(GROUPS),all_word_pos_case_profiles_preserved=True,all_pair_count_partitions_replayed=True,all_199_baselines_and_predictions_unchanged=True,no_model_fit_or_pos_prediction=True))
    print(load(OUT/'audit.json'))
if __name__=='__main__':run()
