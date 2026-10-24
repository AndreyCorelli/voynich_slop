"""Frozen anchor-conditional PP policies on already cached held-out authors."""
from benchmarks.grammar_anchor_budget_iteration85 import *
OUT=ROOT/'iteration86';PREVIOUS=ROOT/'iteration85'
AUTHORS=('Jerome','Caesar');SETTINGS={'20':'empirical90','195':'conservative90'}
CACHE=ROOT/'iteration40/data-truth.json';DECLARATION=ROOT/'iteration40/manifest.json'

def cached_sentences(cache,ids):
    result=[]
    for sid in ids:
        ts=cache[sid]
        assert all(t['head'] is None or isinstance(t['head'],int) and 0<=t['head']<len(ts) for t in ts)
        result.append(dict(sent_id=sid,tokens=[dict(word=t['word'],pos=t['pos'],head=t['head'],rel=t['rel'],features={}) for t in ts]))
    return result

def transfer_rows(sentences,anchors,salt,classes):
    public=ag.public_sentences(sentences,anchors,salt);rows=ag.public_features(public);lookup={(s['sent_id'],i):(s['tokens'],t) for s in sentences for i,t in enumerate(s['tokens'])}
    for r in rows:
        ts,t=lookup[r['sid'],r['index']];pp,_=bundles(ts,[t['pos'] for t in ts],r['index']);r['labels']={'pp':'oraclePP:present=True' in pp};r['masked_center']=r['features'];r['gold_pos']=t['pos']
    return public,rows

def eval_transfer(rows,pol,selected_kind):
    source_policy=pol['pooled_pos']['standard']['precision90'] if selected_kind=='empirical90' else pol['pooled_pos']['conservative'];assert source_policy is not None;threshold=source_policy['threshold'];selected=[r for r in rows if r['scores']['pooled_pos']['pp']>=threshold];hidden=[r for r in rows if not r['visible']]
    result=dict(n=len(rows),positives=sum(r['labels']['pp'] for r in rows),visible_tokens=sum(r['visible'] for r in rows),threshold=threshold,selected_policy=counts(rows,'pp','pooled_pos',threshold),selected_types=len({r['word'] for r in selected}),selected_sentences=len({r['sid'] for r in selected}),hidden_selected_policy=counts(hidden,'pp','pooled_pos',threshold),source_f1_model=counts(rows,'pp','pooled_pos',pol['pooled_pos']['standard']['f1']['threshold']),source_f1_nearest=counts(rows,'pp','left',pol['left']['standard']['f1']['threshold']))
    return result

def run():
    assert not OUT.exists();OUT.mkdir()
    for p,h in load(PREVIOUS/'verification-manifest.json')['inputs'].items():assert digest(p)==h,p
    paths=[Path(__file__),Path('benchmarks/grammar_anchor_budget_iteration85.py'),Path('src/voynich_smt/anchor_grammar.py'),Path('src/voynich_smt/government_oracle.py'),CACHE,DECLARATION,ROOT/'iteration26/datasets.json',ROOT/'iteration49/manifest.json',ROOT/'iteration85/anchor-budgets.json',PREVIOUS/'verification-manifest.json',Path('experiments/holdouts/grammar-construction-next.json')]
    for b in SETTINGS:paths.extend([ROOT/('iteration85/budget-'+b)/name for name in ('models.json','policies.json')])
    (OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='Frozen crossauthor transfer: PRIMARYJerome100 cached40split, SECONDARYCaesar100 cached40split. Both alreadydeclared26 datasets, full40annotations; no rawtreebanknewqueries. Disjoint fromall49source4070splits, reserveIDs excluded. Allstoredtokens,noPOS/Case/constructionfilter. Exact85models andsourcepolicies:20anchorEMPIRICAL90threshold.81,195anchorCONSERVATIVEthreshold.80. No refit/recalibration/budgetselection fromtransfer. Existingfunctionanchors sourcefitmapping/tags supplied, allotherformsopaqueequality, fixedsourcefeatures/contextPOSensemble/stricttrainedpool PP. Public/privatefeatureseparation retained. Reportbothauthors/bothsettings, knownanchorcoverage, selectedcorrect/wrong/precision/recall/types, hiddensubset, frozenF1model andnearestleftcontrol. These cacheddevelopmentsets previouslyusedotherexperiments, notfreshindependentconfirmation; currentmodels nevertrained/calibratedonbothauthors. No reserve/sealedtest/search.'))
    declaration=load(DECLARATION)['split_ids'];data=load(CACHE);datasets=load(ROOT/'iteration26/datasets.json');source_part=load(ROOT/'iteration49/manifest.json')['partitions']['0'];source_ids={sid for ids in source_part.values() for sid in ids};reserved={r['sent_id'] for rr in load('experiments/holdouts/grammar-construction-next.json')['authors'].values() for r in rr};catalogue=load(ROOT/'iteration85/anchor-budgets.json');summaries={};selected_ids={a:declaration[a] for a in AUTHORS}
    for author in AUTHORS:
        ids=selected_ids[author];assert len(ids)==100 and len(set(ids))==100 and not set(ids)&(source_ids|reserved);assert set(ids)=={s['sent_id'] for s in datasets[author.lower()]};sentences=cached_sentences(data,ids);reference={s['sent_id']:s['tokens'] for s in datasets[author.lower()]}
        assert all([t['word'] for t in s['tokens']]==reference[s['sent_id']] for s in sentences)
        for budget,kind in SETTINGS.items():
            folder=OUT/(author.lower()+'-'+budget);folder.mkdir();base=ROOT/('iteration85/budget-'+budget);models=load(base/'models.json');pol=load(base/'policies.json');public,queries=transfer_rows(sentences,catalogue[budget],'transfer86-'+author,models['pos_classes']);save(folder/'public.json',public);rows=infer85(queries,models);save(folder/'predictions.json',rows);save(folder/'prediction-freeze.json',dict(inputs={str(p):digest(p) for p in (folder/'predictions.json',folder/'public.json')}));summaries[author+'/'+budget]=eval_transfer(rows,pol,kind);save(folder/'evaluation.json',summaries[author+'/'+budget]);print(author,budget,json.dumps(summaries[author+'/'+budget]),flush=True)
    save(OUT/'selected-ids.json',selected_ids);save(OUT/'evaluation.json',summaries)
if __name__=='__main__':run()
