"""Fixed conditional case rule on additional cached nonoverlapping passages."""
from benchmarks.grammar_rare_case_frames_iteration167 import *
from benchmarks.scalable_latin_caesar import words as normalize_words
OUT=ROOT/'iteration168';STREAMS=['background-Jerome','background-Palladius','fit-Cicero','fit-Palladius']
RAW=[Path('data/latin-grammar-benchmark/proiel-r2.17')/('la_proiel-ud-'+s+'.conllu') for s in ['train','dev','test']]

def header_authors(wanted):
    result={};mapping={"Jerome's Vulgate":'Jerome','Opus agriculturae':'Palladius'}
    for path in RAW:
        sid=source=None
        for line in path.open():
            if line.startswith('# sent_id = '):sid=line.strip().split(' = ',1)[1]
            elif line.startswith('# source = '):source=line.strip().split(' = ',1)[1].split(',')[0]
            elif not line.strip():
                if sid in wanted:result[sid]=mapping[source]
                sid=source=None
        if sid in wanted:result[sid]=mapping[source]
    assert set(result)==wanted;return result

def signature(words):return tuple(w for token in words for w in normalize_words(token))

def select_passages():
    previous={**load(ROOT/'iteration158/selection.json'),**load(ROOT/'iteration159/selection.json')};oldids={sid for r in previous.values() for sid in r['sent_ids']};reserved={r['sent_id'] for rr in load('experiments/holdouts/grammar-construction-next.json')['authors'].values() for r in rr};views=load(ROOT/'iteration160/word-views.json');seen={signature(s['words']) for vv in views.values() for ss in vv.values() for s in ss};background=load(ROOT/'iteration40/manifest.json')['split_ids']['source'];authors=header_authors(set(background));old=load(ROOT/'iteration40/data-truth.json');source=load(ROOT/'iteration44/annotations-truth.json');fit=load(ROOT/'iteration49/manifest.json')['partitions']['0']['fit'];candidates={'background-'+a:[sid for sid in background if authors[sid]==a] for a in ['Jerome','Palladius']};candidates.update({'fit-'+a:[sid for sid in fit if source[sid]['author']==a] for a in ['Cicero','Palladius']});selection={};sentences={};seenids=set(oldids)
    for key in STREAMS:
        kept=[];rejected=[];ss=[]
        for sid in candidates[key]:
            reason='reserved' if sid in reserved else 'sentence_id_overlap' if sid in seenids else None
            if reason:rejected.append(dict(sent_id=sid,reason=reason));continue
            tt=old[sid] if key.startswith('background-') else source[sid]['tokens'];sig=signature([t['word'] for t in tt])
            if sig in seen:rejected.append(dict(sent_id=sid,reason='normalized_sequence_overlap'));continue
            kept.append(sid);ss.append(dict(sent_id=sid,words=[t['word'] for t in tt]));seen.add(sig);seenids.add(sid)
        selection[key]=dict(candidate_sentences=len(candidates[key]),sent_ids=kept,rejected=rejected,author=key.split('-',1)[1],provenance='iteration40 background' if key.startswith('background-') else 'iteration44 source-fit',development_reuse=True);sentences[key]=ss
    return selection,sentences

