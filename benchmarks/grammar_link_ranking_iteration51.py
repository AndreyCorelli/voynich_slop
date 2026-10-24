"""Oracle competitor audit and a held-sentence single-cue ranking diagnostic."""
from pathlib import Path
from collections import Counter
from statistics import mean,median
from benchmarks.grammar_proper_uncertainty_iteration50 import OUT as PREVIOUS
from benchmarks.grammar_factor_morphology_iteration49 import SOURCE,EXAMPLES,fold,load,save,digest
from benchmarks.grammar_relational_compatibility_iteration46 import eligible_subjects
from voynich_smt.source_morphology import domains
from voynich_smt.relational_compatibility import sv_lattice
from voynich_smt.link_ranking import features,best,select
OUT=PREVIOUS.parent/'iteration51'


def annotated_links(tokens):
    return {(s,t['head']) for s,t in enumerate(tokens) if t['rel']=='nsubj' and t['head'] is not None and tokens[t['head']]['pos'] in ('VERB','AUX') and tokens[t['head']]['features'].get('VerbForm')=='Fin'}


def owner(tokens,index):
    seen=set()
    while index is not None and index not in seen:
        seen.add(index);t=tokens[index]
        if t['pos'] in ('VERB','AUX') and t['features'].get('VerbForm')=='Fin':return index
        index=t['head']
    return None


def source_rows(data,ids,pool):
    rows=[]
    for e in pool:
        if e['sent_id'] not in ids:continue
        tokens=data[e['sent_id']]['tokens'];pairs=[(s,v) for s,t in enumerate(tokens) if t['pos'] in ('NOUN','PROPN','PRON') for v,u in enumerate(tokens) if u['pos'] in ('VERB','AUX') and s!=v]
        rows.append(dict(reference=[e['subject'],e['predicate']],pairs=pairs,observations={p:features(tokens,*p) for p in pairs},valid=annotated_links(tokens)))
    return rows


