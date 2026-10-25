"""All seven focal-occurrence substitutions, keeping source length fixed."""
from benchmarks.grammar_training_sensitivity_iteration148 import *
OUT=ROOT/'iteration150'

def run():
    assert not OUT.exists();OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),ROOT/'iteration149/selection.json',ROOT/'iteration149/verification-manifest.json',ROOT/'iteration149/models.json',ROOT/'iteration149/predictions.json',ROOT/'iteration142/models.json',ROOT/'iteration144/features.json',ROOT/'iteration144/predictions.json',ROOT/'iteration116/type-split.json',ROOT/'iteration44/annotations-truth.json',ROOT/'iteration49/manifest.json',ROOT/'iteration85/anchor-budgets.json',Path('src/voynich_smt/opaque_context_overlap.py'),Path('src/voynich_smt/opaque_context_roles.py')]
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='All7nonempty subsets of three siue positions in source sentence76252 index590 tokens35,37,39, replace each selected occurrence with its own distinct fresh SHA opaqueID; every other token/order/source length unchanged. No sentence deletion/seam. Freeze transforms before features. Original13 types/labels, both scalar features recomputed, same142classbalancedL2/retained standardization/raw>.5 no calibration/tuning/authorselection. Full reference and149whole-sentence-deletion reference, refit full must match142. Freeze allmodels before7targetpredictions, allpredictions beforemodalmetrics. Allpresentcandidate metrics accuracy,NLL,AUC/pairedflips/meanmaxprobchanges. Compare all7subsets, no favorable model selection. Diagnostic onalreadyinspectedstreams; no reserve/sealedworks/newannotations/nuclei/confidencegate. ArtificialIDs unique, not labeled or added training types; changes intentionally remove equality links and reduce siue count, not semantic substitutions.'))
    public,lookup,anchors,split,words,allowed=training_inputs();train=split['training'];wanted={lookup[w] for w in train};ids=[t['id'] for s in public for t in s['tokens']];j=590;assert public[j]['sent_id']=='76252';offset=sum(len(s['tokens']) for s in public[:j]);positions=[offset+k for k in [35,37,39]];assert all(ids[p]==lookup['siue'] for p in positions);fresh=[hashlib.sha256(f'motif150|{p}'.encode()).hexdigest() for p in positions];assert not set(fresh)&set(ids);transforms={str(mask):[positions[k] for k in range(3) if mask&(1<<k)] for mask in range(1,8)};save(OUT/'selection.json',dict(positions=positions,fresh=fresh,transforms=transforms));save(OUT/'selection-freeze.json',dict(inputs={str(OUT/'selection.json'):digest(OUT/'selection.json')}));features={};models={}
    for name,selected in [('full',[])]+list(transforms.items()):
        seq=list(ids)
        for pos in selected:seq[pos]=fresh[positions.index(pos)]
        f=features_for(seq,wanted);features[name]=f;models[name]=fit_vector(f,train,lookup,anchors,COLS)
    baseline=load(ROOT/'iteration142/models.json')['joint']['final'];assert np.allclose(models['full']['weights'],baseline['weights'],atol=1e-6);models['full']=baseline;models['sentence_deleted']=load(ROOT/'iteration149/models.json')['delete590']
    for n,x in [('features',features),('models',models)]:save(OUT/(n+'.json'),x)
    save(OUT/'model-freeze.json',dict(inputs={str(OUT/(n+'.json')):digest(OUT/(n+'.json')) for n in ['features','models']}));cached=load(ROOT/'iteration144/features.json');old=load(ROOT/'iteration144/predictions.json');pred={}
    for key,configs in old.items():
        if not key.endswith('/full'):continue
        w=key[:-5];pred[w]={name:[dict(r,probabilities=dict(raw=predict_vector(cached[key][r['opaque']],m))) for r in configs['joint']] for name,m in models.items()};assert pred[w]['full']==configs['joint'];assert pred[w]['sentence_deleted']==load(ROOT/'iteration149/predictions.json')[w]['delete590']
    save(OUT/'predictions.json',pred);save(OUT/'predictions-freeze.json',dict(inputs={str(OUT/'predictions.json'):digest(OUT/'predictions.json')}));summary=evaluate(pred,anchors,{name:'opaque_substitution' for name in models});save(OUT/'summary.json',summary)
    for w,r in summary.items():print(w,{n:(x['metrics']['correct'],len(x['decision_flips'])) for n,x in r.items()},flush=True)
if __name__=='__main__':run()
