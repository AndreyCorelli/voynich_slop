"""Frozen regularization comparison on all pre-existing matched-length windows."""
from benchmarks.grammar_regularization_iteration153 import *
OUT=ROOT/'iteration154'

def run():
    assert not OUT.exists();OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),ROOT/'iteration153/verification-manifest.json',ROOT/'iteration153/models.json',ROOT/'iteration153/predictions.json',ROOT/'iteration152/models.json',ROOT/'iteration144/verification-manifest.json',ROOT/'iteration144/selection.json',ROOT/'iteration144/features.json',ROOT/'iteration144/predictions.json',ROOT/'iteration144/summary.json',ROOT/'iteration139/common-core.json',ROOT/'iteration85/anchor-budgets.json',ROOT/'iteration93/types.json']
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='No fitting: frozen153source-selectedfullmodel vs152weakpenaltymonotonicfullmodel and144originaljointbaseline. EXACT14463nested1000/3000/4000windows3SHAstarts per7texts plus7fullreferences. Cached144features, unchanged>.5cutoff/candidatepresence. Freeze allpredictions beforemodalmetrics. Allpresenttype accuracy/NLL/AUC primary; supportedn>=5/common14secondary/missingfull16explicit. Fullsamepresent comparator to avoiddenominatorchanges. Allviews reported no author/windowchoice/no pooledindependencereplication. Fullrefs exact153selected and144original;152fixedmonotonicbaseline nearoriginal notexpectedbyteidentical. No newannotations/reserve/sealedworks/newrawtext/default/nuclei/generalPOSclaims.'))
    selection=load(ROOT/'iteration144/selection.json');features=load(ROOT/'iteration144/features.json');old=load(ROOT/'iteration144/predictions.json');models={'selected':load(ROOT/'iteration153/models.json')['full'],'fixed':load(ROOT/'iteration152/models.json')['full']};pred={}
    for key,configs in old.items():pred[key]={'original':configs['joint'],**{name:[dict(r,probabilities=dict(raw=predict_vector(features[key][r['opaque']],m))) for r in configs['joint']] for name,m in models.items()}}
    save(OUT/'predictions.json',pred);save(OUT/'predictions-freeze.json',dict(inputs={str(OUT/'predictions.json'):digest(OUT/'predictions.json')}));anchors=load(ROOT/'iteration85/anchor-budgets.json')['195'];core=set(load(ROOT/'iteration139/common-core.json'));catalogue=set(load(ROOT/'iteration93/types.json')['candidates']);summary={}
    for key,arms in pred.items():
        summary[key]={};w=selection[key]['work']
        for name,rows in arms.items():
            refs=[dict(r,**{'class':anchors[r['type']]}) for r in rows];present={r['type'] for r in rows};full=[dict(r,**{'class':anchors[r['type']]}) for r in pred[w+'/full'][name] if r['type'] in present];summary[key][name]=dict(tokens=selection[key]['stop']-selection[key]['start'],missing_types=sorted(catalogue-present),missing_common14=sorted(core-present),metrics={g:metrics(rr,'raw') for g,rr in [('all',refs),('supported',[r for r in refs if r['supported']]),('common14',[r for r in refs if r['type'] in core])]},full_same_present=metrics(full,'raw'))
    save(OUT/'summary.json',summary)
    for key,arms in summary.items():print(key,{a:(r['metrics']['all']['correct'],r['metrics']['all']['n'],r['metrics']['all']['nll']) for a,r in arms.items()},flush=True)
if __name__=='__main__':run()
