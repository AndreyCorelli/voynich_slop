"""Frozen four-text overlap classifier under matched contiguous token budgets."""
from benchmarks.grammar_overlap_raw_latin_iteration138 import *
OUT=ROOT/'iteration139';SIZES=[1000,3000,7000];SEEDS=[13900,13901,13902]

def streams_and_lookups():
    original=load(ROOT/'iteration135/predictions.json');streams={};lookups={}
    for author in ['Caesar','Jerome']:
        public=load(INPUTS[author]['expanded']);streams[author]=[t['id'] for s in public for t in s['tokens']];lookups[author]={r['type']:r['opaque'] for r in original[author+'-expanded']['corrected']}
    raw=load(ROOT/'iteration138/streams.json');selection=load(ROOT/'iteration138/selection.json')
    for w in WORKS:streams[w]=raw[w];lookups[w]=selection[w]['lookup']
    return streams,lookups

def run():
    assert not OUT.exists();OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),ROOT/'iteration138/verification-manifest.json',ROOT/'iteration138/streams.json',ROOT/'iteration138/selection.json',ROOT/'iteration138/four-text-summary.json',ROOT/'iteration135/models.json',ROOT/'iteration135/calibrators.json',ROOT/'iteration135/predictions.json',ROOT/'iteration85/anchor-budgets.json',Path('src/voynich_smt/opaque_context_overlap.py')]+[INPUTS[a]['expanded'] for a in ['Caesar','Jerome']]
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='Frozen135models/calibrators>.5, anchorfree/sentencefree matchedTOKENbudget diagnostic on exact138fourtexts. Primarycorrected; raw/frequencycontrols frozen/reportallneverselectauthorarm. Fixed3SHAwork-seed starts13900/1/2 forlargest7000contiguouswindow, start=int(SHA(seed|work),16)mod(N-7000+1). Smaller1000/3000windows centeredwithinthat7000window=>nested. All4fullstreamsreferenceoncemustmatch138. 40views, overlapsNOTindependentreplications. Freezeallwindowindices BEFOREstatistics/predictions. Allpresenttypesprimary, missing/supportocc>=5reportonly; fixedintersectionoffullpresentcatalogues secondaryCOMMON14, missingcoreexplicit, comparefullsamepresenttypes. Freezeallpredictions beforeoldsourceMAPreferences/metrics. No new annotations/rawnormalization/initial/cliticrepair/sealedworks/reserve/fitting/PP/default/nuclei. Gelliussourcecmodalmismatch retainedprimary, commoncoredefinedbypresenceONLYnotoutcomes. CompareALL3windowsperbudget no favorablewindow/tokencutoffselection, no pooledaccuracygeneralguarantee.'))
    streams,lookups=streams_and_lookups();assert min(map(len,streams.values()))>=7000;selection={};fullpresent={w:{t for t,i in lookups[w].items() if i in set(seq)} for w,seq in streams.items()};core=sorted(set.intersection(*fullpresent.values()));assert len(core)==14
    for work,seq in streams.items():
        selection[work+'/full']=dict(work=work,start=0,stop=len(seq),full=True)
        for seed in SEEDS:
            start=int(hashlib.sha256((str(seed)+'|'+work).encode()).hexdigest(),16)%(len(seq)-7000+1)
            for n in SIZES:
                lo=start+(7000-n)//2;selection[work+'/'+str(seed)+'/'+str(n)]=dict(work=work,start=lo,stop=lo+n,full=False)
    save(OUT/'selection.json',selection);save(OUT/'common-core.json',core);save(OUT/'selection-freeze.json',dict(inputs={str(OUT/n):digest(OUT/n) for n in ['selection.json','common-core.json']}));models=load(ROOT/'iteration135/models.json');cal=load(ROOT/'iteration135/calibrators.json');savedstats={};pred={}
    for key,r in selection.items():
        work=r['work'];seq=streams[work][r['start']:r['stop']];lookup=lookups[work];st=statistics([dict(tokens=[dict(id=i) for i in seq])],set(lookup.values()));savedstats[key]=st;pred[key]={}
        for arm in ARMS:
            rr=[]
            for word,i in sorted(lookup.items()):
                if i not in st:continue
                raw=predict_scalar(st[i][arm],models[arm]['final']);rr.append(dict(type=word,opaque=i,n=st[i]['n'],sentences=1,supported=st[i]['n']>=5,statistic=st[i][arm],probabilities=dict(raw=raw,new=float(apply_offset([raw],cal[arm])[0]),prior=.5)))
            pred[key][arm]=rr
    save(OUT/'statistics.json',savedstats);save(OUT/'predictions.json',pred);save(OUT/'predictions-freeze.json',dict(inputs={str(OUT/n):digest(OUT/n) for n in ['statistics.json','predictions.json']}));anchors=load(ROOT/'iteration85/anchor-budgets.json')['195'];summary={};paired={}
    for key,arms in pred.items():
        work=selection[key]['work'];summary[key]={};paired[key]={}
        for arm,rows in arms.items():
            refs=[dict(r,**{'class':anchors[r['type']]}) for r in rows];present={r['type'] for r in rows};full={r['type']:dict(r,**{'class':anchors[r['type']]}) for r in pred[work+'/full'][arm]};summary[key][arm]=dict(tokens=selection[key]['stop']-selection[key]['start'],missing_types=sorted(set(lookups[work])-present),missing_common_core=sorted(set(core)-present),metrics={g:{p:metrics(rr,p) for p in ['new','raw','prior']} for g,rr in [('all',refs),('supported',[r for r in refs if r['supported']]),('common_core_present',[r for r in refs if r['type'] in core])]});paired[key][arm]=metrics([full[w] for w in sorted(present)],'new')
        m=summary[key]['corrected']['metrics']['all']['new'];print('RESULT',key,m['correct'],m['n'],m['auc'],m['nll'],flush=True)
    save(OUT/'summary.json',summary);save(OUT/'full-same-present.json',paired)
if __name__=='__main__':run()
