"""Frozen size-matched and prior-only controls for source reweighting."""
from pathlib import Path
import json,hashlib,math
from benchmarks.grammar_bundle_hard_gate_iteration212 import top
P=Path('experiments/results/grammar-restoration');O=P/'iteration217'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def logit(p):return math.log(p/(1-p))
def run():
    assert not O.exists();O.mkdir();(O/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),Path('benchmarks/grammar_bundle_hard_gate_iteration212.py')]+[P/n for n in ['iteration216/predictions.json','iteration216/weights.json','iteration216/summary.json','iteration216/verification-manifest.json','iteration211/applicability-labels.json','iteration207/predictions.json','iteration207/teacher-labels.json']]
    save(O/'design-freeze.json',{str(p):sha(p) for p in paths})
    for p,h in read(P/'iteration216/verification-manifest.json').items():assert sha(Path(p))==h
    pred=read(P/'iteration216/predictions.json');weights=read(P/'iteration216/weights.json');app=read(P/'iteration211/applicability-labels.json');support=read(P/'iteration207/predictions.json');selections={};priors={}
    for target,variants in pred.items():
        src=[a for a in pred if a!=target];qold=sum(sum(app[a])/len(app[a]) for a in src)/3;qnew=sum(sum(w*y for w,y in zip(weights[target][a]['weights'],app[a])) for a in src);shift=logit(qnew)-logit(qold);p=variants['baseline'][target];adjusted=[1/(1+math.exp(-(logit(v)+shift))) for v in p];balanced=[i for i,v in enumerate(variants['balanced'][target]) if v>=.5];k=len(balanced);eligible=dict(baseline=[i for i,v in enumerate(p) if v>=.5],balanced=balanced,size_matched=top(p,list(range(len(p))),k) if k else [],prior_only=[i for i,v in enumerate(adjusted) if v>=.5]);priors[target]=dict(original=qold,balanced=qnew,logit_shift=shift,adjusted_probabilities=adjusted,matched_k=k);selections[target]={name:dict(eligible=ix,lists={f'top{n}':top(support[target]['full12'],ix,n) for n in [3,5]}) for name,ix in eligible.items()}
    save(O/'priors.json',priors);save(O/'selections.json',selections);save(O/'selection-freeze.json',{n:sha(O/n) for n in ['priors.json','selections.json']})
    yy=read(P/'iteration207/teacher-labels.json');old=read(P/'iteration216/summary.json');summary={}
    for a,methods in selections.items():
        summary[a]={};positive=[i for i,v in enumerate(yy[a]) if v]
        for name,d in methods.items():
            ix=d['eligible'];tp=sum(app[a][i] for i in ix);kept=[i for i in positive if i in ix];lists={}
            for label,jj in d['lists'].items():
                hit=sum(yy[a][i] for i in jj);lists[label]=dict(selected=len(jj),supported=hit,precision=hit/len(jj) if jj else None,recall=hit/len(positive) if positive else None,case_bearing=sum(app[a][i] for i in jj))
            summary[a][name]=dict(eligible=len(ix),matched_k=priors[a]['matched_k'],size_excess=len(ix)-priors[a]['matched_k'] if name=='size_matched' else None,case_tp=tp,case_fp=len(ix)-tp,retained_supported=kept,rejected_supported=[i for i in positive if i not in ix],lists=lists)
            if name in ['baseline','balanced']:
                assert len(ix)==old[a][name]['eligible'] and kept==old[a][name]['retained_supported']
                for label,v in lists.items():assert v['selected']==old[a][name]['lists']['hard'][label]['support']['selected'] and v['supported']==old[a][name]['lists']['hard'][label]['support']['supported']
    save(O/'summary.json',summary)
    for a,v in summary.items():print(a,{n:dict(admitted=d['eligible'],retained=len(d['retained_supported']),case_fp=d['case_fp'],top5=d['lists']['top5']['supported']) for n,d in v.items()})
if __name__=='__main__':run()
