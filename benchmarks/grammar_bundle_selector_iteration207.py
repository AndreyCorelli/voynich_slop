"""Fixed anonymous bundle selector, development-only author-held-out pilot."""
from benchmarks.grammar_multi_author_iteration193 import weighted_fit
from benchmarks.grammar_case_applicability_iteration180 import ROOT,load,save,digest,predict,evaluate
from pathlib import Path
from collections import Counter,defaultdict
import math
OUT=ROOT/'iteration207'
AUTHORS=['Aquinas','Caesar','Cicero','Jerome']
NAMES=['log_frequency','log1p_degree','log1p_shared_frames','log1p_queried_pivots','occurrence_reuse','queried_fraction','mean_log_partner_frequency','mean_log1p_partner_degree','left_entropy','right_entropy','joint_entropy','joint_unique_fraction']

def features(g,bb):
    ids=g['ids'];pp=g['positions'];edges=g['descriptors'];counts=Counter(ids);degree=Counter();contexts=defaultdict(list)
    for e in edges:
        degree.update([e['a'],e['b']])
    for i in range(1,len(ids)-1):
        if pp[i-1] and pp[i] and pp[i+1]:contexts[ids[i]].append((ids[i-1],ids[i+1]))
    out=[]
    for b in bb:
        w=b['word'];partners=[edges[j]['b'] if edges[j]['a']==w else edges[j]['a'] for j in b['edges']];cc=contexts[w];n=len(cc)
        def h(c):return -sum(v/n*math.log(v/n) for v in Counter(c).values())/math.log(n) if n>1 else 0.
        vals=[math.log(counts[w]),math.log1p(b['degree']),math.log1p(b['unique_frames']),math.log1p(b['unique_pivot_occurrences']),b['pivot_occurrence_reuse'],b['unique_pivot_occurrences']/counts[w],sum(math.log(counts[x]) for x in partners)/len(partners),sum(math.log1p(degree[x]) for x in partners)/len(partners),h([x[0] for x in cc]),h([x[1] for x in cc]),h(cc),len(set(cc))/n if n else 0.]
        out.append(dict(word=w,values=vals))
    return out

def top(scores,k):
    cut=sorted(scores,reverse=True)[min(k,len(scores))-1]
    return [i for i,s in enumerate(scores) if s>=cut]

def metrics(y,s,ix):
    p=sum(y[i] for i in ix);pos=[s[i] for i,v in enumerate(y) if v];neg=[s[i] for i,v in enumerate(y) if not v]
    auc=sum((a>b)+.5*(a==b) for a in pos for b in neg)/(len(pos)*len(neg)) if pos and neg else None
    return dict(selected=len(ix),supported=p,precision=p/len(ix) if ix else None,recall=p/sum(y) if sum(y) else None,coverage=len(ix)/len(y),auc=auc)

def run():
    assert not OUT.exists();OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    inputs=[Path(__file__),Path('benchmarks/grammar_multi_author_iteration193.py'),Path('benchmarks/grammar_case_applicability_iteration180.py'),ROOT/'iteration193/graphs.json',ROOT/'iteration205/candidates.json',ROOT/'iteration205/details.json',ROOT/'iteration205/verification-manifest.json']
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in inputs},features=NAMES,policy='Conservative205 bundles; fixed full12/count-first4 logistic meanNLL+.05 slope norm squared; unpenalized intercept; equal source-author mass and source-only scaling; all other three authors. Raw frequency/degree controls. Tied top3/5; no winner selection. Full valid lexical contexts. Features before teacher load; all predictions/selections before evaluation. Labels are205 combined adjusted detections, not grammatical correctness. No reserves or new annotation.'))
    graphs=load(ROOT/'iteration193/graphs.json');bundles=load(ROOT/'iteration205/candidates.json')
    ff={a:features(graphs[a],bundles[a]) for a in AUTHORS};save(OUT/'features.json',ff);save(OUT/'feature-freeze.json',{'features.json':digest(OUT/'features.json')})
    dd=load(ROOT/'iteration205/details.json');yy={a:[int(r['adjusted_detected']) for r in dd[a]['edge_or_pivot']] for a in AUTHORS}
    for a in AUTHORS:assert [r['word'] for r in ff[a]]==[r['word'] for r in dd[a]['edge_or_pivot']]
    models={};pred={};sel={}
    for a in AUTHORS:
        sources=[b for b in AUTHORS if b!=a];rows=[r['values'] for b in sources for r in ff[b]];y=[v for b in sources for v in yy[b]];weights=[1/len(ff[b]) for b in sources for r in ff[b]]
        models[a]={name:weighted_fit(rows,y,weights,cols) for name,cols in [('full12',list(range(12))),('count4',list(range(4)))]}
        pred[a]={name:predict(ff[a],m) for name,m in models[a].items()}
        pred[a].update(frequency=[r['values'][0] for r in ff[a]],degree=[r['values'][1] for r in ff[a]])
        sel[a]={name:{'top'+str(k):top(s,k) for k in [3,5]} for name,s in pred[a].items()}
    save(OUT/'models.json',models);save(OUT/'predictions.json',pred);save(OUT/'selections.json',sel);save(OUT/'prediction-freeze.json',{n:digest(OUT/n) for n in ['models.json','predictions.json','selections.json']})
    summary={a:dict(candidates=len(yy[a]),teacher_positives=sum(yy[a]),models={name:dict(lists={k:metrics(yy[a],s,ix) for k,ix in sel[a][name].items()},classification=evaluate(yy[a],s) if name in models[a] else None) for name,s in pred[a].items()}) for a in AUTHORS}
    save(OUT/'teacher-labels.json',yy);save(OUT/'summary.json',summary)
    for a in AUTHORS:
        print(a,summary[a]['teacher_positives'],{m:{k:(v['supported'],v['selected']) for k,v in r['lists'].items()} for m,r in summary[a]['models'].items()})
if __name__=='__main__':run()
