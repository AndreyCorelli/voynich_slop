"""Calibrate single-anchor-deletion stability before frozen transfer evaluation."""
from benchmarks.grammar_anchor_perturbation_iteration87 import *
from voynich_smt.anchor_stability import SLACKS,stable_scores,select_slack
OUT=ROOT/'iteration88'

def stability_predictions(public,labels,anchors,models,uncertain):
    rows=infer85(query_rows(public,labels),models);hidden=[]
    for word in uncertain:
        changed=perturb(public,{word:None},anchors)
        hidden.append([r['scores']['pooled_pos']['pp'] for r in infer85(query_rows(changed,labels),models)])
    return rows,hidden

def apply(rows,hidden,threshold,slack):
    scores=stable_scores([r['scores']['pooled_pos']['pp'] for r in rows],hidden,threshold,slack)
    return [dict(r,scores=dict(r['scores'],pooled_pos={'pp':float(p)})) for r,p in zip(rows,scores)]

def evaluate(rows,hidden,threshold,slack,pol):
    selected=apply(rows,hidden,threshold,slack)
    return dict(selected=counts(selected,'pp','pooled_pos',threshold),baseline=counts(rows,'pp','pooled_pos',threshold),transitions=transitions(selected,rows,threshold),nearest_f1=counts(rows,'pp','left',pol['left']['standard']['f1']['threshold']))

def run():
    assert not OUT.exists();OUT.mkdir()
    data=load(ROOT/'iteration44/annotations-truth.json');part=load(ROOT/'iteration49/manifest.json')['partitions']['0'];source=lambda split:[dict(sent_id=sid,**data[sid]) for sid in part[split]]
    catalogue=load(ROOT/'iteration85/anchor-budgets.json');patterns=load(ROOT/'iteration87/patterns.json');uncertain=list(patterns['missing_top5']);save(OUT/'patterns.json',patterns)
    (OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),Path('src/voynich_smt/anchor_stability.py'),Path('src/voynich_smt/anchor_perturbation.py'),ROOT/'iteration44/annotations-truth.json',ROOT/'iteration49/manifest.json',CACHE,DECLARATION,ROOT/'iteration85/anchor-budgets.json',ROOT/'iteration87/verification-manifest.json',OUT/'patterns.json']
    for b in SETTINGS:paths += [ROOT/('iteration85/budget-'+b)/n for n in ('models.json','policies.json')]
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='Uncertain types = source-fit top5 common anchors from87. On each clean/corrupted public input hide each displayed anchor identity individually, preserving true opaque IDs; recompute all contextual/type-pooled scores. Retain baseline-selected PP only if minimum deletion score >= frozen85 threshold minus slack. Grid0,.05,.1,.2,.4,1 (1=baseline). Source calibration selects maximum worst-pattern precision, ties summedTP thenlargerslack; require cleanTP>=halfbaseline,cleanprecision>=.90,20cleanpredictions,10perpattern. Otherwise baselinefallback. No guarantee of90robustprecision. Freeze BOTH policies before any source-test/author prediction. All six87patterns reported including controls; known development stress patterns, no unseen-error generalization claim. No refit, new annotation, reserve or sealed test.'))
    policies={}
    for budget,kind in SETTINGS.items():
        base=ROOT/('iteration85/budget-'+budget);models=load(base/'models.json');pol=load(base/'policies.json');public,labels=transfer_rows(source('calibration'),catalogue[budget],'cal88',models['pos_classes']);threshold=.81 if budget=='20' else .8;curve={str(s):{} for s in SLACKS}
        for pattern,replacements in patterns.items():
            folder=OUT/('calibration-'+budget+'-'+pattern);folder.mkdir();changed=perturb(public,replacements,catalogue[budget]);rows,hidden=stability_predictions(changed,labels,catalogue[budget],models,uncertain);save(folder/'scores.json',dict(rows=rows,hidden=hidden));save(folder/'prediction-freeze.json',dict(inputs={str(folder/'scores.json'):digest(folder/'scores.json')}))
            for slack in SLACKS:curve[str(slack)][pattern]=counts(apply(rows,hidden,threshold,slack),'pp','pooled_pos',threshold)
        policies[budget]=select_slack(curve);save(OUT/('calibration-curve-'+budget+'.json'),curve);print('calibrated',budget,policies[budget],flush=True)
    save(OUT/'policies.json',policies);save(OUT/'policy-freeze.json',dict(inputs={str(p):digest(p) for p in [OUT/'policies.json']+list(OUT.glob('calibration-curve-*.json'))}))
    datasets={'source':source('test')};cache=load(CACHE);decl=load(DECLARATION)['split_ids'];datasets.update({a:cached_sentences(cache,decl[a]) for a in AUTHORS});summary={}
    for name,sentences in datasets.items():
        for budget,kind in SETTINGS.items():
            base=ROOT/('iteration85/budget-'+budget);models=load(base/'models.json');pol=load(base/'policies.json');public,labels=transfer_rows(sentences,catalogue[budget],'eval88-'+name,models['pos_classes']);threshold=.81 if budget=='20' else .8
            for pattern,replacements in patterns.items():
                folder=OUT/(name.lower()+'-'+budget+'-'+pattern);folder.mkdir();changed=perturb(public,replacements,catalogue[budget]);rows,hidden=stability_predictions(changed,labels,catalogue[budget],models,uncertain);save(folder/'scores.json',dict(rows=rows,hidden=hidden));save(folder/'prediction-freeze.json',dict(inputs={str(folder/'scores.json'):digest(folder/'scores.json')}));result=evaluate(rows,hidden,threshold,policies[budget]['slack'],pol);save(folder/'evaluation.json',result);summary[name+'/'+budget+'/'+pattern]=result
            print('evaluated',name,budget,flush=True)
    save(OUT/'evaluation.json',summary)
if __name__=='__main__':run()
