"""Frozen-policy stress test of source-chosen missing/mistaken anchors."""
from benchmarks.grammar_anchor_transfer_iteration86 import *
from voynich_smt.anchor_perturbation import source_patterns,perturb
OUT=ROOT/'iteration87'

def query_rows(public, labels):
    rows=ag.public_features(public)
    for r,old in zip(rows,labels):
        assert (r['sid'],r['index'])==(old['sid'],old['index'])
        r['labels']=old['labels'];r['masked_center']=r['features']
    return rows

def transitions(rows,baseline,threshold):
    result=Counter()
    for r,b in zip(rows,baseline):
        p=r['scores']['pooled_pos']['pp']>=threshold;q=b['scores']['pooled_pos']['pp']>=threshold;gold=r['labels']['pp']
        if p and not q:result['new_tp' if gold else 'new_fp']+=1
        if q and not p:result['lost_tp' if gold else 'removed_fp']+=1
    return {k:result[k] for k in ('new_tp','new_fp','lost_tp','removed_fp')}

def run():
    assert not OUT.exists();OUT.mkdir()
    data=load(ROOT/'iteration44/annotations-truth.json');part=load(ROOT/'iteration49/manifest.json')['partitions']['0'];source=lambda split:[dict(sent_id=sid,**data[sid]) for sid in part[split]]
    catalogue=load(ROOT/'iteration85/anchor-budgets.json');patterns=source_patterns(source('fit'),catalogue['20']);save(OUT/'patterns.json',patterns)
    (OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),Path('src/voynich_smt/anchor_perturbation.py'),ROOT/'iteration44/annotations-truth.json',ROOT/'iteration49/manifest.json',CACHE,DECLARATION,ROOT/'iteration85/anchor-budgets.json',OUT/'patterns.json',ROOT/'iteration86/verification-manifest.json']
    for b in SETTINGS:paths += [ROOT/('iteration85/budget-'+b)/n for n in ('models.json','policies.json')]
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='Six predeclared patterns selected only from source-fit frequency in common20 anchors: correct, missing top1/top5/topADP, swap top2ADPs, swap topADP/topCCONJ. Type-consistent transformations preserve opaque IDs. Both20/195 frozen85 models and .81/.80 policies; no retraining/recalibration. All source-test tokens plus cached86 Jerome/Caesar100 each; no reserve/new annotations. Report every arm, changes relative correct, fixed nearestleft F1 control. Diagnostic robustness, not discovery of anchors or exact attachments.'))
    datasets={'source':source('test')};cache=load(CACHE);decl=load(DECLARATION)['split_ids']
    datasets.update({a:cached_sentences(cache,decl[a]) for a in AUTHORS});summary={}
    for name,sentences in datasets.items():
        for budget,kind in SETTINGS.items():
            base=ROOT/('iteration85/budget-'+budget);models=load(base/'models.json');pol=load(base/'policies.json');public,labels=transfer_rows(sentences,catalogue[budget],'stress87-'+name,models['pos_classes']);baseline=None
            for pattern,replacements in patterns.items():
                folder=OUT/(name.lower()+'-'+budget+'-'+pattern);folder.mkdir();changed=perturb(public,replacements,catalogue[budget]);rows=infer85(query_rows(changed,labels),models)
                if pattern=='correct':baseline=rows
                save(folder/'public.json',changed);save(folder/'predictions.json',rows);save(folder/'prediction-freeze.json',dict(inputs={str(p):digest(p) for p in (folder/'public.json',folder/'predictions.json')}))
                result=eval_transfer(rows,pol,kind);result['transitions']=transitions(rows,baseline,result['threshold']);result['changed_anchor_tokens']=sum(x!=y for s,t in zip(public,changed) for x,y in zip(s['tokens'],t['tokens']));save(folder/'evaluation.json',result);summary[name+'/'+budget+'/'+pattern]=result
            print(name,budget,'complete',flush=True)
    save(OUT/'evaluation.json',summary)
if __name__=='__main__':run()
