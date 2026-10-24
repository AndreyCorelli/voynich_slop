"""Feature-shared morphology vs the frozen joint-state model, same source splits."""
from pathlib import Path
from collections import defaultdict
import numpy as np
from benchmarks.grammar_source_morphology_iteration48 import OUT as PREVIOUS,ROOT,SOURCE,EXAMPLES,RESERVE,fold,load,save,digest
from voynich_smt.construction_interventions import readings_key
from voynich_smt.source_morphology import group,label as joint_label,domains
from voynich_smt.factor_morphology import fit,calibrate,predict,FEATURES,POLICIES,target,VALUES
from voynich_smt.relational_compatibility import sv_lattice
from voynich_smt.morphology_stress import encode,link_summary
OUT=ROOT/'iteration49'
SUPERVISIONS=('matched','expanded')
ARMS=tuple(s+'_'+p for s in SUPERVISIONS for p in POLICIES)


def run():
    assert not OUT.exists()
    for p,h in load(PREVIOUS/'verification-manifest.json')['inputs'].items():assert digest(p)==h,p
    data=load(SOURCE);examples=load(EXAMPLES);partitions=load(PREVIOUS/'manifest.json')['partitions'];reserve={r['sent_id'] for rows in load(RESERVE)['authors'].values() for r in rows};assert not set(data)&reserve;queryids={e['sent_id'] for e in examples}
    OUT.mkdir();paths=[Path(__file__),Path('src/voynich_smt/factor_morphology.py'),Path('src/voynich_smt/source_morphology.py'),Path('src/voynich_smt/relational_compatibility.py'),Path('src/voynich_smt/morphology_stress.py'),SOURCE,EXAMPLES,PREVIOUS/'verification-manifest.json',PREVIOUS/'manifest.json',PREVIOUS/'models.json',PREVIOUS/'evaluation.json',PREVIOUS/'reference-evaluation.json',RESERVE]
    save(OUT/'manifest.json',dict(inputs={str(p):digest(p) for p in paths},partitions=partitions,arms=ARMS,
        scope='Same4070 source sentences,326 selected constructions and five outer partitions as iteration48. Readable Latin forms/oracle POS and eligible overt-subject selection retained; no test morphology in fitting/calibration; no prior target queries/reserve; development cross-validation, not independent confirmation.',
        estimator='Same source word/suffix counts, maxsuffix4,mincount5,pseudocount2,addhalf prior. Separate binary role (Nom/other or Fin/other), binary Number and3class Person; noun/propernoun third person fixed. Joint probabilities use independent component product; candidate sets use Cartesian combinations, not joint calibrated scores.',
        expanded='Role uses all atomic known Case/VerbForm. Number uses every applicable Sing/Plur annotation regardless of Case/VerbForm. Person uses all applicable1/2/3 annotations on PRON/VERB/AUX. Component missingness handled separately.',
        matched='Control: role only where iteration48 joint label scorable; Number/Person only where that label is a positive Nom/Fin state. No extra component annotations from OTHER or incompletely labeled tokens.',
        policies='top1 composed joint MAP; set95/set99 use that alpha per component, NOT the same joint error budget as old joint sets; total95/total99 divide alpha by2 learned components for nominal or3 for pronoun/verbal. Source calibration label-conditional within POSgroup/component. No formal structural coverage guarantee and no target selection.',
        evaluation='Compare coverage/cardinality and unique correct/wrong links jointly; raw-vs-agreement exact/link survival, empty sets, propagation; fixed clean270 ambiguous cohort and seen/unseen reference cohorts from iteration48; both source authors. Token metrics evaluated on same old joint-scorable tokens for comparability, plus marginal-feature diagnostics.'))
    save(OUT/'fit-freeze.json',dict(inputs={str(p):digest(p) for p in OUT.glob('*.json')}));models={}
    for f in range(5):
        p=partitions[str(f)];models[str(f)]={}
        for supervision in SUPERVISIONS:
            model=fit((data[sid]['tokens'] for sid in p['fit']),supervision);policies=calibrate(model,(data[sid]['tokens'] for sid in p['calibration']));models[str(f)][supervision]=dict(model=model,policies=policies)
        print('Trained/calibrated',f,flush=True)
    save(OUT/'models.json',models);save(OUT/'prediction-freeze.json',dict(inputs={str(p):digest(p) for p in OUT.glob('*.json')}));index=[]
    for f in range(5):
        types={};p=partitions[str(f)]
        for sid in p['test']:
            for token in data[sid]['tokens']:
                key=readings_key(token)
                if group(token['pos']) is None or key in types:continue
                output={s:predict(models[str(f)][s]['model'],models[str(f)][s]['policies'],token['word'],token['pos']) for s in SUPERVISIONS};types[key]=dict(sets={s+'_'+policy:output[s]['sets'][policy] for s in SUPERVISIONS for policy in POLICIES},components=output)
        sentences={}
        for sid in p['test']:
            if sid not in queryids:continue
            tokens=data[sid]['tokens'];sentences[sid]={}
            for arm in ARMS:
                domain=domains(tokens,types,arm);sentences[sid][arm]={rule:encode(sv_lattice(domain,rule)) for rule in ('none','agreement')}
        filename=f'predictions-{f}.json';save(OUT/filename,dict(fold=f,types=types,sentences=sentences));index.append(filename)
    save(OUT/'prediction-index.json',index);save(OUT/'evaluation-freeze.json',dict(inputs={str(p):digest(p) for p in OUT.glob('*.json')}));evaluate()


