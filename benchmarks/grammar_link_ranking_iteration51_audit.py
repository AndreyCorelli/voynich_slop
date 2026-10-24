"""Independent partition/model/ranking replay and paired/sentence-level audit."""
from collections import Counter,defaultdict
from benchmarks.grammar_link_ranking_iteration51 import OUT,PREVIOUS,SOURCE,EXAMPLES,load,save,digest,fold,source_rows,annotated_links
from benchmarks.grammar_relational_compatibility_iteration46 import eligible_subjects
from voynich_smt.link_ranking import features,best,select
from voynich_smt.source_morphology import domains
from voynich_smt.relational_compatibility import sv_lattice


def run():
    checks=0
    for filename in ('design-freeze.json','model-freeze.json'):
        for p,h in load(OUT/filename)['inputs'].items():assert digest(p)==h,p;checks+=1
    data=load(SOURCE);parts=load(PREVIOUS.parent/'iteration49/manifest.json')['partitions'];pool,_=eligible_subjects(data);models=load(OUT/'models.json');pred=load(PREVIOUS/'type-predictions.json');rows=load(OUT/'reference-evaluation.json');look={(r['sent_id'],r['subject'],r['predicate']):r for r in rows};replays=0
    for f in range(5):
        part=parts[str(f)];fit,cal,test=(set(part[k]) for k in ('fit','calibration','test'));assert not (fit&cal or fit&test or cal&test)
        assert select(source_rows(data,fit,pool),source_rows(data,cal,pool))==models[str(f)]
    for e in load(EXAMPLES):
        sid=e['sent_id'];tokens=data[sid]['tokens'];pairs=sorted({tuple(c[:2]) for c in sv_lattice(domains(tokens,pred[str(fold(sid))],'proper_unseen'))});obs={p:features(tokens,*p) for p in pairs};r=look[sid,e['subject'],e['predicate']];model=models[str(fold(sid))]
        for arm,cue,w in [('distance',None,0),('selected',model['cue'],model['weight'])]:
            for task,index in [('unanchored',None),('known_subject',0),('known_predicate',1)]:
                ref=(e['subject'],e['predicate']);choices=[p for p in pairs if index is None or p[index]==ref[index]];assert best(choices,obs,cue,w)==list(map(tuple,r['arms'][arm][task]['top']));replays+=1
    paired={}
    for task in ('unanchored','known_subject','known_predicate'):
        counts=Counter()
        for r in rows:
            a=r['arms']['distance'][task];b=r['arms']['selected'][task]
            for field in ('reference_top','unique_correct','unique_wrong'):
                counts[field+'_gained']+=not a[field] and b[field];counts[field+'_lost']+=a[field] and not b[field]
        paired[task]=dict(counts)
    sentences=defaultdict(list)
    for r in rows:sentences[r['sent_id']].append(r)
    unique={};covered_sentences=sum(any(r['reference_survives'] for r in rs) for rs in sentences.values())
    for arm in ('distance','selected'):
        count=Counter(n=len(sentences))
        for sid,rs in sentences.items():
            outputs=[r['arms'][arm]['unanchored'] for r in rs];assert all(o['top']==outputs[0]['top'] for o in outputs)
            o=outputs[0];valid=annotated_links(data[sid]['tokens']);top=list(map(tuple,o['top']));count['unique_valid']+=len(top)==1 and top[0] in valid;count['unique_wrong']+=len(top)==1 and top[0] not in valid;count['ties']+=len(top)>1;count['any_valid_top']+=any(p in valid for p in top)
        unique[arm]=dict(count)
    save(OUT/'additional-audit.json',dict(paired=paired,unique_sentences=unique,one_link_per_sentence_selected_reference_ceiling=covered_sentences,reference_denominator=len(rows),note='Each selected reference pair occurs once. At most one such pair per sentence can be uniquely recovered by a sentence-global single-link chooser. This is a task-design ceiling, not a parsing upper bound.'))
    save(OUT/'independent-validation.json',dict(hash_checks=checks,models_reselected=5,rankings_replayed=replays,partitions_disjoint=True,reserve_unscored=200,prior_queries_scored=0))
    print(paired);print(unique);print('One-link selected-reference ceiling',covered_sentences,'/',len(rows))
if __name__=='__main__':run()
