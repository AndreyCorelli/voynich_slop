"""Fit frozen passage feature differences; compare structural and full rankings."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from benchmarks.latin_passage_proxy_audit import OUT as PARENT
from benchmarks.latin_sentence_proxy_combination import FEATURES,REGULARIZATIONS
from voynich_smt.data.corpus import digest,write_json
from voynich_smt.relative_ranking import fit_ranker,pair_weights
OUT=Path('experiments/results/latin-relative-ranking')
NAMES=FEATURES+['low_tail_'+f for f in FEATURES]+['sentence_acceptance_rate']
STRUCTURAL=[5,6,7,8,14,15,16,17]


def pairs_from(rows):
    lookup={r['id']:r for r in rows};pairs=[]
    for bad in rows:
        if not bad['family'].startswith('corrupt_'):continue
        for kind,family in [('original','original'),('grammatical_control',bad['family'].replace('corrupt_','control_'))]:
            good=lookup.get(bad['base']+'/'+family)
            if good is None:continue
            pairs.append({'id':bad['id']+'/'+kind,'document':bad['document'],'split':bad['split'],'width':bad['width'],'kind':kind,'tier':bad['family'],'good':good['id'],'bad':bad['id'],'difference':(np.asarray(good['features'])-np.asarray(bad['features'])).tolist(),'changed_good':good['changed_tokens'],'changed_bad':bad['changed_tokens']})
    return pairs


def metrics(pairs,margins):
    margins=np.asarray(margins);weights=pair_weights(pairs);correct=margins>1e-10
    controls=np.asarray([p['kind']=='grammatical_control' for p in pairs]);cw=weights[controls]
    return {'pairs':len(pairs),'correct':int(correct.sum()),'accuracy':float(correct.mean()),'work_width_kind_balanced_accuracy':float(np.average(correct,weights=weights)),
        'control_work_width_balanced_accuracy':float(np.average(correct[controls],weights=cw)),
        'weighted_logistic_loss':float(np.average(np.logaddexp(0,-margins),weights=weights)),
        'ties':int(np.sum(np.abs(margins)<=1e-10))}


def run(validate=False):
    sources=[PARENT/'passages.json',PARENT/'manifest.json',PARENT/'selection.json',PARENT/'validation.json']
    rows=json.loads(sources[0].read_text());pairs=pairs_from(rows)
    protocol={'source_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},'code_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),Path('src/voynich_smt/relative_ranking.py')]},
        'features':NAMES,'structural_indices':STRUCTURAL,'ridge_grid':REGULARIZATIONS,'fit':'un-centered pair differences scaled by fit-only weighted RMS; logistic pair loss, zero intercept; work/width/kind-balanced fitting weights','selection':'calibration grammatical-control balanced accuracy first, all-pair balanced accuracy second, logistic loss third; freeze before test evaluation','gate':'at every width >=95% on both original and grammatical-control rankings, every work >=90%; exploratory reused test works and mutations','pairs_sha256':digest(pairs)}
    manifest={'protocol':protocol,'sha256':digest(protocol)}
    if (OUT/'manifest.json').exists():assert validate and json.loads((OUT/'manifest.json').read_text())==json.loads(json.dumps(manifest))
    else:write_json(OUT/'manifest.json',manifest)
    fit=[p for p in pairs if p['split']=='fit'];cal=[p for p in pairs if p['split']=='calibration'];fw=pair_weights(fit)
    x=np.asarray([p['difference'] for p in fit]);scale=np.sqrt(np.average(x*x,axis=0,weights=fw));scale[scale<1e-10]=1;x=x/scale
    cx=np.asarray([p['difference'] for p in cal])/scale;models=[]
    def key(m):
        t=m['calibration'];return (t['control_work_width_balanced_accuracy'],t['work_width_kind_balanced_accuracy'],-t['weighted_logistic_loss'])
    for family,indices in [('all_features',list(range(len(NAMES)))),('structural_features',STRUCTURAL)]:
        for nonnegative in (True,False):
            trials=[]
            for ridge in REGULARIZATIONS:
                w=np.zeros(len(NAMES));w[indices]=fit_ranker(x[:,indices],fw,ridge,nonnegative)
                trials.append({'ridge':ridge,'weights':w.tolist(),'calibration':metrics(cal,cx@w)})
            best=max(trials,key=key);models.append({'name':family+('_nonnegative' if nonnegative else '_signed'),**best,'trials':trials})
    singles=[]
    for i,name in enumerate(NAMES):
        w=np.zeros(len(NAMES));w[i]=1;singles.append({'name':name,'weights':w.tolist(),'calibration':metrics(cal,cx@w)})
    best_single=max(singles,key=key);chosen=max(models,key=key)['name']
    selection={'manifest_sha256':manifest['sha256'],'scale':scale.tolist(),'models':models,'singles':singles,'chosen_model':chosen,'best_single':best_single['name'],'fit_pairs':len(fit),'calibration_pairs':len(cal)}
    if validate:assert json.loads((OUT/'selection.json').read_text())==selection
    else:write_json(OUT/'selection.json',selection)
    print('FROZEN',chosen,'best single',best_single['name'],flush=True)
    test=[p for p in pairs if p['split']=='test'];tx=np.asarray([p['difference'] for p in test])/scale;results=[]
    for model in models+singles:
        w=np.asarray(model['weights']);margins=tx@w;bywidth=[]
        for width in [250,1000,'whole_work']:
            record={'width':width,'kinds':{}}
            for kind in ('original','grammatical_control'):
                idx=[i for i,p in enumerate(test) if p['width']==width and p['kind']==kind];a=margins[idx];correct=a>1e-10
                record['kinds'][kind]={'pairs':len(idx),'correct':int(correct.sum()),'accuracy':float(correct.mean()),'ties':int(np.sum(np.abs(a)<=1e-10)),
                    'by_work':{doc:{'pairs':sum(test[i]['document']==doc for i in idx),'correct':sum(bool(margins[i]>1e-10) for i in idx if test[i]['document']==doc)} for doc in sorted({test[i]['document'] for i in idx})}}
            bywidth.append(record)
        reliable=all(q['accuracy']>=.95 and all(v['correct']/v['pairs']>=.9 for v in q['by_work'].values()) for r in bywidth for q in r['kinds'].values())
        results.append({'name':model['name'],'test':metrics(test,margins),'by_width':bywidth,'gate_passed':reliable,'predictions':[{'pair':p['id'],'good':p['good'],'bad':p['bad'],'margin':float(v),'correct':bool(v>1e-10)} for p,v in zip(test,margins)]})
    report={'manifest_sha256':manifest['sha256'],'selection_sha256':digest(selection),'pairs_sha256':digest(pairs),'results':results,'chosen_model':chosen,'best_single':best_single['name'],'test_pairs':len(test),'scope':'Exploratory reused four test works and existing sparse global mappings; not new independent reliability evidence. No absolute validity threshold or plaintext reference required for candidate scoring.'}
    if validate:
        assert json.loads((OUT/'report.json').read_text())==report;write_json(OUT/'validation.json',{'full_fit_selection_and_test_replayed':True,'report_sha256':digest(report)})
    else:write_json(OUT/'pairs.json',pairs);write_json(OUT/'report.json',report)
    for name in [chosen,best_single['name'],'morphological_sequence','neural_mean_piece']:
        r=next(r for r in results if r['name']==name);print('RESULT',name,[(q['width'],{k:(v['correct'],v['pairs']) for k,v in q['kinds'].items()}) for q in r['by_width']],flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--validate',action='store_true');run(p.parse_args().validate)