def evaluate():
    data=load(SOURCE);examples=load(EXAMPLES);partitions=load(OUT/'manifest.json')['partitions'];predictions={r['fold']:r for r in (load(OUT/f) for f in load(OUT/'prediction-index.json'))};oldrefs={(r['sent_id'],r['subject'],r['predicate']):r for r in load(PREVIOUS/'reference-evaluation.json')};token=defaultdict(lambda:dict(n=0,covered=0,total_size=0,empty=0));marginal=defaultdict(lambda:dict(n=0,covered=0,total_size=0));perexample=[]
    for f,p in predictions.items():
        for sid in partitions[str(f)]['test']:
            for t in data[sid]['tokens']:
                g=group(t['pos'])
                if g is None:continue
                output=p['types'][readings_key(t)];y=joint_label(t)
                if y is not None:
                    for arm in ARMS:
                        candidates=output['sets'][arm];r=token[arm+'/'+g];r['n']+=1;r['covered']+=y in candidates;r['total_size']+=len(candidates);r['empty']+=not candidates
                for feature in FEATURES:
                    y=target(t,feature,'expanded')
                    if y is None:continue
                    for s in SUPERVISIONS:
                        for policy in POLICIES[1:]:
                            candidates=output['components'][s]['feature_sets'][policy][feature];r=marginal[s+'_'+policy+'/'+g+'/'+feature];r['n']+=1;r['covered']+=y in candidates;r['total_size']+=len(candidates)
    for e in examples:
        p=predictions[fold(e['sent_id'])];old=oldrefs[e['sent_id'],e['subject'],e['predicate']];perexample.append(dict(sent_id=e['sent_id'],author=e['author'],subject=e['subject'],predicate=e['predicate'],both_forms_seen=old['both_forms_seen'],clean_ambiguous=old['clean_ambiguous'],arms={arm:{rule:link_summary(p['sentences'][e['sent_id']][arm][rule],e['reference']) for rule in ('none','agreement')} for arm in ARMS}))
    result={}
    for author in ('pooled','Cicero','Palladius'):
        for cohort in ('all','both_seen','unseen_any','clean_ambiguous'):
            chosen=[r for r in perexample if (author=='pooled' or r['author']==author) and (cohort=='all' or (cohort=='both_seen' and r['both_forms_seen']) or (cohort=='unseen_any' and not r['both_forms_seen']) or (cohort=='clean_ambiguous' and r['clean_ambiguous']))]
            for arm in ARMS:
                for rule in ('none','agreement'):
                    scores=[r['arms'][arm][rule] for r in chosen];result[f'{author}/{cohort}/{arm}/{rule}']=dict(n=len(scores),reference_exact=sum(r['reference_exact'] for r in scores),reference_link=sum(r['reference_link'] for r in scores),unique_correct=sum(r['unique_correct'] for r in scores),false_unique=sum(r['false_unique'] for r in scores),empty=sum(r['links']==0 for r in scores),mean_links=float(np.mean([r['links'] for r in scores])) if scores else None,new_predicates=sum(r['new_opposite']['subject'] for r in scores),new_subjects=sum(r['new_opposite']['predicate'] for r in scores))
    for rows in (token,marginal):
        for r in rows.values():r.update(coverage=r['covered']/r['n'],mean_size=r['total_size']/r['n'])
    save(OUT/'reference-evaluation.json',perexample);save(OUT/'evaluation.json',dict(tokens=dict(token),marginal=dict(marginal),structure=result,comparison_baseline=str(PREVIOUS/'evaluation.json'),note='No target-based policy selection. Per-component nominal alpha and allocated total alpha are distinct; empirical coverage and efficiency are primary. Same readable-word/oracle-POS limits as iteration48.'))
    for arm in ARMS:print(arm,result[f'pooled/all/{arm}/agreement'])
    print('Token pronoun',{k:dict(coverage=round(v['coverage'],4),mean_size=round(v['mean_size'],2)) for k,v in token.items() if k.endswith('/pronoun')})
if __name__=='__main__':run()
