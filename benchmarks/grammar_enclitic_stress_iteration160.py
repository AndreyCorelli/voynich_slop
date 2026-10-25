"""Boundary metadata audit and predeclared label-blind enclitic joining stress."""
from benchmarks.grammar_broad_author_iteration158 import *
OUT=ROOT/'iteration160';AUTHORS=['Caesar','Jerome','Cicero','Palladius']
RAW=[Path('data/latin-grammar-benchmark/proiel-r2.17')/('la_proiel-ud-'+split+'.conllu') for split in ['train','dev','test']]

def joined_sentences(sentences):
    result=[];events=[]
    for s in sentences:
        tokens=[]
        for k,t in enumerate(s['tokens']):
            w=t['word'];join=bool(tokens) and (w in ['que','ue'] or (w=='c' and tokens[-1]['word']=='ne'))
            if join:
                prev=tokens[-1];events.append(dict(sent_id=s['sent_id'],index=k,host=prev['word'],component=w));prev['word']+=w;prev['parts'].append(dict(t))
            else:tokens.append(dict(word=w,parts=[dict(t)]))
        result.append(dict(sent_id=s['sent_id'],tokens=tokens))
    return result,events

def metadata_audit(selected,expected,source_ids):
    from benchmarks.scalable_latin_caesar import words as source_words
    found={}
    def finish(block):
        headers={line[2:].split(' = ',1)[0]:line[2:].split(' = ',1)[1] for line in block if line.startswith('# ') and ' = ' in line}
        sid=headers.get('sent_id')
        if sid not in selected:return
        rows=[line.split('\t') for line in block if line and not line.startswith('#')]
        normalize=(lambda w:list(source_words(w))) if sid in source_ids else (lambda w:[w.lower().replace('v','u').replace('j','i')] if any(c.isalpha() for c in w) else [])
        forms=[w for r in rows if r[0].isdecimal() for w in normalize(r[1])];assert forms==expected[sid],sid
        text=headers.get('text');textforms=[w for token in text.split() for w in normalize(token)] if text else None
        found[sid]=dict(multiword_ranges=sum('-' in r[0] for r in rows),spaceafter_no=sum('SpaceAfter=No' in r[-1] for r in rows),text_present=text is not None,text_matches_split_forms=textforms==forms)
    for path in RAW:
        block=[]
        for line in path.open():
            line=line.rstrip('\n\r')
            if not line:finish(block);block=[]
            else:block.append(line)
        if block:finish(block)
    assert set(found)==selected;return found