def run():
    assert not OUT.exists();OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),ROOT/'iteration167/verification-manifest.json',ROOT/'iteration40/manifest.json',ROOT/'iteration40/data-truth.json',ROOT/'iteration44/annotations-truth.json',ROOT/'iteration49/manifest.json',ROOT/'iteration158/selection.json',ROOT/'iteration159/selection.json',ROOT/'iteration160/word-views.json',Path('experiments/holdouts/grammar-construction-next.json')]+RAW
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='Replicationfixed166conditionalcase rule, no thresholds/tuning/newannotations. EXACT4predeclaredcachedpools:40sourcebackgroundJerome/Palladius,49partition0fitCicero/Palladius. Authorfromcached44metadata orrawHEADERONLY source/sent_id for40; neverrawPOS/FORM. FixedpoolorderbackgroundJerome,backgroundPalladius,fitCicero,fitPalladius; originalIDorder. EXCLUDEreserved/prior158+159IDs, exactnormalizedwordsequenceoverlapwithALL160original/joinedsentences, within/acrossnewpools dedup inthatorder. Normalizeforsignature existingLatinwords tokenizer, inferencewordsunchanged. Freeze selections/rejectionreasons/wordstreams beforegraphs. PRIMARYfloor5/twoDISTINCTsharedframes, floor2fixedcontrol andoneframesecondary allreported. Samecaseinventory/pair-frame-edgeweighting/null16seeds16400..15; no changingseedstogetnullseparation. IndependentlysaltedflatopaqueIDs/noPOS/purity/catalogueforedges; casesonlyconditionalreference afterdescriptorsfreeze. Freezeallcomparisonsbeforeaggregate/nullmetrics. Reportperpoolhistory/counts/applicability/coverage/precision/conflictfree/nulls, emptyNone. Dataalreadydeveloped/sourceauthorsseenelsewhere; unsupervisedrulehasnofittedlabels, theseNOTfreshindependentauthorconfirmations. No reservefeatures/sealedworks/namedcases/nuclei/deploymentclaim.'))
    selection,sentences=select_passages();streams={};transforms={}
    for key,ss in sentences.items():
        words=[w for s in ss for w in s['words']];streams[key]=[hashlib.sha256(('replication168-'+key+'|'+w).encode()).hexdigest() for w in words];selection[key]['tokens']=len(words);selection[key]['types']=len(set(words));transforms[key]={'original':None,**{'word'+str(seed):np.random.default_rng(seed).permutation(len(words)).tolist() for seed in SEEDS}}
    for name,x in [('selection',selection),('word-inputs',sentences),('streams',streams),('transforms',transforms)]:save(OUT/(name+'.json'),x)
    save(OUT/'input-freeze.json',dict(inputs={str(OUT/(n+'.json')):digest(OUT/(n+'.json')) for n in ['selection','word-inputs','streams','transforms']}));descriptors={};eligibility={}
    for key,seq in streams.items():
        descriptors[key]={};eligibility[key]={}
        for floor in [5,2]:
            f=str(floor);descriptors[key][f]={};eligibility[key][f]=sum(n>=floor for n in Counter(seq).values())
            for view,ix in transforms[key].items():dd,n=descriptors_for(seq if ix is None else [seq[k] for k in ix],floor);assert n==eligibility[key][f];descriptors[key][f][view]=dd
    save(OUT/'descriptors.json',descriptors);save(OUT/'eligibility.json',eligibility);save(OUT/'descriptors-freeze.json',dict(inputs={str(OUT/n):digest(OUT/n) for n in ['descriptors.json','eligibility.json']}));old=load(ROOT/'iteration40/data-truth.json');source=load(ROOT/'iteration44/annotations-truth.json');case_inputs={};details={}
    for key,r in selection.items():
        case_inputs[key]=[t.get('case','') for sid in r['sent_ids'] for t in (old[sid] if key.startswith('background-') else source[sid]['tokens'])];assert len(case_inputs[key])==len(streams[key]);details[key]={}
        for floor,vv in descriptors[key].items():
            details[key][floor]={}
            for view,dd in vv.items():ix=transforms[key][view];cases=case_inputs[key] if ix is None else [case_inputs[key][k] for k in ix];details[key][floor][view]=score_cases(dd,cases)
    save(OUT/'case-inputs.json',case_inputs);save(OUT/'details.json',details);save(OUT/'scores-freeze.json',dict(inputs={str(OUT/n):digest(OUT/n) for n in ['case-inputs.json','details.json']}));summary={k:{floor:{view:summarize_cases(dd,eligibility[k][floor]) for view,dd in vv.items()} for floor,vv in ff.items()} for k,ff in details.items()};contrasts={}
    for key,ff in summary.items():
        contrasts[key]={}
        for floor,vv in ff.items():
            contrasts[key][floor]={}
            for threshold in ['1','2']:
                actual=vv['original'][threshold];pp=[vv['word'+str(seed)][threshold]['edge_macro_frame_case_agreement'] for seed in SEEDS if vv['word'+str(seed)][threshold]['case_edges']];v=actual['edge_macro_frame_case_agreement'];contrasts[key][floor][threshold]=dict(actual=actual,null_with_case=len(pp),null_mean=float(np.mean(pp)) if pp else None,null_max=max(pp) if pp else None,null_at_least_actual=sum(p>=v for p in pp) if v is not None else None)
        print(key,selection[key]['tokens'],len(selection[key]['sent_ids']),{f:tt['2'] for f,tt in contrasts[key].items()},flush=True)
    save(OUT/'summary.json',summary);save(OUT/'contrasts.json',contrasts)
if __name__=='__main__':run()
