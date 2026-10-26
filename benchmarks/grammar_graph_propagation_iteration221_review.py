"""Independent feature, scalar score and synchronous propagation replay."""
from pathlib import Path
from collections import Counter,defaultdict
import json,math,hashlib
from benchmarks.grammar_case_applicability_iteration180_review import close,independent_evaluate
P=Path('experiments/results/grammar-restoration');F=P/'iteration221';O=P/'iteration221-finalization'
def read(p):return json.loads(p.read_text())
def run():
    ff=read(F/'features.json');gg=read(P/'iteration193/graphs.json');bb=read(P/'iteration204/bundles.json');pp=read(F/'predictions.json');indices=read(F/'center-projection.json');labels=read(P/'iteration220/labels.json');yy=read(P/'iteration207/teacher-labels.json');support=read(P/'iteration207/predictions.json');sel=read(F/'selections.json');ss=read(O/'summary.json');base=read(P/'iteration211/models.json');balanced=read(P/'iteration216/models.json');rowschecked=0;lists=0
    for a,rows in ff.items():
        g=gg[a];counts=Counter(g['ids']);adj=defaultdict(set);contexts=defaultdict(list)
        for e in g['descriptors']:adj[e['a']].add(e['b']);adj[e['b']].add(e['a'])
        for i in range(1,len(g['ids'])-1):
            if all(g['positions'][j] is not None for j in [i-1,i,i+1]):contexts[g['ids'][i]].append((g['ids'][i-1],g['ids'][i+1]))
        lookup={r['word']:i for i,r in enumerate(rows)}
        for row,b in zip(rows,bb[a]):
            w=row['word'];frames=set();pivots=set();uses=0
            for ei in b['edges']:
                e=g['descriptors'][ei];side='a' if e['a']==w else 'b'
                for f in e['frames']:frames.add(tuple(f['frame']));pivots.update(f[side+'_positions']);uses+=len(f[side+'_positions'])
            c=contexts[w];n=len(c)
            def entropy(items):return sum(-v/n*math.log(v/n) for v in Counter(items).values())/math.log(n) if n>1 else 0.
            values=[math.log(counts[w]),math.log1p(len(adj[w])),math.log1p(len(frames)),math.log1p(len(pivots)),uses/len(pivots),len(pivots)/counts[w],sum(math.log(counts[v]) for v in adj[w])/len(adj[w]),sum(math.log1p(len(adj[v])) for v in adj[w])/len(adj[w]),entropy([l for l,r in c]),entropy([r for l,r in c]),entropy(c),len(set(c))/n if n else 0.];close(values,row['values']);rowschecked+=1
        assert [rows[i] for i in indices[a]]==read(P/'iteration207/features.json')[a]
        y=[labels[a][r['word']] for r in rows];cy=[y[i] for i in indices[a]]
        for variant,m in [('baseline',base[a]['full12']),('balanced',balanced[a]['balanced'])]:
            original=[]
            for row in rows:
                z=m['beta'][0]+sum((v-m['mean'][j])/m['scale'][j]*m['beta'][j+1] for j,v in enumerate(row['values']));original.append(1/(1+math.exp(-z)))
            close(original,pp[a][variant]['original']);refined=[(pp[a][variant]['original'][i]+sum(pp[a][variant]['original'][lookup[v]] for v in adj[r['word']])/len(adj[r['word']]))/2 for i,r in enumerate(rows)];close(refined,pp[a][variant]['refined'])
            for stage,values in pp[a][variant].items():
                v=ss[a][variant][stage];cp=[values[i] for i in indices[a]];close(independent_evaluate(y,values),v['all_nodes']);close(independent_evaluate(cy,cp),v['centers']);keep=[i for i,z in enumerate(cp) if z>=.5];assert keep==sel[a][variant][stage]['eligible'] and v['eligible']==len(keep);positive=[i for i,z in enumerate(yy[a]) if z];assert v['retained_supported']==[i for i in positive if i in keep]
                for mode,scores,universe in [('hard',support[a]['full12'],keep),('product',[p*q for p,q in zip(cp,support[a]['full12'])],list(range(len(cp))))]:
                    neg=[i for i,z in enumerate(yy[a]) if not z];auc=sum((scores[i]>scores[j])+.5*(scores[i]==scores[j]) for i in positive for j in neg)/(len(positive)*len(neg)) if positive and neg else None
                    for k in [3,5]:
                        label=f'top{k}';cut=sorted([scores[i] for i in universe],reverse=True)[min(k,len(universe))-1] if universe else None;ix=[i for i in universe if scores[i]>=cut] if universe else [];assert ix==sel[a][variant][stage][mode][label];hit=sum(yy[a][i] for i in ix);close(v['lists'][mode][label]['support'],dict(selected=len(ix),supported=hit,precision=hit/len(ix) if ix else None,recall=hit/len(positive) if positive else None,coverage=len(ix)/len(cp),auc=auc));assert v['lists'][mode][label]['case_bearing']==sum(cy[i] for i in ix);lists+=1
    hashes=0
    for manifest in [read(F/'design-freeze.json'),read(O/'design-freeze.json'),read(P/'iteration220/verification-manifest.json')]:
        for p,h in manifest.items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h;hashes+=1
    for fn in ['feature-freeze.json','prediction-freeze.json']:
        for p,h in read(F/fn).items():assert hashlib.sha256((F/p).read_bytes()).hexdigest()==h;hashes+=1
    result=dict(status='passed',feature_rows=rowschecked,prediction_transition_groups=16,lists=lists,hashes=hashes);(O/'independent-review.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
if __name__=='__main__':run()
