"""Within-sentence word-order destruction with unchanged graph eligibility."""
from pathlib import Path
from collections import Counter,defaultdict
import json,hashlib,random
import numpy as np
from benchmarks.grammar_pos_text_robustness_iteration237 import rebuild,partition
from benchmarks.grammar_pos_spectral_iteration233 import score
P=Path('experiments/results/grammar-restoration');O=P/'iteration240';AA=['Aquinas','Caesar','Cicero','Jerome','Dante']
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def describe(v):return dict(minimum=min(v),mean=float(np.mean(v)),maximum=max(v)) if v else None
def run():
    assert not O.exists();O.mkdir();(O/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),Path('benchmarks/grammar_pos_text_robustness_iteration237.py'),Path('benchmarks/grammar_pos_spectral_iteration233.py')]+[P/n for n in ['iteration193/graphs.json','iteration198/graphs.json','iteration237/baselines.json','iteration231/features.json','iteration231/truth.json','iteration239/verification-manifest.json']];save(O/'design-freeze.json',dict(inputs={str(p):sha(p) for p in paths},seeds=list(range(24000,24199))))
    for p,h in read(P/'iteration239/verification-manifest.json').items():assert sha(Path(p))==h
    gg=read(P/'iteration193/graphs.json');gg['Dante']=read(P/'iteration198/graphs.json')['primary'];graphs={};parts={};audit={}
    for a in AA:
        g=gg[a];sentences=defaultdict(list)
        for i,p in enumerate(g['positions']):
            if p is not None:sentences[tuple(p[:2])].append(i)
        graphs[a]=[];parts[a]=[];audit[a]=[]
        for seed in range(24000,24199):
            rng=random.Random(seed);ids=g['ids'].copy();changed=0
            for sentence,ix in sorted(sentences.items()):
                values=[g['ids'][i] for i in ix];rng.shuffle(values);assert Counter(values)==Counter(g['ids'][i] for i in ix)
                for i,w in zip(ix,values):ids[i]=w;changed+=w!=g['ids'][i]
            edges=rebuild(dict(ids=ids,positions=g['positions']),set());graphs[a].append(dict(seed=seed,descriptors=edges));parts[a].append(dict(seed=seed,**partition(edges)));audit[a].append(dict(seed=seed,sentences=len(sentences),lexical_positions=sum(map(len,sentences.values())),changed_positions=changed))
    for n,v in [('graphs',graphs),('partitions',parts),('shuffle-audit',audit)]:save(O/(n+'.json'),v)
    save(O/'graph-freeze.json',{n:sha(O/n) for n in ['graphs.json','partitions.json','shuffle-audit.json']})
    ff=read(P/'iteration231/features.json');truth=read(P/'iteration231/truth.json');baseline=read(P/'iteration237/baselines.json');details={};summary={}
    for a in AA:
        lookup={r['word']:i for i,r in enumerate(ff[a])};originalfreq={r['word']:truth[a]['frequencies'][i] for i,r in enumerate(ff[a])};originalprofiles={r['word']:truth[a]['profiles'][i] for i,r in enumerate(ff[a])}
        # Null graphs can include words outside the original endpoint universe: get their profiles from cached streams.
        if a!='Dante':
            ref=read(P/'iteration201/development-references.json')[a]['pos']
        else:ref=read(P/'iteration200/pos-references.json')['pos_by_stream_position']
        tags=read(P/'iteration231/design-freeze.json')['tags'];counts=defaultdict(Counter);freq=Counter()
        for i,p in enumerate(gg[a]['positions']):
            if p is not None:counts[gg[a]['ids'][i]][ref[i]]+=1;freq[gg[a]['ids'][i]]+=1
        profiles={w:[c[t]/sum(c.values()) for t in tags] for w,c in counts.items()}
        def evaluate(part):
            if not part['clusterable']:return None
            y=[profiles[w] for w in part['words']];return {weighting:{k:v for k,v in score(part['labels'],y,weights).items() if k in ['one_to_one','purity','majority','profile_oracle']} for weighting,weights in [('type_macro',[1]*len(y)),('token_weighted',[freq[w] for w in part['words']])]}
        actual=evaluate(baseline[a]['partition']);records=[]
        for graph,part in zip(graphs[a],parts[a]):records.append(dict(seed=part['seed'],edges=len(graph['descriptors']),nodes=len(part['words']),clusterable=part['clusterable'],scores=evaluate(part)))
        details[a]=records;summary[a]=dict(original_edges=baseline[a]['edges'],original_nodes=len(baseline[a]['partition']['words']),original_scores=actual,null_edges=describe([r['edges'] for r in records]),null_nodes=describe([r['nodes'] for r in records]),clusterable_runs=sum(r['clusterable'] for r in records),zero_edge_runs=sum(r['edges']==0 for r in records),edge_count_upper_tail=(1+sum(r['edges']>=baseline[a]['edges'] for r in records))/200,conditional_scores={w:{metric:describe([r['scores'][w][metric] for r in records if r['clusterable']]) for metric in ['one_to_one','purity']} for w in ['type_macro','token_weighted']})
    save(O/'details.json',details);save(O/'summary.json',summary);print(json.dumps(summary,indent=2))
if __name__=='__main__':run()
