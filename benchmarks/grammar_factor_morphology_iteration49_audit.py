"""Paired reference changes, additional supervision and component-level losses."""
from benchmarks.grammar_factor_morphology_iteration49 import OUT,PREVIOUS,SOURCE,EXAMPLES,ARMS,fold,load,save
from voynich_smt.construction_interventions import readings_key
from voynich_smt.factor_morphology import VALUES
from voynich_smt.source_morphology import group


def run():
    data=load(SOURCE);examples=load(EXAMPLES);old={(r['sent_id'],r['subject'],r['predicate']):r for r in load(PREVIOUS/'reference-evaluation.json')};new={(r['sent_id'],r['subject'],r['predicate']):r for r in load(OUT/'reference-evaluation.json')};pred={f:load(OUT/f'predictions-{f}.json') for f in range(5)};changes={};failures=[]
    for arm in ARMS:
        counts=dict(reference_new_losses=0,reference_rescued=0,unique_added=0,unique_removed=0)
        for key,r in new.items():
            a=old[key]['arms']['set99']['agreement'];b=r['arms'][arm]['agreement'];counts['reference_new_losses']+=a['reference_link'] and not b['reference_link'];counts['reference_rescued']+=b['reference_link'] and not a['reference_link'];counts['unique_added']+=b['unique_correct'] and not a['unique_correct'];counts['unique_removed']+=a['unique_correct'] and not b['unique_correct']
        changes[arm]=counts
    for e in examples:
        key=e['sent_id'],e['subject'],e['predicate'];r=new[key];a=old[key]['arms']['set99']['agreement'];b=r['arms']['expanded_total99']['agreement']
        if b['reference_exact'] and b['reference_link']:continue
        tokens=data[e['sent_id']]['tokens'];endpoints=[]
        for name,i,number,person in (('subject',e['subject'],e['reference'][2],e['reference'][3]),('predicate',e['predicate'],e['reference'][4],e['reference'][5])):
            output=pred[fold(e['sent_id'])]['types'][readings_key(tokens[i])]['components']['expanded'];sets=output['feature_sets']['total99'];truth=dict(role='YES',number=number,person=person);missing=[f for f,v in truth.items() if v not in sets[f]];endpoints.append(dict(endpoint=name,word=tokens[i]['word'],pos=tokens[i]['pos'],expected=truth,component_sets=sets,missing_features=missing,component_probabilities=output['component_probabilities']))
        failures.append(dict(sent_id=e['sent_id'],subject=e['subject'],predicate=e['predicate'],reference=e['reference'],old_reference_link=a['reference_link'],new_reference_link=b['reference_link'],new_reference_exact=b['reference_exact'],endpoints=endpoints,sentence=' '.join(t['word'] for t in tokens)))
    models=load(OUT/'models.json');support={f:{s:record['model']['training_labels'] for s,record in trained.items()} for f,trained in models.items()};zeros={f:{s:{k:v['n'] for k,v in record['policies']['total99']['classes'].items() if v['threshold']==0} for s,record in trained.items()} for f,trained in models.items()}
    save(OUT/'additional-audit.json',dict(paired_changes_vs_joint99=changes,training_support=support,zero_threshold_classes=zeros,note='Descriptive audits of frozen candidates; no policy selected or cutoff changed.'))
    save(OUT/'reference-failure-audit.json',failures);print(changes['expanded_total99'])
    for e in failures:
        if e['old_reference_link'] and not e['new_reference_link']:print(e['sent_id'],[(r['word'],r['missing_features'],r['component_sets']) for r in e['endpoints']])
if __name__=='__main__':run()
