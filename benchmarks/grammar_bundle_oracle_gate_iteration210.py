"""Oracle Case-bearing gate on unchanged anonymous rankings."""
from pathlib import Path
import json,hashlib
P=Path('experiments/results/grammar-restoration');O=P/'iteration210'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def ranks(scores,positive,eligible):
    return [dict(index=i,first=1+sum(scores[j]>scores[i] for j in eligible),last=sum(scores[j]>=scores[i] for j in eligible)) for i in positive if i in eligible]
def measure(ix,y,n,eligible):
    hits=sum(y[i] for i in ix)
    return dict(selected=len(ix),supported=hits,precision=hits/len(ix) if ix else None,recall=hits/sum(y) if sum(y) else None,original_coverage=len(ix)/n,eligible_coverage=len(ix)/len(eligible) if eligible else None)
def top(scores,eligible,k):
    if not eligible:return []
    cutoff=sorted([scores[i] for i in eligible],reverse=True)[min(k,len(eligible))-1]
    return [i for i in eligible if scores[i]>=cutoff]
def run():
    assert not O.exists();O.mkdir();(O/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__)]+[P/f'iteration207/{n}.json' for n in ['predictions','teacher-labels','selections','summary','verification-manifest']]+[P/f'iteration209/{n}.json' for n in ['details','verification-manifest']]
    save(O/'design-freeze.json',{str(p):sha(p) for p in paths})
    for it in ['iteration207','iteration209']:
        for p,h in read(P/it/'verification-manifest.json').items():assert sha(Path(p))==h
    pred=read(P/'iteration207/predictions.json');y=read(P/'iteration207/teacher-labels.json');refs=read(P/'iteration209/details.json');baseline=read(P/'iteration207/selections.json');summary={};details={}
    for a,models in pred.items():
        eligible=[r['index'] for r in refs[a] if r['center_global_case_fraction']>0];positive=[i for i,v in enumerate(y[a]) if v];allix=list(range(len(y[a])));assert set(positive)<=set(eligible)
        details[a]=dict(eligible=eligible,rejected=[dict(index=r['index'],word=r['word']) for r in refs[a] if r['index'] not in eligible],models={});summary[a]=dict(original_candidates=len(allix),eligible=len(eligible),rejected=len(allix)-len(eligible),original_supported=len(positive),retained_supported=len(set(positive)&set(eligible)),models={})
        for name,s in models.items():
            lists={};result={}
            for kind,universe in [('original',allix),('gated',eligible)]:
                lists[kind]={f'top{k}':top(s,universe,k) for k in [3,5]};result[kind]={label:measure(ix,y[a],len(allix),universe) for label,ix in lists[kind].items()}
            assert lists['original']==baseline[a][name]
            details[a]['models'][name]=dict(lists=lists,original_ranks=ranks(s,positive,allix),gated_ranks=ranks(s,positive,eligible));summary[a]['models'][name]=result
    save(O/'details.json',details);save(O/'summary.json',summary)
    for a,v in summary.items():print(a,v['eligible'],{n:{mode:{k:f"{z['supported']}/{z['selected']}" for k,z in m.items()} for mode,m in r.items()} for n,r in v['models'].items()})
if __name__=='__main__':run()
