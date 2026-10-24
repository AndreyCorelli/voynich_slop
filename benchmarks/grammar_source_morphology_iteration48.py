"""Morphology retrieved from source-only training/calibration, sentence-held-out."""
from pathlib import Path
from collections import Counter,defaultdict
import hashlib
import numpy as np
from benchmarks.grammar_morphology_stress_iteration47 import OUT as PREVIOUS,ROOT,SOURCE,RESERVE,load,save,digest
from voynich_smt.construction_interventions import readings_key
from voynich_smt.relational_compatibility import sv_lattice
from voynich_smt.morphology_stress import encode,link_summary
from voynich_smt.source_morphology import fit,calibrate,predict,domains,labels,label,group,ARMS
OUT=ROOT/'iteration48'
EXAMPLES=ROOT/'iteration46/sv-lattices.json'


def fold(sid):return int(hashlib.sha256(sid.encode()).hexdigest(),16)%5


def run():
    assert not OUT.exists()
    for p,h in load(PREVIOUS/'verification-manifest.json')['inputs'].items():assert digest(p)==h,p
    data=load(SOURCE);examples=load(EXAMPLES);reserve={r['sent_id'] for rows in load(RESERVE)['authors'].values() for r in rows};assert not set(data)&reserve;queryids={e['sent_id'] for e in examples};partitions={}
    for f in range(5):partitions[str(f)]={name:[sid for sid in data if condition(fold(sid))] for name,condition in (('fit',lambda g:g not in (f,(f+1)%5)),('calibration',lambda g:g==(f+1)%5),('test',lambda g:g==f))}
    OUT.mkdir();paths=[Path(__file__),Path('src/voynich_smt/source_morphology.py'),Path('src/voynich_smt/relational_compatibility.py'),Path('src/voynich_smt/morphology_stress.py'),SOURCE,EXAMPLES,PREVIOUS/'verification-manifest.json',RESERVE]
    save(OUT/'manifest.json',dict(inputs={str(p):digest(p) for p in paths},partitions=partitions,
        scope='Reused4070 source Cicero/Palladius sentences and326 iteration46 overt-subject examples. Five outer sentence folds; fit3folds, calibration nextfold, test heldfold. No test sentence morphology contributes to its model/dictionary/calibration. No prior Jerome/Caesar queries or reserve scoring; not fresh independent confirmation.',
        channels='Inference gets readable normalized Latin word and supplied POS only. Nominative/finite eligibility plus Number/Person are predicted together. Gold construction existence/reference selection and POS remain supplied; not anonymous-cipher morphology induction or blind parsing.',
        labels='NOUN/PROPN: OTHER,NomSing3,NomPlur3; PRON: OTHER plus6 nominative number/person states; VERB/AUX: OTHER plus6 finite states. Missing/non-atomic morphology excluded from fitting/calibration/scorable token evaluation, but all applicable test tokens predicted.',
        estimator='Source word counts with pseudocount2 toward longest source suffix1..4 with>=5 labeled tokens, smoothed by2 toward POS-group addhalf prior. POS-specific word keys; suffix priors share noun/propernoun and verb/aux groups. No tuning.',
        policies='Dictionary observed fit-only labels, unknown-form fallback all states; top1; label-conditional split-conformal thresholds alpha.05/.01; all states uninformative control. Calibration counts and thresholds never add dictionary readings. Finite quantile formula; sparse classes include all. No formal coverage claim under sentence clustering/development reuse.',
        evaluation='All labeled held-source tokens plus fixed326 reference constructions. Raw-vs-agreement exact/link survival, unique correct/wrong, empty and propagation; fixed270 clean-ambiguous cohort, author and fit-known/unseen reference forms. Candidate cardinality/label coverage and empty sets by POS group. False singleton never counted as recovery.'))
    save(OUT/'split-freeze.json',dict(inputs={str(p):digest(p) for p in OUT.glob('*.json')}));models={}
    for f in range(5):
        partition=partitions[str(f)];model=fit(data[sid]['tokens'] for sid in partition['fit']);policies={name:calibrate(model,(data[sid]['tokens'] for sid in partition['calibration']),alpha) for name,alpha in (('set95',.05),('set99',.01))};models[str(f)]=dict(model=model,policies=policies);print('Fitted/calibrated fold',f,model['training_tokens'],flush=True)
    save(OUT/'models.json',models);save(OUT/'prediction-freeze.json',dict(inputs={str(p):digest(p) for p in OUT.glob('*.json')}));index=[]
    for f in range(5):
        partition=partitions[str(f)];model=models[str(f)]['model'];policies=models[str(f)]['policies'];types={}
        for sid in partition['test']:
            for t in data[sid]['tokens']:
                key=readings_key(t)
                if group(t['pos']) and key not in types:types[key]=predict(model,policies,t['word'],t['pos'])
        sentences={}
        for sid in partition['test']:
            if sid not in queryids:continue
            tokens=data[sid]['tokens'];sentences[sid]={}
            for arm in ARMS:
                domain=domains(tokens,types,arm);sentences[sid][arm]={rule:encode(sv_lattice(domain,rule)) for rule in ('none','agreement')}
        filename=f'predictions-{f}.json';save(OUT/filename,dict(fold=f,types=types,sentences=sentences));index.append(filename)
    save(OUT/'prediction-index.json',index);save(OUT/'evaluation-freeze.json',dict(inputs={str(p):digest(p) for p in OUT.glob('*.json')}));evaluate()


