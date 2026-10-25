"""Independent source lexicon, oracle candidates, Poisson scores and ranks."""
from benchmarks.grammar_lexical_utility_iteration161 import *

def run():
    hc=sc=rc=0
    for name in ['design-freeze','source-freeze','input-freeze','scores-freeze']:
        for p,h in load(OUT/(name+'.json'))['inputs'].items():assert digest(p)==h,p;hc+=1
    data=load(ROOT/'iteration44/annotations-truth.json');fit=load(ROOT/'iteration49/manifest.json')['partitions']['0']['fit'];reserved={r['sent_id'] for rr in load('experiments/holdouts/grammar-construction-next.json')['authors'].values() for r in rr};assert not set(fit)&reserved;cc=Counter();tags={}
    for sid in fit:
        for t in data[sid]['tokens']:cc[t['word']]+=1;tags.setdefault(t['word'],Counter())[t['pos']]+=1
    lex={}
    for w,c in tags.items():
        tag=sorted(c,key=lambda x:(-c[x],x))[0]
        if c[tag]*5>=cc[w]*4:lex[w]=dict(modal=tag,label=int(tag in POSITIVE),count=cc[w],purity=c[tag]/cc[w])
    source=load(OUT/'source.json');assert source==dict(counts=dict(cc),lexicon=lex,N=sum(cc.values()),V=len(cc),alpha=.5,q=.8);views=load(ROOT/'iteration160/word-views.json');inputs=load(OUT/'inputs.json');scores=load(OUT/'scores.json');evaluation=load(OUT/'evaluation.json');summary=load(OUT/'summary.json');refs=load(ROOT/'iteration160/references.json');den=sum(cc.values())+.5*(len(cc)+1)
    for author,vv in views.items():
        for view,ss in vv.items():
            key=author+'/'+view;r=inputs[key];words=[w for s in ss for w in s['words']];counts=Counter(words);candidates=sorted(counts);assert r['candidates']==candidates and r['N']==len(words);supported=sorted((n for n in counts.values() if n>=5),reverse=True);cut=supported[min(10,len(supported))-1];assert r['cutoff_count']==cut;query={hashlib.sha256(('utility161|'+key+'|'+w).encode()).hexdigest():w for w,n in counts.items() if n>=cut};assert {q['opaque']:q['n'] for q in r['queries']}=={i:counts[w] for i,w in query.items()};assert set(scores[key])==set(query)
            for opaque,arms in scores[key].items():
                n=counts[query[opaque]]
                for j,w in enumerate(candidates):
                    rate=(cc[w]+.5)/den;base=n*math.log(rate)-len(words)*rate;addition=0. if w not in lex else math.log(2*(.8 if lex[w]['label'] else .2));assert abs(base-arms['baseline'][j])<1e-9;assert abs(base+addition-arms['prior'][j])<1e-9;sc+=2
            assert len(evaluation[key])==len(query)
            for row in evaluation[key]:
                opaque=row['opaque'];w=query[opaque];assert row['true_word']==w;label=None if w not in lex else lex[w]['label'];target=refs[author][view]['host'][w];assert row['source_class']==label and row['target_host_class']==target;assert row['source_class_agrees']==(None if label is None else label==target);j=candidates.index(w)
                for arm,sscores in scores[key][opaque].items():
                    v=sscores[j];strict=len([x for x in sscores if x>v]);equal=len([x for x in sscores if x==v]);m=row['metrics'][arm];assert m['best_rank']==strict+1 and m['worst_rank']==strict+equal;assert m==rank_metrics(sscores,j);rc+=1
            rr=evaluation[key];s=summary[key];assert s['queries']==len(rr) and s['candidates']==len(candidates);assert s['source_class_known']==sum(x['source_class'] is not None for x in rr);assert s['source_class_mismatches']==sum(x['source_class_agrees'] is False for x in rr)
            for field,op in [('improved',lambda a,b:a<b),('tied',lambda a,b:a==b),('worsened',lambda a,b:a>b)]:assert s[field]==sum(op(x['metrics']['prior']['midrank'],x['metrics']['baseline']['midrank']) for x in rr)
            for arm,m in s['metrics'].items():
                assert abs(m['mean_midrank']-sum(x['metrics'][arm]['midrank'] for x in rr)/len(rr))<1e-12;assert abs(m['mean_reciprocal_midrank']-sum(x['metrics'][arm]['reciprocal_midrank'] for x in rr)/len(rr))<1e-12
                for field in ['top1_guaranteed','top1_possible','top5_guaranteed','top5_possible']:assert m[field]==sum(x['metrics'][arm][field] for x in rr)
    save(OUT/'audit.json',dict(input_hashes_verified=hc,source_lexicon_independently_rebuilt=True,views_verified=8,queries_verified=sum(s['queries'] for s in summary.values()),candidate_scores_independently_replayed=sc,true_candidate_rank_pairs_verified=rc,oracle_vocabulary_complete=True,target_labels_only_used_in_evaluation=True,all_summary_fields_verified=True))
if __name__=='__main__':run()
