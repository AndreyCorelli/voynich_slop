"""Fixed small nonlinear models on the unchanged decoder-confusion samples."""
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import time
from benchmarks.grammar_decoder_confusions_iteration12 import OUT as TWELVE,TEN,NINE,SEVEN,pair_rows,evaluate_scores,GATE
from benchmarks.grammar_structure_iteration3_validate import FrozenAdapter
from benchmarks.grammar_nonlinear_contrasts_iteration13_reserve import RESERVATION
from voynich_smt.shallow_boosting import ShallowBoostedClassifier
from voynich_smt.predicate_structure import Logistic
from voynich_smt.data.corpus import write_json,digest

OUT=Path('experiments/results/grammar-restoration/iteration13-v2')


def nonlinear_screen(evaluations):
    rich=evaluations['nonlinear_rich'];distance=evaluations['nonlinear_distance']
    ge=lambda a,b:a+1e-12>=b
    checks={'matched_sample':rich['matched_preference']['pairs']>=GATE['minimum_matched_pairs'],
        'same_child_sample':rich['same_child_preference']['pairs']>=GATE['minimum_same_child'],
        'matched_auc':ge(rich['matched_auc'],GATE['matched_auc']),
        'matched_auc_gain':ge(rich['matched_auc']-distance['matched_auc'],GATE['matched_auc_gain_over_distance']),
        'matched_preference':ge(rich['matched_preference']['accuracy'],GATE['matched_preference']),
        'matched_preference_gain':ge(rich['matched_preference']['accuracy']-distance['matched_preference']['accuracy'],GATE['matched_preference_gain_over_distance']),
        'same_child_preference':ge(rich['same_child_preference']['accuracy'],GATE['same_child_preference']),
        'same_child_gain':ge(rich['same_child_preference']['accuracy']-distance['same_child_preference']['accuracy'],GATE['same_child_gain_over_distance'])}
    return {'passed':all(checks.values()),'checks':checks,'scope':'diagnostic screen on reused development; never automatic score composition'}


def observations():
    load=lambda p:json.loads(p.read_text());samples=load(TWELVE/'samples.json')
    train=load(NINE/'train-truth.json');dev=load(NINE/'development-truth.json')
    source_predictions=load(TWELVE/'source-crossfit-predictions.json');old=load(TEN/'predictions.json')
    dev_predictions=[next(r['prediction'] for r in old if (r['stream'],r['training'],r['features'],r['markers'],r['condition'])==(i,'oof','interactions','predicted','unrestricted')) for i in range(len(dev))]
    adapter=FrozenAdapter(load(SEVEN/'morphology-lattice.json'))
    return samples,train,dev,source_predictions,dev_predictions,adapter


def run():
    if OUT.exists():raise ValueError('Preserve previous output')
    start=time.monotonic();load=lambda p:json.loads(p.read_text())
    samples,train,dev,source_predictions,dev_predictions,adapter=observations()
    if not RESERVATION.exists():raise ValueError('Reserve validation sentence IDs first')
    inputs=[TWELVE/n for n in ['samples.json','source-crossfit-predictions.json','models.json','predictions.json','report.json','validation.json']]
    inputs += [NINE/'train-truth.json',NINE/'development-truth.json',TEN/'predictions.json',SEVEN/'morphology-lattice.json',RESERVATION]
    manifest={'scope':'fixed-source nonlinear capacity diagnostic on reused development; no score composition or reserved-holdout evaluation',
        'reference_version':'predicate-complex-v1','source_matched_pairs':131,'development_matched_pairs':40,'development_same_child':20,
        'model':'five jointly searched depth-two Newton-boosted trees; min leaf 20, leaf L2 10, shrinkage .2, update clipping 1',
        'settings':'fixed before fit; no development selection','input_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},
        'code_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),Path('src/voynich_smt/shallow_boosting.py')]}}
    write_json(OUT/'manifest.json',manifest)
    models={};old=load(TWELVE/'models.json');fitting={};evaluations={};predictions={}
    for suffix,rich in [('distance',False),('rich',True)]:
        records=[r for m in samples['source']['matched']['matches'] for r in [m['positive'],m['negative']]]
        x=pair_rows(records,train,source_predictions,adapter,rich);y=[v for _ in samples['source']['matched']['matches'] for v in [1,0]]
        model=ShallowBoostedClassifier.fit(x,y)
        models['nonlinear_'+suffix]=model;models['hard_'+suffix]=Logistic(**old['hard_'+suffix])
        write_json(OUT/('nonlinear-'+suffix+'-model.json'),asdict(model))
    for name,model in models.items():
        rich=name.endswith('rich')
        positive=model.logits(pair_rows(samples['development']['positives'],dev,dev_predictions,adapter,rich)).tolist()
        negative=model.logits(pair_rows(samples['development']['negatives'],dev,dev_predictions,adapter,rich)).tolist()
        predictions[name]={'positive_logits':positive,'negative_logits':negative}
        evaluations[name]=evaluate_scores(samples['development'],positive,negative)
        p=model.logits(pair_rows(samples['source']['positives'],train,source_predictions,adapter,rich)).tolist()
        n=model.logits(pair_rows(samples['source']['negatives'],train,source_predictions,adapter,rich)).tolist()
        fitting[name]=evaluate_scores(samples['source'],p,n)
        print(name,'fit preference',round(fitting[name]['matched_preference']['accuracy'],3),
            'development AUC',round(evaluations[name]['matched_auc'],3),'matched preference',round(evaluations[name]['matched_preference']['accuracy'],3),
            'same-child',round(evaluations[name]['same_child_preference']['accuracy'],3),flush=True)
    decision=nonlinear_screen(evaluations)
    write_json(OUT/'predictions.json',predictions)
    report={'manifest_sha256':digest(manifest),'evaluations':evaluations,'source_fitting_only':fitting,'nonlinear_screen':decision,
        'nonlinear_models_fit':2,'linear_controls_frozen':True,'elapsed_seconds':time.monotonic()-start,
        'decision':'capacity diagnostic and construction audit only; no decoder/holdout/confirmation/target evaluation'}
    write_json(OUT/'report.json',report);print('Nonlinear diagnostic screen',decision,flush=True)


if __name__=='__main__':run()
