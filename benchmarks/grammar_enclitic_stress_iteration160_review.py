"""Independent joining, feature, reference and tie-bound stress audit."""
from benchmarks.grammar_enclitic_stress_iteration160 import *
from benchmarks.grammar_broad_author_iteration158_review import tie_bounds
from benchmarks.grammar_joint_scalars_iteration142_review import combined
from benchmarks.scalable_latin_caesar import words as source_words

def run():
    hc=fc=pc=mc=0
    for name in ['design-freeze','input-freeze','predictions-freeze']:
        for p,h in load(OUT/(name+'.json'))['inputs'].items():assert digest(p)==h,p;hc+=1
    archive=ROOT/'iteration160-preflight-initial';initial=load(archive/'design-freeze.json')
    for p,h in initial['inputs'].items():assert digest(archive/'runner-initial.py' if p.endswith('grammar_enclitic_stress_iteration160.py') else p)==h,p
    assert not (archive/'predictions.json').exists() and not (archive/'features.json').exists()
    sel={**load(ROOT/'iteration158/selection.json'),**load(ROOT/'iteration159/selection.json')};old=load(ROOT/'iteration40/data-truth.json');source=load(ROOT/'iteration44/annotations-truth.json');public=load(OUT/'word-views.json');events=load(OUT/'join-events.json');features=load(OUT/'features.json');pred=load(OUT/'predictions.json');refs=load(OUT/'references.json');summary=load(OUT/'summary.json');metadata=load(OUT/'boundary-metadata.json');models=load(ROOT/'iteration157/models.json');bounds={};expected={};source_ids=set();reserved={r['sent_id'] for rr in load('experiments/holdouts/grammar-construction-next.json')['authors'].values() for r in rr}
    for author,s in sel.items():
        ss=[];ev=[];assert not set(s['sent_ids'])&reserved
        for sid in s['sent_ids']:
            tt=old[sid] if author in ['Caesar','Jerome'] else source[sid]['tokens'];expected[sid]=[t['word'] for t in tt]
            if author in ['Cicero','Palladius']:source_ids.add(sid)
            original=[dict(word=t['word'],parts=[t]) for t in tt];groups=[]
            for k,t in enumerate(tt):
                if groups and (t['word'] in {'que','ue'} or (t['word']=='c' and groups[-1]['word']=='ne')):
                    ev.append(dict(sent_id=sid,index=k,host=groups[-1]['word'],component=t['word']));groups[-1]['word']+=t['word'];groups[-1]['parts'].append(t)
                else:groups.append(dict(word=t['word'],parts=[t]))
            ss.append((sid,original,groups))
        assert ev==events[author];bounds[author]={}
        for view,idx in [('original',1),('joined',2)]:
            assert public[author][view]==[dict(sent_id=sid,words=[t['word'] for t in row[idx]]) for row in ss for sid in [row[0]]];tokens=[t for row in ss for t in row[idx]];counts=Counter(t['word'] for t in tokens);eligible={w for w,n in counts.items() if n>=5};lookup={w:hashlib.sha256(('enclitic160-'+author+'|'+w).encode()).hexdigest() for w in eligible};ids=[hashlib.sha256(('enclitic160-'+author+'|'+t['word']).encode()).hexdigest() for t in tokens];f=combined(ids,set(lookup.values()));assert set(f)==set(features[author][view]);bounds[author][view]={}
            for i,ff in f.items():
                for c in ff:assert abs(ff[c]-features[author][view][i][c])<1e-11
                fc+=1
            for policy in ['host','component']:
                cc={}
                for t in tokens:
                    tags=[p['pos'] for p in t['parts']];tag=tags[0] if policy=='host' else next((p for p in tags if p in POSITIVE),tags[0]);cc.setdefault(t['word'],Counter())[tag]+=1
                labels={w:int(sorted(cc[w],key=lambda p:(-cc[w][p],p))[0] in POSITIVE) for w in eligible};assert labels==refs[author][view][policy];bounds[author][view][policy]={}
                for name,pp in pred[author][view].items():
                    assert set(pp)==eligible;m=models[name]['final']
                    if policy=='host':
                        for w,p in pp.items():
                            ff=dict(f[lookup[w]],frequency=math.log1p(counts[w]));x=(np.array([ff[c] for c in m['columns']])-m['mean'])/m['scale'];q=float(expit(m['beta'][0]+x@np.array(m['beta'][1:])));assert abs(p-q)<1e-9;pc+=1
                    assert summary[author][view][policy][name]==detection_metrics(pp,labels);bounds[author][view][policy][name]={str(k):tie_bounds(pp,labels,k) for k in [5,10,20,50]};mc+=1
            if view=='original':
                historical=load(ROOT/('iteration158' if author in ['Caesar','Jerome'] else 'iteration159')/'summary.json')[author]['raw'];assert summary[author][view]['host']==historical
    found={}
    for path in RAW:
        for block in path.read_text().split('\n\n'):
            lines=block.splitlines();sid=next((line.split(' = ',1)[1] for line in lines if line.startswith('# sent_id = ')),None)
            if sid not in expected:continue
            rows=[line.split('\t') for line in lines if line and not line.startswith('#')];norm=(lambda w:list(source_words(w))) if sid in source_ids else (lambda w:[w.lower().replace('v','u').replace('j','i')] if any(c.isalpha() for c in w) else []);forms=[w for r in rows if r[0].isdecimal() for w in norm(r[1])];assert forms==expected[sid];text=next((line.split(' = ',1)[1] for line in lines if line.startswith('# text = ')),None);record=dict(multiword_ranges=sum('-' in r[0] for r in rows),spaceafter_no=sum('SpaceAfter=No' in r[-1] for r in rows),text_present=text is not None,text_matches_split_forms=([w for token in text.split() for w in norm(token)]==forms if text is not None else False));assert record==metadata[sid];found[sid]=record
    assert set(found)==set(expected);save(OUT/'tie-bounds.json',bounds);save(OUT/'audit.json',dict(input_hashes_verified=hc,initial_preflight_archive_verified=True,metadata_sentences_verified=len(found),source_and_reserve_projection_restricted=True,all_join_events_verified=sum(map(len,events.values())),independent_feature_vectors=fc,probabilities_independently_replayed=pc,metric_groups_replayed=mc,original_author_summaries_matched=4,all_policies_and_tie_bounds_retained=True,no_fitting=True))
if __name__=='__main__':run()
