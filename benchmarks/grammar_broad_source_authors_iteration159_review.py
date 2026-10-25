"""Independent author projection, references, features and tie bounds."""
from benchmarks.grammar_broad_source_authors_iteration159 import *
from benchmarks.grammar_joint_scalars_iteration142_review import combined

def tie_bounds(pp,labels,k):
    k=min(k,len(pp));cut=sorted(pp.values(),reverse=True)[k-1];above=[w for w,p in pp.items() if p>cut];tied=[w for w,p in pp.items() if p==cut];need=k-len(above);base=sum(labels[w] for w in above);pos=sum(labels[w] for w in tied)
    return dict(n=k,minimum_correct=base+max(0,need-(len(tied)-pos)),maximum_correct=base+min(need,pos),boundary_tied_types=sorted(tied),slots_from_tie=need)

def run():
    hc=fc=pc=mc=0
    for name in ['design-freeze','input-freeze','predictions-freeze']:
        for p,h in load(OUT/(name+'.json'))['inputs'].items():assert digest(p)==h,p;hc+=1
    data=load(ROOT/'iteration44/annotations-truth.json');truth={sid:r['tokens'] for sid,r in data.items()};part=load(ROOT/'iteration49/manifest.json')['partitions']['0'];sel=load(OUT/'selection.json');streams=load(OUT/'streams.json');saved=load(OUT/'features.json');refs=load(OUT/'references.json');pred=load(OUT/'predictions.json');summary=load(OUT/'summary.json');models=load(ROOT/'iteration157/models.json');bounds={};reserved={r['sent_id'] for rows in load('experiments/holdouts/grammar-construction-next.json')['authors'].values() for r in rows};source=set(part['fit']);assert set(sel)==set(AUTHORS);assert load(ROOT/'iteration147/audit.json')['source_fit_tokens']==31884
    for author,s in sel.items():
        sids=[sid for sid in part['calibration']+part['test'] if data[sid]['author']==author and sid not in reserved];assert s['sent_ids']==sids and sids and not set(sids)&(reserved|source);words=[t['word'] for sid in sids for t in truth[sid]];counts=Counter(words);ids=[hashlib.sha256(('author159-'+author+'|'+w).encode()).hexdigest() for w in words];assert ids==streams[author];assert s['tokens']==len(ids) and s['word_types']==len(counts);eligible={w for w,n in counts.items() if n>=5};assert set(s['eligible'])==eligible==set(refs[author]);wanted={r['opaque'] for r in s['eligible'].values()};f=combined(ids,wanted);assert set(f)==set(saved[author])
        for i,r in f.items():
            for c in r:assert abs(r[c]-saved[author][i][c])<1e-11
            fc+=1
        cc={}
        for sid in sids:
            for t in truth[sid]:cc.setdefault(t['word'],Counter())[t['pos']]+=1
        for w in eligible:
            tag=sorted(cc[w],key=lambda p:(-cc[w][p],p))[0];n=cc[w][tag];assert refs[author][w]==dict(modal=tag,n=counts[w],purity=n/counts[w],label=int(tag in POSITIVE),pos_counts=dict(cc[w]));assert s['eligible'][w]==dict(opaque=hashlib.sha256(('author159-'+author+'|'+w).encode()).hexdigest(),n=counts[w])
        labels={w:r['label'] for w,r in refs[author].items()};bounds[author]={}
        for scale,arms in pred[author].items():
            bounds[author][scale]={}
            for name,pp in arms.items():
                assert set(pp)==eligible;m=models[name]['final'];bounds[author][scale][name]={str(k):tie_bounds(pp,labels,k) for k in [5,10,20,50]}
                for w,p in pp.items():
                    v=dict(f[s['eligible'][w]['opaque']]);v['frequency']=math.log1p(counts[w]*(1 if scale=='raw' else 31884/len(ids)));x=(np.array([v[c] for c in m['columns']])-m['mean'])/m['scale'];q=float(expit(m['beta'][0]+x@np.array(m['beta'][1:])));assert abs(q-p)<1e-9;pc+=1
                mm=summary[author][scale][name];assert mm==detection_metrics(pp,labels);yy=[w for w in pp if labels[w]];nn=[w for w in pp if not labels[w]];auc=sum((pp[a]>pp[b])+.5*(pp[a]==pp[b]) for a in yy for b in nn)/(len(yy)*len(nn));assert abs(auc-mm['auc'])<1e-12;mc+=1
    save(OUT/'tie-bounds.json',bounds);save(OUT/'audit.json',dict(input_hashes_verified=hc,author_sets_verified=2,source_and_reserve_overlap=0,all_supported_types_referenced=True,independent_feature_vectors=fc,probabilities_independently_replayed=pc,metric_groups_replayed=mc,all_top_budgets_tie_bounds_recorded=True,no_fitting=True))
if __name__=='__main__':run()
