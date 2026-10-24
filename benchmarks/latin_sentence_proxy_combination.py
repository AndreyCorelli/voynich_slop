"""Weighted grammar-discrimination benchmark, with source and corruption holdouts."""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
from types import SimpleNamespace
import numpy as np
from benchmarks.latin_sentence_proxy_cases import OUT
from benchmarks.word_mapping_neural_model import DEFAULT_MODEL,file_hashes
from benchmarks import word_mapping_anchor_recovery as resource
from voynich_smt.data.corpus import digest,write_json
from voynich_smt.word_mapping.corpora import WordStream
from voynich_smt.word_mapping.ngram import NgramModel,NgramConfig
from voynich_smt.structural_language import StructuralLanguageModel
from voynich_smt.neural_scoring import WholeWordScorer
from voynich_smt.bootstrap_mapping import AgreementModel
from voynich_smt.bootstrap_marginal import MarginalAgreementModel
from voynich_smt.proxy_combination import fit_linear,threshold,evaluate,grouped_intervals

FEATURES=['neural_mean_piece','neural_piece_sum','word_unigram','word_bigram','word_trigram','morphological_sequence','adjacent_agreement','marginal_agreement','morphology_coverage']
REGULARIZATIONS=(.001,.01,.1,1.,10.)

def run(validate=False,resume=False):
    cases=json.loads((OUT/'cases.json').read_text());dataset=json.loads((OUT/'dataset-manifest.json').read_text())
    assert digest(dataset['protocol'])==dataset['sha256'] and digest(cases)==dataset['protocol']['cases_sha256']
    assert hashlib.sha256((OUT/'morphology.json').read_bytes()).hexdigest()==dataset['protocol']['morphology_sha256']
    entries=json.loads((OUT/'morphology.json').read_text())['entries']
    train=list(WordStream.load(resource.PARENT/'splits/train.json').segments())
    asset=json.loads((DEFAULT_MODEL/'manifest.json').read_text());assert file_hashes(DEFAULT_MODEL)==asset['protocol']['files_sha256']
    paths=[Path(__file__),Path('src/voynich_smt/proxy_combination.py'),Path('src/voynich_smt/neural_scoring.py'),Path('src/voynich_smt/structural_language.py'),Path('src/voynich_smt/bootstrap_mapping.py'),Path('src/voynich_smt/bootstrap_marginal.py'),Path('src/voynich_smt/word_mapping/ngram.py')]
    protocol={'dataset_sha256':dataset['sha256'],'model_sha256':asset['sha256'],'training_segments_sha256':digest(train),'features':FEATURES,
        'regularizations':REGULARIZATIONS,'seed':1207,'nonnegative_and_signed_combinations':True,
        'selection':'fit-only normalization and logistic weights; calibration-only regularization, threshold and best-single selection; model frozen before test scoring',
        'reliability_gate':{'balanced_accuracy':.95,'paired_accuracy':.95,'minimum_family_accuracy':.90,'minimum_control_acceptance':.95,'minimum_bootstrap_lower':.90},
        'scope':'automatic dependency corruption labels; no gold heads/POS in score inputs; source-disjoint test; no guarantee of no alternate parse or universal grammaticality',
        'code_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
    manifest={'protocol':protocol,'sha256':digest(protocol)}
    if (OUT/'scoring-manifest.json').exists():
        if not (validate or resume) or json.loads((OUT/'scoring-manifest.json').read_text())!=json.loads(json.dumps(manifest)):raise ValueError('Existing or changed scoring protocol')
    else:write_json(OUT/'scoring-manifest.json',manifest)
    scorer=WholeWordScorer.load(DEFAULT_MODEL/'inference',batch_size=16,threads=4)
    bigram=NgramModel.train(train,NgramConfig(bigram_weight=1.,trigram_weight=0.))
    trigram=NgramModel.train(train,NgramConfig(bigram_weight=0.,trigram_weight=1.))
    structural=StructuralLanguageModel(entries).fit(train)
    morphology=SimpleNamespace(entries=entries,identity=digest(dataset['protocol']['morphology_sha256']))
    agreement=AgreementModel(morphology);marginal=MarginalAgreementModel(morphology)
    counts=Counter(w for s in train for w in s);total=sum(counts.values());vocab=len(counts)+1
    cache={};feature_rows=[]
    def score(row):
        key=tuple(row['words'])
        if key not in cache:
            result=scorer.segment(key).totals();n=len(key)
            cache[key]=[result['word_normalized_log_sum']/n,result['word_masked_log_sum']/n,
                sum(math.log((counts[w]+.1)/(total+.1*vocab)) for w in key)/n,
                bigram.score([key]).log_likelihood/n,trigram.score([key]).log_likelihood/n,structural.score([key])/n,
                agreement.score([key])/max(1,n-1),marginal.score([key])/max(1,n-1),sum(bool(entries.get(w)) for w in key)/n]
        return cache[key]
    def get_split(split):
        rows=[r for r in cases if r['split']==split];path=OUT/f'features-{split}.json'
        if resume and path.exists() and not validate:
            saved=json.loads(path.read_text());assert [r['id'] for r in saved]==[r['id'] for r in rows]
            feature_rows.extend(saved);return rows,np.asarray([r['features'] for r in saved])
        features=[]
        for i,row in enumerate(rows,1):
            values=score(row);features.append({'id':row['id'],'features':values})
            if i%25==0:print('scored',split,i,'/',len(rows),flush=True)
        if validate:
            saved=json.loads(path.read_text());assert [r['id'] for r in saved]==[r['id'] for r in features]
            assert np.allclose([r['features'] for r in saved],[r['features'] for r in features],atol=1e-6,rtol=0)
        else:write_json(path,features)
        feature_rows.extend(features);return rows,np.asarray([r['features'] for r in features])
    fit,fx=get_split('fit');calibration,cx=get_split('calibration')
    mean=fx.mean(0);scale=fx.std(0);scale[scale<1e-10]=1
    x=(fx-mean)/scale;v=(cx-mean)/scale
    y=np.asarray([r['valid'] for r in fit],dtype=int);vy=np.asarray([r['valid'] for r in calibration],dtype=int)
    candidates=[]
    for nonnegative in (True,False):
        trials=[]
        for regularization in REGULARIZATIONS:
            parameters=fit_linear(x,y,regularization,nonnegative)
            scores=v@parameters[:-1]+parameters[-1];cutoff=threshold(scores,vy);metrics=evaluate(calibration,scores,cutoff)
            trials.append({'regularization':regularization,'parameters':parameters.tolist(),'threshold':cutoff,'calibration':metrics})
        best=max(trials,key=lambda r:(r['calibration']['balanced_accuracy'],r['calibration']['paired_accuracy'],-sum(abs(w) for w in r['parameters'][:-1])))
        candidates.append({'name':'nonnegative_combination' if nonnegative else 'signed_combination',**best,'trials':trials})
    singles=[]
    for i,feature in enumerate(FEATURES):
        parameters=np.zeros(len(FEATURES)+1);parameters[i]=1.;scores=v[:,i];cutoff=threshold(scores,vy)
        singles.append({'name':feature,'parameters':parameters.tolist(),'threshold':cutoff,'calibration':evaluate(calibration,scores,cutoff)})
    best_single=max(singles,key=lambda r:(r['calibration']['balanced_accuracy'],r['calibration']['paired_accuracy']))
    selection={'manifest_sha256':manifest['sha256'],'mean':mean.tolist(),'scale':scale.tolist(),'candidates':candidates,'single_proxies':singles,'best_single':best_single['name'],
        'fit_ids_sha256':digest([r['id'] for r in fit]),'calibration_ids_sha256':digest([r['id'] for r in calibration])}
    if validate:assert json.loads((OUT/'selection.json').read_text())==selection
    elif resume and (OUT/'selection.json').exists():assert json.loads((OUT/'selection.json').read_text())==selection
    else:write_json(OUT/'selection.json',selection)
    print('Selection frozen before test scoring:',[(c['name'],c['calibration']['balanced_accuracy']) for c in candidates],best_single['name'],flush=True)
    test,tx=get_split('test');z=(tx-mean)/scale
    results=[];fit_lemmas={r.get('lemma') for r in fit if not r['valid']}
    for selected in candidates+singles:
        parameters=np.asarray(selected['parameters']);scores=z@parameters[:-1]+parameters[-1];cutoff=selected['threshold']
        metrics=evaluate(test,scores,cutoff);intervals=grouped_intervals(test,scores,cutoff)
        family_min=min(r['accuracy'] for r in metrics['families'].values());controls=[r['accuracy'] for k,r in metrics['families'].items() if k.endswith('_control')]
        reliable=metrics['balanced_accuracy']>=.95 and metrics['paired_accuracy']>=.95 and family_min>=.9 and min(controls)>=.95 and intervals['balanced_accuracy'][0]>=.9 and intervals['paired_accuracy'][0]>=.9
        novel_pairs=[(r,float(score)) for r,score in zip(test,scores) if not r['valid'] and r.get('lemma') not in fit_lemmas]
        originals={r['base']:float(score) for r,score in zip(test,scores) if r['family']=='original'}
        results.append({'name':selected['name'],'test':metrics,'confidence_95_sentence_cluster_bootstrap':intervals,'reliable_on_preregistered_gate':reliable,
            'unseen_edited_lemma_pairs':len(novel_pairs),'unseen_edited_lemma_paired_accuracy':float(np.mean([originals[r['base']]>s+1e-10 for r,s in novel_pairs])),
            'predictions':[{'id':r['id'],'score':float(s),'predicted_valid':bool(s>=cutoff)} for r,s in zip(test,scores)]})
    report={'manifest_sha256':manifest['sha256'],'selection_sha256':digest(selection),'feature_rows_sha256':digest(feature_rows),
        'split_counts':dict(Counter(r['split'] for r in cases)),'base_sentences':len({r['base'] for r in cases}),
        'results':results,'conclusion':'No reliability established' if not any(r['reliable_on_preregistered_gate'] for r in results[:2]) else 'Controlled benchmark gate passed; unrestricted grammaticality still unestablished'}
    if validate:
        saved=json.loads((OUT/'report.json').read_text())
        # Tiny public-forward floating variation is handled in raw feature replay;
        # ranking/selection and downstream report must still match exactly.
        assert saved==report;write_json(OUT/'validation.json',{'all_features_and_report_replayed':True,'tolerance':1e-6,'report_sha256':digest(report)})
    else:write_json(OUT/'report.json',report)
    print('RESULT',report['conclusion'],flush=True)
    for result in results:
        print(result['name'],result['test']['balanced_accuracy'],result['test']['paired_accuracy'],result['test']['families'],flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--validate',action='store_true');p.add_argument('--resume',action='store_true');a=p.parse_args();run(a.validate,a.resume)