def evaluate():
    data=load(SOURCE);examples=load(EXAMPLES);manifest=load(OUT/'manifest.json');predictions={p['fold']:p for p in (load(OUT/f) for f in load(OUT/'prediction-index.json'))};token=defaultdict(lambda:dict(n=0,covered=0,total_size=0,empty=0));perexample=[]
    for f,pred in predictions.items():
        for sid in manifest['partitions'][str(f)]['test']:
            for t in data[sid]['tokens']:
                y=label(t)
                if y is None:continue
                output=pred['types'][readings_key(t)];g=group(t['pos']);known='seen' if output['seen'] else 'unseen'
                for arm in ARMS:
                    candidates=output['sets'][arm]
                    for cohort in ('all',known):
                        row=token[arm+'/'+g+'/'+cohort];row['n']+=1;row['covered']+=y in candidates;row['total_size']+=len(candidates);row['empty']+=not candidates
    for e in examples:
        f=fold(e['sent_id']);pred=predictions[f];tokens=data[e['sent_id']]['tokens'];seen=all(pred['types'][readings_key(tokens[i])]['seen'] for i in (e['subject'],e['predicate']));common=e['arms']['none']['summaries']['none']['reference_retained'] and e['arms']['agreement']['summaries']['none']['reference_retained'] and e['arms']['none']['summaries']['none']['links']>1
        perexample.append(dict(sent_id=e['sent_id'],author=e['author'],subject=e['subject'],predicate=e['predicate'],fold=f,both_forms_seen=seen,clean_ambiguous=common,arms={arm:{rule:link_summary(pred['sentences'][e['sent_id']][arm][rule],e['reference']) for rule in ('none','agreement')} for arm in ARMS}))
    structural={}
    for author in ('pooled','Cicero','Palladius'):
        for cohort in ('all','both_seen','unseen_any','clean_ambiguous'):
            selected=[r for r in perexample if (author=='pooled' or r['author']==author) and (cohort=='all' or r['both_forms_seen'] if cohort=='both_seen' else not r['both_forms_seen'] if cohort=='unseen_any' else r['clean_ambiguous'] if cohort=='clean_ambiguous' else True)]
            # Explicit cohort filter avoids interpreting seen forms as independent data.
            selected=[r for r in perexample if (author=='pooled' or r['author']==author) and (cohort=='all' or (cohort=='both_seen' and r['both_forms_seen']) or (cohort=='unseen_any' and not r['both_forms_seen']) or (cohort=='clean_ambiguous' and r['clean_ambiguous']))]
            for arm in ARMS:
                for rule in ('none','agreement'):
                    scores=[r['arms'][arm][rule] for r in selected];structural[f'{author}/{cohort}/{arm}/{rule}']=dict(n=len(scores),reference_exact=sum(r['reference_exact'] for r in scores),reference_link=sum(r['reference_link'] for r in scores),unique_correct=sum(r['unique_correct'] for r in scores),false_unique=sum(r['false_unique'] for r in scores),empty=sum(r['links']==0 for r in scores),mean_links=float(np.mean([r['links'] for r in scores])) if scores else None,new_predicates=sum(r['new_opposite']['subject'] for r in scores),new_subjects=sum(r['new_opposite']['predicate'] for r in scores))
    for row in token.values():row.update(coverage=row['covered']/row['n'],mean_size=row['total_size']/row['n'])
    save(OUT/'reference-evaluation.json',perexample);save(OUT/'evaluation.json',dict(tokens=dict(token),structure=structural,note='Source cross-validation, selected eligible constructions, oracle POS and readable Latin words. Label-conditional thresholds are empirical; no guaranteed joint/structural coverage. No target metric selection.'))
    for k,v in structural.items():
        if '/all/' in k and k.startswith('pooled/'):print(k,v)
    print('Token coverage',{k:(round(v['coverage'],3),round(v['mean_size'],2),v['n']) for k,v in token.items() if k.endswith('/all')})
if __name__=='__main__':run()
