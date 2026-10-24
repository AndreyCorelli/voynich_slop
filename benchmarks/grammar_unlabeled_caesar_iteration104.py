"""More unlabeled context for a fixed author sample, fixed candidate core/policies."""
from benchmarks.grammar_core_uncertainty_iteration103 import *
from voynich_smt.unlabeled_caesar_context import BOOKS,extract,normalize,overlap_fragments,overlaps
from voynich_smt.pair_uncertainty import sentence_totals,gains_from_totals,summarize,selected
OUT=ROOT/'iteration104';RAW=Path('data/raw/word-mapping-caesar')


def prepare():
    # Only stored word sequences are used, not new grammatical annotations.
    cache=load(ROOT/'iteration40/data-truth.json');ids=load(ROOT/'iteration40/manifest.json')['split_ids']['Caesar'];scored=[dict(sent_id=sid,tokens=[dict(word=t['word']) for t in cache[sid]]) for sid in ids]
    assert len(scored)==100 and all(normalize(t['word'])==t['word'] for s in scored for t in s['tokens'])
    fragments=overlap_fragments(scored);hashes=load(RAW/'sha256.json');added={};metadata={}
    for book in BOOKS:
        path=RAW/f'voinich-caesar-{book}.html';raw=path.read_bytes();assert digest(path)==hashes[path.name];sentences,meta=extract(book,raw);meta['excluded_overlap']=overlaps(meta.pop('prose_letters'),fragments);metadata[book]=meta
        if not meta['excluded_overlap']:added[book]=sentences
    views={'base':scored,'civil':scored+[s for b,ss in added.items() if b.startswith('bc') for s in ss],'expanded':scored+[s for ss in added.values() for s in ss]}
    save(OUT/'context-selection.json',dict(books=metadata,views={k:dict(sentences=len(v),tokens=sum(len(s['tokens']) for s in v),added_books=[] if k=='base' else [b for b in added if k=='expanded' or b.startswith('bc')]) for k,v in views.items()},overlap_policy='Exclude ENTIRE book with any shared80contiguousnormalizedletters from a scoredsentence; normalizedlettersmergeuv/ij andignoretokenboundaries; all6bookfiles inspected, neverGallicI-IV.'))
    return views


def compute(public,case,replacements,anchors,core,model,weights,folder):
    changed=perturb(public,replacements,anchors);lookup={t['anchor']:t['id'] for s in public for t in s['tokens'] if t['anchor'] in core};proposed={t['id']:t['tag'] for s in changed for t in s['tokens'] if t['id'] in lookup.values()};counts={i:sum(t['id']==i for s in public for t in s['tokens']) for i in lookup.values()};ns={i:sum(any(t['id']==i for t in s['tokens']) for s in public) for i in lookup.values()};pairs=[];draws=[];totals=[]
    for a in sorted(i for i,p in proposed.items() if p=='ADP'):
        for c in sorted(i for i,p in proposed.items() if p=='CCONJ'):
            pair=sorted([a,c]);n,q=sentence_totals(changed,pair,model);tags=[proposed[i] for i in pair];gain=float(gains_from_totals(n.sum(0),q.sum(0),tags));p=dict(pair=pair,gain=gain,supported=all(counts[i]>=5 and ns[i]>=3 for i in pair));pairs.append(p)
            active=np.any(n>0,axis=1);draws.append(gains_from_totals(weights[:,active]@n[active],weights[:,active]@q[active],tags));totals.append((n,q))
    boot=np.array(draws).T;features=summarize(pairs,boot)
    np.savez_compressed(folder/(case+'.npz'),counts=np.array([n for n,q in totals]),sums=np.array([q for n,q in totals]),draws=boot)
    ref=reference_for(public,replacements,case.startswith('swap_'),pairs,core)
    row=dict(case=case,features=features,reference=ref,pairs=pairs,proposed=[[proposed[i] for i in p['pair']] for p in pairs],identities={v:k for k,v in lookup.items()},counts={w:dict(n=counts[i],sentences=ns[i]) for w,i in lookup.items()});save(folder/(case+'.json'),row);return row