def run():
    assert not OUT.exists()
    previous=load(PREVIOUS/'verification-manifest.json')
    for p,h in previous['inputs'].items():assert digest(p)==h,p
    OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),Path('src/voynich_smt/link_ranking.py'),SOURCE,EXAMPLES,PREVIOUS/'verification-manifest.json',PREVIOUS/'type-predictions.json',OUT/'proposal-design.md']
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='Same folds/source as49, proper_unseen50. Broad candidate sets retained. Select one of intervening verbal/SCONJ/CCONJ penalties on fit source anchored ranking, then weight0,.5,1,2,4,8,16 on calibration source. Source fit/calibration candidates use POS-only pairs, not predictions trained on an outer test set. Gold edges used for training/evaluation only. Inference uses POS and index only. Other annotated finite nsubj links are valid alternatives. Reused development evaluation; no reserve.'))
    data=load(SOURCE);examples=load(EXAMPLES);partitions=load(PREVIOUS.parent/'iteration49/manifest.json')['partitions'];pool,_=eligible_subjects(data);models={}
    for f in range(5):
        part=partitions[str(f)];models[str(f)]=select(source_rows(data,set(part['fit']),pool),source_rows(data,set(part['calibration']),pool))
    save(OUT/'models.json',models);save(OUT/'model-freeze.json',dict(inputs={str(p):digest(p) for p in OUT.glob('*.json')}))
    predictions=load(PREVIOUS/'type-predictions.json');previousrefs={(r['sent_id'],r['subject'],r['predicate']):r for r in load(PREVIOUS/'reference-evaluation.json')};rows=[];checks=0
    for e in examples:
        sid=e['sent_id'];tokens=data[sid]['tokens'];pairs=sorted({tuple(c[:2]) for c in sv_lattice(domains(tokens,predictions[str(fold(sid))],'proper_unseen'))});reference=(e['subject'],e['predicate']);obs={p:features(tokens,*p) for p in pairs};mutated=[dict(t,features={},head=None,rel='?',lemma='?',word='?') for t in tokens];assert obs=={p:features(mutated,*p) for p in pairs};checks+=1
        valid=annotated_links(tokens);old=previousrefs[sid,*reference];assert (reference in pairs)==old['arms']['proper_unseen']['agreement']['reference_link'];model=models[str(fold(sid))];arms={}
        for name,cue,weight in [('distance',None,0.),('selected',model['cue'],model['weight'])]:
            arms[name]={}
            for task,index in [('unanchored',None),('known_subject',0),('known_predicate',1)]:
                choices=[p for p in pairs if index is None or p[index]==reference[index]];winners=best(choices,obs,cue,weight)
                arms[name][task]=dict(top=winners,reference_top=reference in winners,unique_correct=winners==[reference],unique_other_valid=len(winners)==1 and winners[0] in valid and winners[0]!=reference,unique_wrong=len(winners)==1 and winners[0] not in valid,tie=len(winners)>1,empty=not winners,any_valid_top=any(p in valid for p in winners),fractional_reference=(1/len(winners) if reference in winners else 0),fractional_valid=(sum(p in valid for p in winners)/len(winners) if winners else 0))
        audit=Counter();cuewins=Counter();refobs=features(tokens,*reference)
        for pair in pairs:
            if pair==reference:continue
            s,v=pair
            category='other_annotated_link' if pair in valid else 'cross_finite_owner' if owner(tokens,s)!=v else 'same_owner_non_subject'
            audit[category]+=1
            if pair not in valid:
                for cue in ('verbal','subordinator','coordinator'):
                    cuewins[cue+'_reference_lower']+=refobs[cue]<obs[pair][cue];cuewins[cue+'_reference_higher']+=refobs[cue]>obs[pair][cue]
        rows.append(dict(sent_id=sid,subject=reference[0],predicate=reference[1],author=e['author'],clean_ambiguous=old['clean_ambiguous'],reference_survives=reference in pairs,links=len(pairs),annotated_links_in_lattice=sum(p in valid for p in pairs),oracle_audit=dict(audit),cue_audit=dict(cuewins),arms=arms))
    save(OUT/'reference-evaluation.json',rows);result={}
    for cohort in ('all','hard','Cicero','Palladius'):
        chosen=[r for r in rows if cohort=='all' or cohort=='hard' and r['clean_ambiguous'] or r['author']==cohort]
        for arm in ('distance','selected'):
            for task in ('unanchored','known_subject','known_predicate'):
                scores=[r['arms'][arm][task] for r in chosen];result[cohort+'/'+arm+'/'+task]=dict(n=len(scores),**{k:sum(s[k] for s in scores) for k in ('reference_top','unique_correct','unique_other_valid','unique_wrong','tie','empty','any_valid_top','fractional_reference','fractional_valid')})
    audit=Counter();cues=Counter()
    for r in rows:audit.update(r['oracle_audit']);cues.update(r['cue_audit'])
    surviving=[r for r in rows if r['reference_survives']];opportunity=dict(n=len(rows),reference_survives=len(surviving),unique=sum(r['links']==1 and r['reference_survives'] for r in rows),mean_links=mean(r['links'] for r in rows),median_links=median(r['links'] for r in rows),maximum_links=max(r['links'] for r in rows),multiple_annotated_links=sum(r['annotated_links_in_lattice']>1 for r in rows),competitors=dict(audit),cues=dict(cues))
    save(OUT/'evaluation.json',dict(opportunity=opportunity,ranking=result,selected={f:dict(cue=m['cue'],weight=m['weight']) for f,m in models.items()},note='Unanchored single-link ranking does not reconstruct all sentence links. Tied reference inclusion is not unique recovery; other valid links are not counted as wrong.'))
    save(OUT/'validation.json',dict(previous_hashes=len(previous['inputs']),reference_survival_replays=checks,gold_inference_mutation_checks=checks,reserved_unscored=200,prior_queries_scored=0))
    print(opportunity);print({f:(m['cue'],m['weight']) for f,m in models.items()})
    for k,r in result.items():
        if k.startswith(('all/','hard/')):print(k,r)
if __name__=='__main__':run()
