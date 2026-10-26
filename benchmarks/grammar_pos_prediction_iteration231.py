"""Direct source-trained POS profiles, with fixed anonymous pair refinement."""
from pathlib import Path
from collections import Counter
import json,hashlib
import numpy as np
from benchmarks.grammar_bundle_selector_iteration207 import features
from benchmarks.grammar_ego_bundle_iteration204 import bundle_structure
from benchmarks.grammar_case_subfamilies_iteration172 import TAGS
P=Path('experiments/results/grammar-restoration');O=P/'iteration231';AA=['Aquinas','Caesar','Cicero','Jerome']
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def fit(raw,y,w):
    xx=np.array(raw);w=np.array(w);w/=w.sum();mu=w@xx;sd=np.sqrt(w@((xx-mu)**2));sd[sd<1e-12]=1;x=np.column_stack([np.ones(len(xx)),(xx-mu)/sd]);pen=np.diag([0]+[.1]*len(mu));beta=np.linalg.solve(x.T@(w[:,None]*x)+pen,x.T@(w[:,None]*np.array(y)));return dict(mean=mu.tolist(),scale=sd.tolist(),beta=beta.tolist())
def predict(rows,m):
    xx=np.array([r['values'] for r in rows]);raw=np.column_stack([np.ones(len(xx)),(xx-m['mean'])/m['scale']])@np.array(m['beta']);clipped=np.maximum(raw,0);assert np.all(clipped.sum(axis=1)>0);return (clipped/clipped.sum(axis=1)[:,None]).tolist()
def evaluate(y,p,counts,indices):
    yy=np.array(y)[indices];pp=np.array(p)[indices];cc=np.array(counts)[indices];top=np.argmax(pp,axis=1);mass=yy[np.arange(len(indices)),top];return dict(nodes=len(indices),type_macro_top1_mass=float(mass.mean()),covered_token_top1_accuracy=float(cc@mass/cc.sum()),tokens=int(cc.sum()),mean_squared_profile_error=float(np.mean(np.sum((pp-yy)**2,axis=1))),predicted_tag_counts=dict(Counter(TAGS[t] for t in top)))
def run():
    assert not O.exists();O.mkdir();(O/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__)]+[Path('benchmarks')/n for n in ['grammar_bundle_selector_iteration207.py','grammar_ego_bundle_iteration204.py','grammar_case_subfamilies_iteration172.py']]+[P/n for n in ['iteration193/graphs.json','iteration198/graphs.json','iteration221/features.json','iteration223/profiles.json','iteration227/selections.json','iteration226/disjoint-selections.json','iteration229/selections.json','iteration200/pos-references.json','iteration230/verification-manifest.json']];save(O/'design-freeze.json',dict(inputs={str(p):sha(p) for p in paths},tags=TAGS,status='four development LOAO plus consumed Dante; graph endpoints only'))
    for p,h in read(P/'iteration230/verification-manifest.json').items():assert sha(Path(p))==h
    graphs=read(P/'iteration193/graphs.json');graphs['Dante']=read(P/'iteration198/graphs.json')['primary'];ff=read(P/'iteration221/features.json');ff['Dante']=features(graphs['Dante'],bundle_structure(graphs['Dante']['descriptors']));save(O/'features.json',ff);save(O/'feature-freeze.json',{'features.json':sha(O/'features.json')})
    profiles=read(P/'iteration223/profiles.json');rawsel=read(P/'iteration227/selections.json');richsel=read(P/'iteration226/disjoint-selections.json');dantesel=read(P/'iteration229/selections.json');models={};pred={};selections={}
    for target in AA+['Dante']:
        src=[a for a in AA if a!=target];raw=[r['values'] for a in src for r in ff[a]];y=[[profiles[a][r['word']].get(t,0) for t in TAGS] for a in src for r in ff[a]];w=[1/len(ff[a]) for a in src for r in ff[a]];models[target]=fit(raw,y,w);prior=np.average(np.array(y),axis=0,weights=w).tolist();base=predict(ff[target],models[target]);pred[target]=dict(prior=[prior]*len(ff[target]),node=base);selections[target]={};lookup={r['word']:i for i,r in enumerate(ff[target])}
        for name in ['support','rich19']:
            ix=dantesel[name]['disjoint']['top10'] if target=='Dante' else (rawsel[target]['support']['disjoint']['top10'] if name=='support' else richsel[target]['rich19']['top10']);selections[target][name]=ix;refined=np.array(base).copy()
            for ei in ix:
                e=graphs[target]['descriptors'][ei];u=lookup[e['a']];v=lookup[e['b']];refined[u]=refined[v]=(np.array(base[u])+np.array(base[v]))/2
            pred[target][name]=refined.tolist()
    for n,v in [('models',models),('predictions',pred),('selections',selections)]:save(O/(n+'.json'),v)
    save(O/'prediction-freeze.json',{n:sha(O/n) for n in ['models.json','predictions.json','selections.json']})
    tags=read(P/'iteration200/pos-references.json')['pos_by_stream_position'];g=graphs['Dante'];counts={}
    for i,p in enumerate(g['positions']):
        if p is not None:counts.setdefault(g['ids'][i],Counter())[tags[i]]+=1
    profiles['Dante']={w:{t:n/sum(c.values()) for t,n in c.items()} for w,c in counts.items()};summary={};truth={};nodechanges={}
    for a in AA+['Dante']:
        g=graphs[a];freq=Counter(g['ids'][i] for i,p in enumerate(g['positions']) if p is not None);y=[[profiles[a][r['word']].get(t,0) for t in TAGS] for r in ff[a]];counts=[freq[r['word']] for r in ff[a]];truth[a]=dict(profiles=y,frequencies=counts);summary[a]=dict(coverage=dict(graph_nodes=len(ff[a]),text_word_types=len(freq),word_type_fraction=len(ff[a])/len(freq),covered_tokens=sum(counts),text_tokens=sum(freq.values()),token_fraction=sum(counts)/sum(freq.values())),methods={name:evaluate(y,p,counts,list(range(len(y)))) for name,p in pred[a].items()},selected={});nodechanges[a]={};lookup={r['word']:i for i,r in enumerate(ff[a])}
        for name,ix in selections[a].items():
            selected=sorted({lookup[g['descriptors'][i][k]] for i in ix for k in ['a','b']});summary[a]['selected'][name]=dict(before=evaluate(y,pred[a]['node'],counts,selected),after=evaluate(y,pred[a][name],counts,selected));nodechanges[a][name]=[dict(index=i,word=ff[a][i]['word'],before=TAGS[int(np.argmax(pred[a]['node'][i]))],after=TAGS[int(np.argmax(pred[a][name][i]))]) for i in selected if np.argmax(pred[a]['node'][i])!=np.argmax(pred[a][name][i])]
    for n,v in [('truth',truth),('node-changes',nodechanges),('summary',summary)]:save(O/(n+'.json'),v)
    for a,v in summary.items():print(a,'coverage',round(v['coverage']['token_fraction'],4),{n:round(d['type_macro_top1_mass'],4) for n,d in v['methods'].items()},'selected',{n:(round(d['before']['type_macro_top1_mass'],4),round(d['after']['type_macro_top1_mass'],4)) for n,d in v['selected'].items()})
if __name__=='__main__':run()