def run():
    assert not OUT.exists();OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),ROOT/'iteration160-preflight-initial/runner-initial.py',ROOT/'iteration160-preflight-initial/design-freeze.json',ROOT/'iteration160-preflight-initial/failure.json',Path('benchmarks/scalable_latin_caesar.py'),ROOT/'iteration158/selection.json',ROOT/'iteration158/summary.json',ROOT/'iteration159/selection.json',ROOT/'iteration159/summary.json',ROOT/'iteration157/models.json',ROOT/'iteration40/data-truth.json',ROOT/'iteration44/annotations-truth.json',Path('experiments/holdouts/grammar-construction-next.json')]+RAW
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='Amended beforefeatures: preserve failedmetadata preflight archive; apply exact40 vs44 cached normalization byauthor (existing44tokenizer), no taskdesignchange. Four exact158/159authorsets, boundarymetadata audit ONLYadmittedsentIDs before FORM/MISCprojection; no newPOS/annotations/reserve/sealedworks. No MWT/SpaceAfter known frompreflight, textitselfsplit: cannotclaim exactorthographicreconstruction. PREDECLAREDlabelblindstressjoin eachque/ue toprecedingtoken within sentence; cONLYafterliteralne ->nec; nevercrosssentence, initialcomponentsleftuntouched. No wordexception/errorselection. CachePOSonly referenceprojections: host(firstcomponent)POS primary; component policy firstpositivecomponentPOS ifany elsehost, explicitgenerous alternative not validatedwordPOS. Original andjoined views, rawfrozen1573models/no fitting/source-lengthcontrol (scope rawonlyhere), all>=5typeseligible/no purityfilter/cataloguefilter. Freezewordviews/eventsbeforefeatures/allpredictionsbefore projectedreferences/metrics. Alltop5/10/20/50/tiebounds/precisionrecallAPAUCNLL perauthor/arm/view/projection, no favorablepolicychoice. Compareoriginalreferences exact158/159. Changesinseveralwordidentities/counts/groupedreferences meansstressdiagnostic nottrueorthographicPOSvalidation. Coarsegrammaticalcue notnuclei/exactPOS.'))
    oldtruth=load(ROOT/'iteration40/data-truth.json');source=load(ROOT/'iteration44/annotations-truth.json');selection={**load(ROOT/'iteration158/selection.json'),**load(ROOT/'iteration159/selection.json')};sentences={};expected={};reserved={r['sent_id'] for rr in load('experiments/holdouts/grammar-construction-next.json')['authors'].values() for r in rr}
    for author,s in selection.items():
        assert not set(s['sent_ids'])&reserved;sentences[author]=[dict(sent_id=sid,tokens=oldtruth[sid] if author in ['Caesar','Jerome'] else source[sid]['tokens']) for sid in s['sent_ids']];expected.update({s['sent_id']:[t['word'] for t in s['tokens']] for s in sentences[author]})
    metadata=metadata_audit(set(expected),expected,{s['sent_id'] for a,ss in sentences.items() if a in ['Cicero','Palladius'] for s in ss});save(OUT/'boundary-metadata.json',metadata);views={};events={};public={}
    for author,ss in sentences.items():
        joined,events[author]=joined_sentences(ss);views[author]={'original':[dict(sent_id=s['sent_id'],tokens=[dict(word=t['word'],parts=[dict(t)]) for t in s['tokens']]) for s in ss],'joined':joined};public[author]={v:[dict(sent_id=s['sent_id'],words=[t['word'] for t in s['tokens']]) for s in sentences] for v,sentences in views[author].items()}
    save(OUT/'word-views.json',public);save(OUT/'join-events.json',events);save(OUT/'input-freeze.json',dict(inputs={str(OUT/n):digest(OUT/n) for n in ['word-views.json','join-events.json','boundary-metadata.json']}));models=load(ROOT/'iteration157/models.json');features={};pred={};lookups={}
    for author,vv in public.items():
        features[author]={};pred[author]={};lookups[author]={}
        for view,ss in vv.items():
            words=[w for s in ss for w in s['words']];counts=Counter(words);lookup={w:hashlib.sha256(('enclitic160-'+author+'|'+w).encode()).hexdigest() for w,n in counts.items() if n>=5};ids=[hashlib.sha256(('enclitic160-'+author+'|'+w).encode()).hexdigest() for w in words];f=features_for(ids,set(lookup.values()));features[author][view]=f;lookups[author][view]=lookup;pred[author][view]={name:{w:probability(dict(f[i],frequency=math.log1p(f[i]['n'])),mm['final']) for w,i in lookup.items()} for name,mm in models.items()}
    save(OUT/'features.json',features);save(OUT/'predictions.json',pred);save(OUT/'predictions-freeze.json',dict(inputs={str(OUT/n):digest(OUT/n) for n in ['features.json','predictions.json']}));refs={};summary={}
    for author,vv in views.items():
        refs[author]={};summary[author]={}
        for view,ss in vv.items():
            refs[author][view]={};summary[author][view]={}
            for policy in ['host','component']:
                cc={}
                for s in ss:
                    for t in s['tokens']:
                        parts=t['parts'];tag=parts[0]['pos']
                        if policy=='component':tag=next((p['pos'] for p in parts if p['pos'] in POSITIVE),tag)
                        cc.setdefault(t['word'],Counter())[tag]+=1
                labels={w:int(sorted(c,key=lambda tag:(-c[tag],tag))[0] in POSITIVE) for w,c in cc.items() if w in lookups[author][view]};refs[author][view][policy]=labels;summary[author][view][policy]={name:detection_metrics(pp,labels) for name,pp in pred[author][view].items()}
    save(OUT/'references.json',refs);save(OUT/'summary.json',summary)
    for author,vv in summary.items():print(author,'JOINS',len(events[author]),{view:{policy:{name:(r['top']['10']['correct'],r['top']['10']['n']) for name,r in arms.items()} for policy,arms in policies.items()} for view,policies in vv.items()},flush=True)
if __name__=='__main__':run()
