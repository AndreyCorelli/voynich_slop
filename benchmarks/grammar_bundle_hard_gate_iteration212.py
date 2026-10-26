"""Fixed .5 hard applicability gate; no fits or threshold search."""
from pathlib import Path
import json,hashlib
P=Path('experiments/results/grammar-restoration');O=P/'iteration212'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def top(scores,eligible,k):
    if not eligible:return []
    cut=sorted((scores[i] for i in eligible),reverse=True)[min(k,len(eligible))-1]
    return [i for i in eligible if scores[i]>=cut]
def run():
    assert not O.exists();O.mkdir();(O/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__)]+[P/f'iteration211/{n}.json' for n in ['predictions','applicability-labels','features','summary','verification-manifest']]+[P/f'iteration207/{n}.json' for n in ['teacher-labels','summary','verification-manifest']]+[P/f'iteration210/{n}.json' for n in ['summary','verification-manifest']]
    save(O/'design-freeze.json',{str(p):sha(p) for p in paths})
    for it in ['iteration207','iteration210','iteration211']:
        for p,h in read(P/it/'verification-manifest.json').items():assert sha(Path(p))==h
    pred=read(P/'iteration211/predictions.json');detail={}
    for a,models in pred.items():
        detail[a]={}
        for name,scores in models.items():
            eligible=[i for i,p in enumerate(scores['applicability']) if p>=.5];detail[a][name]=dict(eligible=eligible,lists={f'top{k}':top(scores['support'],eligible,k) for k in [3,5]})
    save(O/'selections.json',detail);save(O/'selection-freeze.json',{'selections.json':sha(O/'selections.json')})
    yy=read(P/'iteration207/teacher-labels.json');app=read(P/'iteration211/applicability-labels.json');ff=read(P/'iteration211/features.json');original=read(P/'iteration207/summary.json');soft=read(P/'iteration211/summary.json');oracle=read(P/'iteration210/summary.json');summary={};ranks={}
    for a,models in detail.items():
        summary[a]={};ranks[a]={};positive=[i for i,v in enumerate(yy[a]) if v]
        for name,d in models.items():
            eligible=d['eligible'];retained=[i for i in positive if i in eligible];rejected=[i for i in positive if i not in eligible];scores=pred[a][name]['support'];ranks[a][name]=[dict(index=i,word=ff[a][i]['word'],retained=i in eligible,rank_first=1+sum(scores[j]>scores[i] for j in eligible) if i in eligible else None,rank_last=sum(scores[j]>=scores[i] for j in eligible) if i in eligible else None) for i in positive];lists={}
            for label,ix in d['lists'].items():
                hit=sum(yy[a][i] for i in ix);lists[label]=dict(selected=len(ix),supported=hit,case_bearing=sum(app[a][i] for i in ix),precision=hit/len(ix) if ix else None,recall=hit/len(positive) if positive else None,coverage=len(ix)/len(yy[a]),eligible_coverage=len(ix)/len(eligible) if eligible else None,retained_support_recall=hit/len(retained) if retained else None)
            summary[a][name]=dict(candidates=len(yy[a]),eligible=len(eligible),eligible_case_bearing=sum(app[a][i] for i in eligible),supported=len(positive),retained_supported=retained,rejected_supported=rejected,lists=lists,comparators={label:dict(original=original[a]['models'][name]['lists'][label],product=soft[a]['models'][name]['lists']['product'][label]['support'],oracle=oracle[a]['models'][name]['gated'][label]) for label in ['top3','top5']})
    save(O/'supported-ranks.json',ranks);save(O/'summary.json',summary)
    for a,v in summary.items():print(a,{name:dict(eligible=r['eligible'],retained=len(r['retained_supported']),rejected=len(r['rejected_supported']),lists={k:(z['supported'],z['selected'],z['case_bearing']) for k,z in r['lists'].items()}) for name,r in v.items()})
if __name__=='__main__':run()
