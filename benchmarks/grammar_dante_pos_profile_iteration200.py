"""Reference-only POS composition and word x POS Case-profile control on fixed Dante outputs."""
import re,random
from collections import Counter,defaultdict
from benchmarks.grammar_dante_case_transfer_iteration199 import ROOT,Path,load,save,digest
from benchmarks.grammar_case_subfamilies_iteration172 import score,composition,GROUPS,TAGS
from benchmarks.grammar_multi_author_review192_193 import listmetrics
OUT=ROOT/'iteration200';BASE=ROOT/'iteration199';COVER=ROOT/'iteration198';SEEDS=list(range(19900,20099))
POLICY='Follow-up, NOT fresh validation: freeze unchanged199 graph/models/outputs/11selections and strata all,pd_involving,both_pd,exactly_one_pd,neither_pd (PD=PRON/DET) before first admittedDante POS decode. Decode UPOS only on198 admitted DVE+Mon sentence IDs; reuse199 Case stream, other reserves unchanged. All17tagpair composition (153unordered combinations includingzeros) for every fixedlist; stratum eligibility = >=1occurrencecomparison in stratum, not new graph support2 requirement. Report active and case edges/endpoint types/paircounts/conditional frame equality/selectedgraph jointyield, all sparse/empty cases; all-group exact199 metrics required. Fixed199seeds19900..20098 shuffle Case INCLUDINGmissing among all lexical occurrences within each (opaque word,POS) bucket. Preserve every bucket profile, no new graph/features/probabilities/training/selection or family selection. Real/null scoring samefixed lists/strata, tails descriptive not universal confidence or model POS restoration. Primary fullgraph all equality versuswordPOSnull; required primary rank-rich top10 and allotherlists/strata. POS is reference only, targetCase/POS consumed for followup and never fed to frozenmodels; no letters/quarantines/Seneca reference access.'

def group_metrics(rows,indices):
    chosen=[rows[i] for i in indices];active=[r for r in chosen if r['all_occurrence_pairs']];covered=[r for r in active if r['case_occurrence_pairs']];n=len(indices);nt=len(active);nc=len(covered);total=sum(r['frame_macro_case_agreement'] for r in covered);pairs=sum(r['all_occurrence_pairs'] for r in active);valid=sum(r['case_occurrence_pairs'] for r in active);matched=sum(r['matching_case_pairs'] for r in active)
    return dict(selected_graph_edges=n,active_stratum_edges=nt,case_edges=nc,case_edge_applicability=nc/nt if nt else None,active_endpoint_types=len({r[k] for r in active for k in ['a','b']}),case_endpoint_types=len({r[k] for r in covered for k in ['a','b']}),all_occurrence_pairs=pairs,case_occurrence_pairs=valid,matching_case_pairs=matched,case_pair_fraction=valid/pairs if pairs else None,conditional_frame_case_equality=total/nc if nc else None,pooled_case_equality=matched/valid if valid else None,joint_yield_over_selected_graph_edges=total/n if n else None)

def read_pos(path,wanted):
    sid=None
    with path.open() as f:
        for line in f:
            if line.startswith('# sent_id ='):sid=line.split('=',1)[1].strip()
            elif line.startswith('#') or not line.strip() or sid not in wanted:continue
            else:
                tabs=[i for i,c in enumerate(line) if c=='\t'];assert len(tabs)==9;identifier=line[:tabs[0]]
                if identifier.isdigit():yield (str(path),sid,int(identifier)),line[tabs[2]+1:tabs[3]]

