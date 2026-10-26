"""Reference POS and fixed-model logit audit, not POS inference."""
from pathlib import Path
from collections import Counter,defaultdict
import json,hashlib
import numpy as np
P=Path('experiments/results/grammar-restoration');O=P/'iteration213'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def summarize(rows,ix,prob):
    result=dict(n=len(ix),probability_range=[min(prob[i] for i in ix),max(prob[i] for i in ix)] if ix else None)
    for view in ['global','queried']:
        pooled=Counter();macro=Counter()
        for i in ix:
            counts=rows[i][view];pooled.update(counts);n=sum(counts.values())
            for tag,v in counts.items():macro[tag]+=v/n/len(ix)
        total=sum(pooled.values());result[view]=dict(occurrences=total,counts=dict(sorted(pooled.items())),pooled_fractions={t:v/total for t,v in sorted(pooled.items())} if total else {},center_macro_fractions=dict(sorted(macro.items())))
    return result

def run():
    assert not O.exists();O.mkdir();(O/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__)]+[P/n for n in ['iteration193/graphs.json','iteration201/development-references.json','iteration205/candidates.json','iteration207/teacher-labels.json','iteration211/features.json','iteration211/models.json','iteration211/predictions.json','iteration211/applicability-labels.json','iteration212/selections.json','iteration212/verification-manifest.json']]
    save(O/'design-freeze.json',{str(p):sha(p) for p in paths})
    for p,h in read(P/'iteration212/verification-manifest.json').items():assert sha(Path(p))==h
    y=read(P/'iteration207/teacher-labels.json');app=read(P/'iteration211/applicability-labels.json');pred=read(P/'iteration211/predictions.json');sel=read(P/'iteration212/selections.json');groups={}
    for a in pred:
        groups[a]={}
        for name in pred[a]:
            keep=set(sel[a][name]['eligible']);groups[a][name]=dict(all=list(range(len(y[a]))),case_bearing=[i for i,v in enumerate(app[a]) if v],accepted_case_bearing=[i for i,v in enumerate(app[a]) if v and i in keep],rejected_case_bearing=[i for i,v in enumerate(app[a]) if v and i not in keep],supported_retained=[i for i,v in enumerate(y[a]) if v and i in keep],supported_rejected=[i for i,v in enumerate(y[a]) if v and i not in keep],admitted_unsupported_head=[i for i in sel[a][name]['lists']['top5'] if not y[a][i]])
    save(O/'groups.json',groups);save(O/'group-freeze.json',{'groups.json':sha(O/'groups.json')})
    gg=read(P/'iteration193/graphs.json');refs=read(P/'iteration201/development-references.json');bb=read(P/'iteration205/candidates.json');ff=read(P/'iteration211/features.json');models=read(P/'iteration211/models.json');details={};summary={};contrasts={}
    for a in groups:
        g=gg[a];ref=refs[a];globalpos=defaultdict(Counter)
        for i,p in enumerate(g['positions']):
            if p:globalpos[g['ids'][i]][ref['pos'][i]]+=1
        rows=[]
        for j,b in enumerate(bb[a]):
            pivots=set()
            for ei in b['edges']:
                e=g['descriptors'][ei];side='a' if e['a']==b['word'] else 'b'
                for frame in e['frames']:pivots.update(frame[side+'_positions'])
            rows.append(dict(index=j,word=b['word'],global_positions_count=sum(globalpos[b['word']].values()),queried_positions=sorted(pivots),global_=dict(globalpos[b['word']]),queried=dict(Counter(ref['pos'][i] for i in pivots))))
            rows[-1]['global']=rows[-1].pop('global_')
        details[a]=rows;summary[a]={};contrasts[a]={}
        for name,group in groups[a].items():
            prob=pred[a][name]['applicability'];summary[a][name]={k:summarize(rows,ix,prob) for k,ix in group.items()};rejected=group['supported_rejected'];accepted=group['accepted_case_bearing'];m=models[a][name]
            if rejected and accepted:
                raw=np.array([r['values'] for r in ff[a]])[:,m['columns']];z=(raw-np.array(m['mean']))/np.array(m['scale']);delta=z[rejected].mean(0)-z[accepted].mean(0);contrib=delta*np.array(m['beta'][1:]);contrasts[a][name]=dict(rejected_supported_minus_accepted_case_bearing_standardized_feature=delta.tolist(),logit_contributions=contrib.tolist(),mean_logit_gap=float(contrib.sum()))
            else:contrasts[a][name]=None
    save(O/'details.json',details);save(O/'summary.json',summary);save(O/'contrasts.json',contrasts)
    for a,v in summary.items():
        for name,groups in v.items():print(a,name,{k:dict(n=groups[k]['n'],pos=groups[k]['global']['center_macro_fractions']) for k in ['accepted_case_bearing','supported_rejected','supported_retained']})
if __name__=='__main__':run()
