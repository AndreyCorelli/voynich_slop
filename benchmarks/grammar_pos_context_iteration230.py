"""Frozen selected-pair local POS agreement and within-word shuffle audit."""
from pathlib import Path
from collections import defaultdict
import json,hashlib,random
import numpy as np
P=Path('experiments/results/grammar-restoration');O=P/'iteration230';AA=['Aquinas','Caesar','Cicero','Jerome','Dante']
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def run():
    assert not O.exists();O.mkdir();(O/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    names=['iteration193/graphs.json','iteration198/graphs.json','iteration201/development-references.json','iteration200/pos-references.json','iteration223/details.json','iteration225/selections.json','iteration226/disjoint-selections.json','iteration227/selections.json','iteration229/selections.json','iteration229/labels.json','iteration229/verification-manifest.json'];paths=[Path(__file__)]+[P/n for n in names];save(O/'design-freeze.json',dict(inputs={str(p):sha(p) for p in paths},seeds=list(range(23000,23199))))
    for p,h in read(P/'iteration229/verification-manifest.json').items():assert sha(Path(p))==h
    gg=read(P/'iteration193/graphs.json');gg['Dante']=read(P/'iteration198/graphs.json')['primary'];learned=read(P/'iteration225/selections.json');disjoint=read(P/'iteration226/disjoint-selections.json');raw=read(P/'iteration227/selections.json');dante=read(P/'iteration229/selections.json');lists={}
    for a in AA:
        lists[a]={'all':list(range(len(gg[a]['descriptors'])))}
        methods=dante if a=='Dante' else {**raw[a],**{name:dict(tied=learned[a][name],disjoint=disjoint[a][name]) for name in learned[a]}}
        for name,modes in methods.items():
            for mode,sets in modes.items():
                for label,ix in sets.items():lists[a][name+'/'+mode+'/'+label]=ix
    save(O/'selections.json',lists);save(O/'selection-freeze.json',{'selections.json':sha(O/'selections.json')})
    refs=read(P/'iteration201/development-references.json');refs['Dante']={'pos':read(P/'iteration200/pos-references.json')['pos_by_stream_position']};globalvalues={a:d['edge_values'] for a,d in read(P/'iteration223/details.json').items()};globalvalues['Dante']=read(P/'iteration229/labels.json');edgevalues={};summary={}
    for a in AA:
        g=gg[a];tags=refs[a]['pos'];code={t:i for i,t in enumerate(sorted(set(tags)))};original=np.array([code[t] for t in tags]);buckets=defaultdict(list)
        for i,p in enumerate(g['positions']):
            if p is not None:buckets[g['ids'][i]].append(i)
        assignments=[original]
        for seed in range(23000,23199):
            rng=random.Random(seed);perm=original.copy()
            for w,pp in sorted(buckets.items()):
                vv=[int(original[i]) for i in pp];rng.shuffle(vv);perm[pp]=vv
            assignments.append(perm)
        matrix=np.stack(assignments);columns=[]
        for e in g['descriptors']:
            values=np.zeros(len(matrix))
            for f in e['frames']:
                p=[p for p in f['a_positions'] for q in f['b_positions']];q=f['b_positions']*len(f['a_positions']);values+=np.mean(matrix[:,p]==matrix[:,q],axis=1)/len(e['frames'])
            columns.append(values)
        values=np.column_stack(columns);expected=np.array(globalvalues[a]);edgevalues[a]=dict(observed=values[0].tolist(),expected=expected.tolist(),surplus=(values[0]-expected).tolist(),null=values[1:].tolist(),sampled_zero_variance=int(sum(np.ptp(values[1:],axis=0)<=1e-12)));summary[a]={}
        for name,ix in lists[a].items():
            observed=float(values[0,ix].mean());exp=float(expected[ix].mean());null=values[1:,ix].mean(axis=1);summary[a][name]=dict(edges=len(ix),observed=observed,expected=exp,surplus=observed-exp,null_mean=float(null.mean()),null_min=float(null.min()),null_max=float(null.max()),null_zero_range=bool(float(np.ptp(null))<=1e-12),upper_tail=(1+int(sum(null>=observed-1e-12)))/200)
    save(O/'edge-values.json',edgevalues);save(O/'summary.json',summary)
    for a,v in summary.items():print(a,{n:{k:round(z,4) if isinstance(z,float) else z for k,z in v[n].items()} for n in ['all','rich19/tied/top10','rich19/disjoint/top10','support/disjoint/top10']})
if __name__=='__main__':run()
