"""Frozen joint classifier on matched nested token windows in seven texts."""
from benchmarks.grammar_joint_author_replication_iteration143 import *
from benchmarks.grammar_overlap_token_budget_iteration139 import streams_and_lookups
OUT=ROOT/'iteration144';SIZES=[1000,3000,4000];SEEDS=[14400,14401,14402]

def inputs():
    streams,lookups=streams_and_lookups();streams.update(load(ROOT/'iteration143/streams.json'));lookups.update({w:r['lookup'] for w,r in load(ROOT/'iteration143/selection.json').items()});return streams,lookups

def selection_for(streams):
    selected={}
    for work,seq in streams.items():
        selected[work+'/full']=dict(work=work,start=0,stop=len(seq))
        for seed in SEEDS:
            start=int(hashlib.sha256((str(seed)+'|'+work).encode()).hexdigest(),16)%(len(seq)-4000+1)
            for n in SIZES:
                lo=start+(4000-n)//2;selected[f'{work}/{seed}/{n}']=dict(work=work,start=lo,stop=lo+n)
    return selected

def summarize(pred,selection,lookups):
    anchors=load(ROOT/'iteration85/anchor-budgets.json')['195'];core=set(load(ROOT/'iteration139/common-core.json'));catalogue=set(load(ROOT/'iteration93/types.json')['candidates']);out={}
    for key,configs in pred.items():
        out[key]={};work=selection[key]['work']
        for name,rows in configs.items():
            refs=[dict(r,**{'class':anchors[r['type']]}) for r in rows];present={r['type'] for r in rows};full=[dict(r,**{'class':anchors[r['type']]}) for r in pred[work+'/full'][name] if r['type'] in present]
            out[key][name]=dict(tokens=selection[key]['stop']-selection[key]['start'],missing_types=sorted(catalogue-present),missing_common14=sorted(core-present),metrics={g:metrics(rr,'raw') for g,rr in [('all',refs),('supported',[r for r in refs if r['supported']]),('common14',[r for r in refs if r['type'] in core])]},full_same_present=metrics(full,'raw'))
    return out

def run():
    assert not OUT.exists();OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),Path('benchmarks/grammar_joint_author_replication_iteration143.py'),Path('benchmarks/grammar_overlap_token_budget_iteration139.py'),ROOT/'iteration142/models.json',ROOT/'iteration142/summary.json',ROOT/'iteration143/summary.json',ROOT/'iteration143/streams.json',ROOT/'iteration143/selection.json',ROOT/'iteration138/streams.json',ROOT/'iteration138/selection.json',ROOT/'iteration135/predictions.json',ROOT/'iteration139/common-core.json',ROOT/'iteration85/anchor-budgets.json',ROOT/'iteration93/types.json',Path('src/voynich_smt/opaque_context_overlap.py'),Path('src/voynich_smt/opaque_context_roles.py')]+[INPUTS[a]['expanded'] for a in ['Caesar','Jerome']]
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='Frozen142 joint RAW primary, corrected/roles RAW controls all reported without author selection. Seven already inspected streams; no new raw text, labels, reserve, sealed works, fitting, offsets or PP. Three SHA(seed|work) modulo N-4000+1 starts seeds14400..2; nested centered1000/3000/4000 windows and full references:70 views. Freeze selections before features and predictions before metrics. All present catalogue types primary; missing relative full16 explicit, n>=5 and existing139 common14 secondary. Full same-present paired comparator. No favorable window selection, no pooled independent replication claim or universal length threshold. This diagnoses volume versus text-specific failure; no general POS/nuclei claim.'))
    streams,lookups=inputs();selected=selection_for(streams);assert len(selected)==70;save(OUT/'selection.json',selected);save(OUT/'selection-freeze.json',dict(inputs={str(OUT/'selection.json'):digest(OUT/'selection.json')}));models=load(ROOT/'iteration142/models.json');features={};pred={}
    for key,r in selected.items():
        seq=streams[r['work']][r['start']:r['stop']];lookup=lookups[r['work']];f=features_for(seq,set(lookup.values()));features[key]=f;pred[key]={name:[dict(type=w,opaque=i,n=f[i]['n'],sentences=1,supported=f[i]['n']>=5,probabilities=dict(raw=predict_vector(f[i],models[name]['final']))) for w,i in sorted(lookup.items()) if i in f] for name in CONFIGS}
        print('predicted',key,flush=True)
    save(OUT/'features.json',features);save(OUT/'predictions.json',pred);save(OUT/'predictions-freeze.json',dict(inputs={str(OUT/n):digest(OUT/n) for n in ['features.json','predictions.json']}));summary=summarize(pred,selected,lookups);save(OUT/'summary.json',summary)
    for key,r in summary.items():
        m=r['joint']['metrics']['all'];print(key,m['correct'],m['n'],m['auc'],m['nll'],flush=True)
if __name__=='__main__':run()
