"""Source-selected abstention and fixed top-k controls for grammatical class seeds."""
from benchmarks.grammar_context_overlap_iteration135 import *
OUT=ROOT/'iteration140'

def assess(rows,anchors):
    correct=sum((r['probability']>.5)==(anchors[r['type']]=='CCONJ') for r in rows)
    return dict(selected=len(rows),correct=correct,wrong=len(rows)-correct,accuracy=correct/len(rows) if rows else None,predicted_classes=dict(Counter('CCONJ' if r['probability']>.5 else 'ADP' for r in rows)))

def candidates(rows):
    return [dict(type=r['type'],n=r['n'],probability=r['probabilities']['new'],confidence=max(r['probabilities']['new'],1-r['probabilities']['new'])) for r in rows if r['n']>=5]

def top_with_ties(rows,k):
    if len(rows)<=k:return rows
    cut=sorted((r['confidence'] for r in rows),reverse=True)[k-1]
    return [r for r in rows if r['confidence']>=cut]

def run():
    assert not OUT.exists();OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),ROOT/'iteration135/oof-probabilities.json',ROOT/'iteration135/training-statistics.json',ROOT/'iteration135/calibrators.json',ROOT/'iteration116/type-split.json',ROOT/'iteration85/anchor-budgets.json',ROOT/'iteration137/predictions.json',ROOT/'iteration138/predictions.json',ROOT/'iteration139/common-core.json',ROOT/'iteration139/verification-manifest.json']
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='Selectivegrammaticalclassseed diagnostic, NOTexactlexicalnuclei. Frozen135PRIMARYcorrectedonly, no fitting/classcutchange. Sourcepolicyfrom13type-heldoutOOF probabilities+samebalancedoffset fiton13(disclosedcalibration/selectionreuse, tinyclasspool). Requireocc>=5, confidence=max(q,1-q); gridallattainedsourceconfidences+.5+1 inclusive>=. Sourcequalify>=3selected ANDselectedreferenceaccuracy>=.90, maximizecorrect,minwrong,highestcut;OFFifnone. Freezechosenpolicy BEFOREloading4targetpredictions. Exact137sentencefreeexpandedCaesar/Jerome,138originalGellius/Livy; allpresenteligibletypes fixed. PrimarypassrequiresEACHtext>=3selectedAND>=90%agreement, notaveragepool. SecondaryPREDECLAREDtop3/top5 highestconfidence withALLboundaryties included, no authorcutoffs; notfallbackpolicy. Reportallpresentandcommon14(139presence-defined) metrics, selectedtypes/errors/counts; rawcambiguity flagged ifselected, neverrelabeled/droppedprimary. Rejectany inferenceoflexicalidentity fromsourceknownwordlabels. No model/PP/newannotations/reserve/sealedworks/defaultchange; reuseddevelopment, empirical3typesNOTconfidenceguarantee.'))
    anchors=load(ROOT/'iteration85/anchor-budgets.json')['195'];train=load(ROOT/'iteration116/type-split.json')['training'];oof=load(ROOT/'iteration135/oof-probabilities.json')['corrected'];cal=load(ROOT/'iteration135/calibrators.json')['corrected'];stats=load(ROOT/'iteration135/training-statistics.json');source=[]
    for w in train:
        q=float(apply_offset([oof[w]],cal)[0]);n=stats[hashlib.sha256(('fit116|'+w).encode()).hexdigest()]['n']
        if n>=5:source.append(dict(type=w,n=n,probability=q,confidence=max(q,1-q)))
    cuts=sorted({.5,1.}|{r['confidence'] for r in source});curve=[]
    for cut in cuts:
        rr=[r for r in source if r['confidence']>=cut];m=assess(rr,anchors);curve.append(dict(threshold=cut,metrics=m,qualified=m['selected']>=3 and 10*m['correct']>=9*m['selected'],selected_types=[r['type'] for r in rr]))
    good=[r for r in curve if r['qualified']];chosen=max(good,key=lambda r:(r['metrics']['correct'],-r['metrics']['wrong'],r['threshold'])) if good else dict(threshold=None,qualified=False);save(OUT/'source-candidates.json',source);save(OUT/'source-curve.json',curve);save(OUT/'chosen.json',chosen);save(OUT/'policy-freeze.json',dict(inputs={str(OUT/n):digest(OUT/n) for n in ['source-candidates.json','source-curve.json','chosen.json']}));print('CHOSEN',chosen,flush=True)
    previous=load(ROOT/'iteration137/predictions.json');raw=load(ROOT/'iteration138/predictions.json');inputs={'Caesar':previous['Caesar-expanded']['concat']['corrected'],'Jerome':previous['Jerome-expanded']['concat']['corrected'],**{w:raw[w]['original']['corrected'] for w in ['gellius-1','livy-1']}};core=set(load(ROOT/'iteration139/common-core.json'));selections={}
    for work,rows in inputs.items():
        cc=candidates(rows);selected=[r for r in cc if r['confidence']>=chosen['threshold']] if chosen['qualified'] else [];selections[work]=dict(eligible=cc,primary=selected,top3=top_with_ties(cc,3),top5=top_with_ties(cc,5))
    save(OUT/'selections.json',selections);save(OUT/'selection-freeze.json',dict(inputs={str(OUT/'selections.json'):digest(OUT/'selections.json')}));evaluation={}
    for work,arms in selections.items():
        evaluation[work]={arm:dict(all=assess(rr,anchors),common14=assess([r for r in rr if r['type'] in core],anchors),selected_types=[r['type'] for r in rr],wrong_types=[r['type'] for r in rr if (r['probability']>.5)!=(anchors[r['type']]=='CCONJ')],raw_c_reference_ambiguity_present=work=='gellius-1' and any(r['type']=='c' for r in rr)) for arm,rr in arms.items()};print('RESULT',work,evaluation[work],flush=True)
    passed=chosen['qualified'] and all(v['primary']['all']['selected']>=3 and v['primary']['all']['accuracy']>=.9 for v in evaluation.values());save(OUT/'evaluation.json',evaluation);save(OUT/'result.json',dict(source_qualified=chosen['qualified'],all_four_texts_passed=passed,no_lexical_nuclei_or_default_change=True))
if __name__=='__main__':run()