def run():
    assert not OUT.exists();OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),Path('benchmarks/grammar_case_subfamilies_iteration172.py')]+[BASE/n for n in ['verification-manifest.json','selections.json','outputs.json','models.json','case-references.json','case-details.json','summary.json']]+[COVER/n for n in ['graphs.json','admitted-sentences.json']]
    paths +=[Path(p) for p in sorted({r['path'] for r in load(COVER/'admitted-sentences.json')})]
    save(OUT/'design-freeze.json',dict(policy=POLICY,seeds=SEEDS,inputs={str(p):digest(p) for p in paths}))
    for p,h in load(BASE/'verification-manifest.json').items():assert digest(Path(p))==h
    lists=load(BASE/'selections.json');save(OUT/'selections.json',lists);save(OUT/'selection-freeze.json',{'selections.json':digest(OUT/'selections.json')})
    g=load(COVER/'graphs.json')['primary'];dd=g['descriptors'];cc=load(BASE/'case-references.json')['case_by_stream_position'];admitted=load(COVER/'admitted-sentences.json');wanted=defaultdict(set)
    for r in admitted:wanted[r['path']].add(r['sent_id'])
    pos={};counts=Counter()
    for path,sids in wanted.items():
        for key,tag in read_pos(Path(path),sids):assert tag in TAGS,(key,tag);pos[key]=tag;counts[tag]+=1
    tt=[pos[tuple(p)] if p else 'X' for p in g['positions']];save(OUT/'pos-references.json',dict(pos_by_stream_position=tt,admitted_integer_rows=len(pos),raw_pos_counts=dict(counts),reference_only=True))
    detail=score(dd,cc,tt);assert detail['all']==load(BASE/'case-details.json');save(OUT/'case-stratum-details.json',detail)
    summary={name:{group:group_metrics(detail[group],ix) for group in GROUPS} for name,ix in lists.items()};comp={name:composition([dd[i] for i in ix],cc,tt) for name,ix in lists.items()};save(OUT/'summary.json',summary);save(OUT/'pos-pair-composition.json',comp)
    old=load(BASE/'summary.json')['lists'];eligible=load(BASE/'summary.json')['eligible_candidate_endpoint_types']
    for name,ix in lists.items():assert listmetrics([detail['all'][i] for i in ix],eligible)==old[name]
    buckets=defaultdict(list);byword=defaultdict(set)
    for i,p in enumerate(g['positions']):
        if p:buckets[(g['ids'][i],tt[i])].append(i);byword[g['ids'][i]].add(tt[i])
    save(OUT/'bucket-summary.json',dict(lexical_word_types=len(byword),word_pos_buckets=len(buckets),multi_pos_word_types=sum(len(v)>1 for v in byword.values()),permutable_buckets=sum(len(set(cc[i] for i in pp))>1 for pp in buckets.values())))
    nulls={}
    for seed in SEEDS:
        rng=random.Random(seed);permuted=cc.copy()
        for key in sorted(buckets):
            pp=buckets[key];values=[cc[i] for i in pp];rng.shuffle(values)
            for i,c in zip(pp,values):permuted[i]=c
        nr=score(dd,permuted,tt);nulls[str(seed)]={name:{group:group_metrics(nr[group],ix) for group in GROUPS} for name,ix in lists.items()}
    save(OUT/'word-pos-profile-nulls.json',nulls)
    comparison={}
    for name,ss in summary.items():
        comparison[name]={}
        for group,actual in ss.items():
            comparison[name][group]={}
            for key in ['case_edge_applicability','conditional_frame_case_equality','joint_yield_over_selected_graph_edges']:
                values=[v[name][group][key] for v in nulls.values() if v[name][group][key] is not None];a=actual[key];comparison[name][group][key]=dict(actual=a,nonempty_nulls=len(values),min=min(values) if values else None,max=max(values) if values else None,mean=sum(values)/len(values) if values else None,at_least_actual=sum(v>=a for v in values) if a is not None else None)
    save(OUT/'null-comparisons.json',comparison)
    print('buckets',load(OUT/'bucket-summary.json'),flush=True)
    for name in ['all_candidates','rank_rich/top10']:
        print(name,summary[name],flush=True);print('null',name,comparison[name],flush=True)
if __name__=='__main__':run()
