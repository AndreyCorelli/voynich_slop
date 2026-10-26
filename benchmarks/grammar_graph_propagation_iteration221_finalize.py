"""Finalize frozen221 outputs after exact floating equality stop; no new predictions."""
from benchmarks.grammar_graph_propagation_iteration221 import read,sha,save,P,evaluate,metrics
from pathlib import Path
O=P/'iteration221-finalization';F=P/'iteration221'
def run():
    assert not O.exists();O.mkdir();paths=[Path(__file__),Path('benchmarks/grammar_graph_propagation_iteration221.py')]+sorted(F.glob('*.json'));save(O/'design-freeze.json',{str(p):sha(p) for p in paths})
    ff=read(F/'features.json');projection=read(F/'center-projection.json');pred=read(F/'predictions.json');sel=read(F/'selections.json');labels=read(P/'iteration220/labels.json');yy=read(P/'iteration207/teacher-labels.json');support=read(P/'iteration207/predictions.json');oldbase=read(P/'iteration211/predictions.json');oldbalanced=read(P/'iteration216/predictions.json');oldmetrics=read(P/'iteration216/summary.json');summary={};maxdiff=0.
    for a,variants in pred.items():
        y=[labels[a][r['word']] for r in ff[a]];cy=[y[i] for i in projection[a]];summary[a]={}
        for variant,stages in variants.items():
            summary[a][variant]={}
            for stage,p in stages.items():
                cp=[p[i] for i in projection[a]];s=sel[a][variant][stage];positive=[i for i,v in enumerate(yy[a]) if v];product=[x*y for x,y in zip(cp,support[a]['full12'])];summary[a][variant][stage]=dict(all_nodes=evaluate(y,p),centers=evaluate(cy,cp),eligible=len(s['eligible']),retained_supported=[i for i in positive if i in s['eligible']],lists={mode:{label:dict(support=metrics(yy[a],support[a]['full12'] if mode=='hard' else product,ix),case_bearing=sum(cy[i] for i in ix)) for label,ix in s[mode].items()} for mode in ['hard','product']})
                if stage=='original':
                    old=oldbase[a]['full12']['applicability'] if variant=='baseline' else oldbalanced[a]['balanced'][a];diff=max(abs(x-y) for x,y in zip(cp,old));assert diff<1e-12;maxdiff=max(maxdiff,diff)
                    for mode in ['hard','product']:
                        for label,ix in s[mode].items():
                            prior=read(P/'iteration212/selections.json')[a]['full12']['lists'][label] if variant=='baseline' and mode=='hard' else (read(P/'iteration211/selections.json')[a]['full12'][mode][label] if variant=='baseline' else read(P/'iteration216/selections.json')[a]['balanced'][mode][label]);assert ix==prior
    save(O/'summary.json',summary);save(O/'finalization-audit.json',dict(reason='Original exact equality assertion stopped after frozen predictions; batched matrix arithmetic max seed difference only machine precision. All original selections exactly unchanged.',maximum_seed_difference=maxdiff))
    for a,v in summary.items():print(a,{variant:{stage:dict(auc=round(d['centers']['auc'],4),retained=len(d['retained_supported']),hard5=d['lists']['hard']['top5']['support']['supported'],product5=d['lists']['product']['top5']['support']['supported']) for stage,d in stages.items()} for variant,stages in v.items()})
if __name__=='__main__':run()
