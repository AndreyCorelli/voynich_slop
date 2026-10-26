"""Independent multioutput augmented LS, profile normalization and metrics."""
from pathlib import Path
from collections import Counter,defaultdict
from fractions import Fraction as F
import json,math,hashlib
import numpy as np
from benchmarks.grammar_case_applicability_iteration180_review import close
from benchmarks.grammar_case_subfamilies_iteration172 import TAGS
P=Path('experiments/results/grammar-restoration');O=P/'iteration231';AA=['Aquinas','Caesar','Cicero','Jerome']
def read(p):return json.loads(p.read_text())
def run():
    ff=read(O/'features.json');mm=read(O/'models.json');pred=read(O/'predictions.json');sel=read(O/'selections.json');truth=read(O/'truth.json');ss=read(O/'summary.json');changes=read(O/'node-changes.json');gg=read(P/'iteration193/graphs.json');gg['Dante']=read(P/'iteration198/graphs.json')['primary'];ref=read(P/'iteration201/development-references.json');ref['Dante']={'pos':read(P/'iteration200/pos-references.json')['pos_by_stream_position']};profiles={};freq={};fits=0
    oldff=read(P/'iteration221/features.json');assert all(ff[a]==oldff[a] for a in AA)
    for a,rows in ff.items():
        counts=defaultdict(Counter);freq[a]=Counter()
        for i,p in enumerate(gg[a]['positions']):
            if p is not None:counts[gg[a]['ids'][i]][ref[a]['pos'][i]]+=1;freq[a][gg[a]['ids'][i]]+=1
        profiles[a]=[[float(F(counts[r['word']][t],sum(counts[r['word']].values()))) for t in TAGS] for r in rows];close(profiles[a],truth[a]['profiles']);assert truth[a]['frequencies']==[freq[a][r['word']] for r in rows]
    # Independent anonymous projection for the newly added Dante endpoints.
    g=gg['Dante'];globalcount=Counter(g['ids']);adj=defaultdict(set);contexts=defaultdict(list)
    for e in g['descriptors']:adj[e['a']].add(e['b']);adj[e['b']].add(e['a'])
    for i in range(1,len(g['ids'])-1):
        if all(g['positions'][j] is not None for j in [i-1,i,i+1]):contexts[g['ids'][i]].append((g['ids'][i-1],g['ids'][i+1]))
    for row in ff['Dante']:
        word=row['word'];frames=set();pivots=set();uses=0
        for e in g['descriptors']:
            if word not in [e['a'],e['b']]:continue
            side='a' if e['a']==word else 'b'
            for f in e['frames']:frames.add(tuple(f['frame']));pivots.update(f[side+'_positions']);uses+=len(f[side+'_positions'])
        cc=contexts[word];n=len(cc)
        def entropy(items):return sum(-v/n*math.log(v/n) for v in Counter(items).values())/math.log(n) if n>1 else 0.
        values=[math.log(globalcount[word]),math.log1p(len(adj[word])),math.log1p(len(frames)),math.log1p(len(pivots)),uses/len(pivots),len(pivots)/globalcount[word],sum(math.log(globalcount[v]) for v in adj[word])/len(adj[word]),sum(math.log1p(len(adj[v])) for v in adj[word])/len(adj[word]),entropy([l for l,r in cc]),entropy([r for l,r in cc]),entropy(cc),len(set(cc))/n if n else 0.]
        close(values,row['values'])
    for target in ff:
        src=[a for a in AA if a!=target];raw=np.array([r['values'] for a in src for r in ff[a]]);y=np.array([r for a in src for r in profiles[a]]);w=np.array([1/(len(src)*len(ff[a])) for a in src for r in ff[a]]);mu=w@raw;sd=np.sqrt(w@((raw-mu)**2));sd[sd<1e-12]=1;m=mm[target];close(mu.tolist(),m['mean']);close(sd.tolist(),m['scale']);x=np.column_stack([np.ones(len(raw)),(raw-mu)/sd]);aug=np.vstack([np.sqrt(w)[:,None]*x,np.diag([0]+[math.sqrt(.1)]*12)]);b=np.linalg.lstsq(aug,np.vstack([np.sqrt(w)[:,None]*y,np.zeros((13,len(TAGS)))]),rcond=None)[0];close(b.tolist(),m['beta']);tx=np.array([r['values'] for r in ff[target]]);rawpred=np.column_stack([np.ones(len(tx)),(tx-mu)/sd])@np.array(m['beta']);normal=np.clip(rawpred,0,None);normal/=normal.sum(axis=1)[:,None];close(normal.tolist(),pred[target]['node']);prior=(w@y).tolist();close([prior]*len(tx),pred[target]['prior']);fits+=1
        index={r['word']:i for i,r in enumerate(ff[target])}
        for name,ix in sel[target].items():
            expected=normal.copy();used=set()
            for ei in ix:
                e=gg[target]['descriptors'][ei];u=index[e['a']];v=index[e['b']];assert u not in used and v not in used;used|={u,v};expected[u]=expected[v]=(normal[u]+normal[v])/2
            close(expected.tolist(),pred[target][name]);after=pred[target][name];expectedchanges=[dict(index=i,word=ff[target][i]['word'],before=TAGS[int(np.argmax(normal[i]))],after=TAGS[int(np.argmax(after[i]))]) for i in sorted(used) if np.argmax(normal[i])!=np.argmax(after[i])];assert changes[target][name]==expectedchanges
        coverage=ss[target]['coverage'];n=len(ff[target]);tokens=sum(truth[target]['frequencies']);assert coverage['graph_nodes']==n and coverage['text_word_types']==len(freq[target]) and coverage['covered_tokens']==tokens and coverage['text_tokens']==sum(freq[target].values());close(coverage['word_type_fraction'],n/len(freq[target]));close(coverage['token_fraction'],tokens/sum(freq[target].values()))
        def metrics(p,ix):
            chosen=[max(range(len(TAGS)),key=lambda j:p[i][j]) for i in ix];mass=[profiles[target][i][t] for i,t in zip(ix,chosen)];f=truth[target]['frequencies'];return dict(nodes=len(ix),type_macro_top1_mass=sum(mass)/len(ix),covered_token_top1_accuracy=sum(f[i]*v for i,v in zip(ix,mass))/sum(f[i] for i in ix),tokens=sum(f[i] for i in ix),mean_squared_profile_error=sum(sum((p[i][j]-profiles[target][i][j])**2 for j in range(len(TAGS))) for i in ix)/len(ix),predicted_tag_counts=dict(Counter(TAGS[t] for t in chosen)))
        for name,p in pred[target].items():close(metrics(p,list(range(n))),ss[target]['methods'][name])
        for name,ix in sel[target].items():
            selected=sorted({index[gg[target]['descriptors'][ei][k]] for ei in ix for k in ['a','b']});close(metrics(pred[target]['node'],selected),ss[target]['selected'][name]['before']);close(metrics(pred[target][name],selected),ss[target]['selected'][name]['after'])
    hashes=0
    for manifest in [read(O/'design-freeze.json')['inputs'],read(P/'iteration230/verification-manifest.json')]:
        for p,h in manifest.items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h;hashes+=1
    for fn in ['feature-freeze.json','prediction-freeze.json']:
        for p,h in read(O/fn).items():assert hashlib.sha256((O/p).read_bytes()).hexdigest()==h;hashes+=1
    result=dict(status='passed',rational_node_profiles=sum(map(len,profiles.values())),multioutput_ls_refits=fits,metric_groups=40,hashes=hashes);(O/'independent-review.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
if __name__=='__main__':run()