def run():
    assert not OUT.exists();OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),Path('src/voynich_smt/unlabeled_caesar_context.py'),Path('benchmarks/expanded_medieval_latin.py'),Path('src/voynich_smt/pair_uncertainty.py'),ROOT/'iteration103/verification-manifest.json',ROOT/'iteration103/policies.json',ROOT/'iteration93/models.json',ROOT/'iteration100/core.json',ROOT/'iteration98/calibration-bank.json',ROOT/'iteration40/data-truth.json',ROOT/'iteration40/manifest.json',ROOT/'iteration85/anchor-budgets.json',RAW/'README.md',RAW/'sha256.json']+[RAW/f'voinich-caesar-{b}.html' for b in BOOKS]
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='CachedunlabeledCaesarcontext, NO network/newannotation/reserve/sealedlexicalaccess. ReadONLY6listedGallicV-VII/CivilI-IIIHTML, exactrawhashes. Original100Caesarwordsequences40fixed; additionalcontent numberedproseonly, normalize loweruv/ij, Unicodelettertokens, sentenceboundaries .!?; numericlabelsdiscarded, rawencliticsNOTsplit, abbreviationsegmentationlimitationsreported. ExcludeENTIREbookifANYnormalized80letterfragmentmatchesANYscoredsentencebeforemodelscoring. Freezecontextselection andpublicviews beforemodelscoring. Primaryexpandedallremainingbooks; secondaryCivilonly; base100control. Nooutcome-basedbookchoice. Globalsaltunlabeled104-Caesar makeswordIDsidenticalallviews. Same mappingglobalatALLoccurrences,195givenanchors fixed,allothersopaque. Frozen8core15errors+3controls, no errorfilter/reselection. Frozen93jointmodel/support5occ3sentences, 256sentencebootstrap sharedallpairs/caseswithinview seed104000+i, same102uncertainty; replicateeligibilityfixedoriginalset/missingselectedfails. Fixed95cutand103gain/gap policies(no calibration); 103uncertaintyOFF retained. Reportpairprecision/recall/unsupportedpartners/rank/stability/controls forALLviews/cases, everycounterexample; noaddedtextlabels, noPPintegrationthisiteration, no claimednuclei. Extra rawtextmaynotaddseparatequeoccurrences, documenttokenization mismatch ratherthan inventencliticexception. Reusedauthordevelopment100, notfreshconfirmation.'))
    views=prepare();anchors=load(ROOT/'iteration85/anchor-budgets.json')['195'];core=load(ROOT/'iteration100/core.json');bank={k:v for k,v in load(ROOT/'iteration98/calibration-bank.json').items() if not k.startswith('swap_') or set(v)<=set(core)};assert len(bank)==18
    model=load(ROOT/'iteration93/models.json')['context'];policies=load(ROOT/'iteration103/policies.json');save(OUT/'policies.json',policies);publics={k:ag.public_sentences(v,anchors,'unlabeled104-Caesar') for k,v in views.items()}
    for name,public in publics.items():save(OUT/('public-'+name+'.json'),public)
    save(OUT/'context-freeze.json',dict(inputs={str(p):digest(p) for p in [OUT/'context-selection.json',OUT/'policies.json']+list(OUT.glob('public-*.json'))}));evaluation=[]
    for vi,(view,public) in enumerate(publics.items()):
        folder=OUT/view;folder.mkdir();weights=np.random.default_rng(104000+vi).multinomial(len(public),np.full(len(public),1/len(public)),size=256);np.savez_compressed(folder/'weights.npz',weights=weights)
        for case,replacements in bank.items():
            row=compute(public,case,replacements,anchors,core,model,weights,folder);row.update(block=view,regime=view);evaluation.append(row);print(view,case,flush=True)
    save(OUT/'evaluation-cases.json',evaluation);save(OUT/'evaluation-summary.json',{arm:evaluate102(evaluation,p) for arm,p in policies.items()});save(OUT/'actions.json',{arm:{c['block']+'/'+c['case']:selected(c['features'],p) for c in evaluation} for arm,p in policies.items()});print(json.dumps(load(OUT/'evaluation-summary.json')),flush=True)
if __name__=='__main__':run()
