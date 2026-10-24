"""Source-label availability, genuinely absent forms, and reference failures."""
from collections import Counter
from benchmarks.grammar_source_morphology_iteration48 import OUT,SOURCE,EXAMPLES,ARMS,fold,load,save
from voynich_smt.construction_interventions import readings_key


def run():
    data=load(SOURCE);examples=load(EXAMPLES);manifest=load(OUT/'manifest.json');models=load(OUT/'models.json');evalrows=load(OUT/'reference-evaluation.json');index={(r['sent_id'],r['subject'],r['predicate']):r for r in evalrows};partitions=manifest['partitions'];available={f:{readings_key(t) for sid in p['fit'] for t in data[sid]['tokens']} for f,p in partitions.items()};counts=Counter();groups={};failures=[]
    for e in examples:
        f=str(fold(e['sent_id']));tokens=data[e['sent_id']]['tokens'];keys=[readings_key(tokens[i]) for i in (e['subject'],e['predicate'])];missing=sum(k not in available[f] for k in keys);unlabeled=sum(k in available[f] and k not in models[f]['model']['words'] for k in keys);cohort='both_absent' if missing==2 else 'one_absent' if missing else 'both_present';counts[cohort]+=1;counts['endpoints_seen_but_unlabeled']+=unlabeled;r=index[e['sent_id'],e['subject'],e['predicate']]
        for arm in ARMS:
            for rule in ('none','agreement'):
                s=r['arms'][arm][rule];v=groups.setdefault(cohort+'/'+arm+'/'+rule,dict(n=0,reference_exact=0,reference_link=0,unique_correct=0,false_unique=0));v['n']+=1
                for k in ('reference_exact','reference_link','unique_correct','false_unique'):v[k]+=s[k]
        if not r['arms']['set99']['agreement']['reference_exact'] or r['arms']['top1']['agreement']['false_unique']:
            failures.append(dict(**e,seen_in_fit=[k in available[f] for k in keys],source_labeled_seen=[k in models[f]['model']['words'] for k in keys],results=r['arms'],sentence=' '.join(t['word'] for t in tokens)))
    sparse={}
    for f,trained in models.items():
        sparse[f]={name:{key:record['n'] for key,record in policy['classes'].items() if record['threshold']==0} for name,policy in trained['policies'].items()}
    save(OUT/'additional-audit.json',dict(form_counts=dict(counts),genuine_form_cohorts=groups,zero_threshold_calibration_classes=sparse,note='Availability uses word/POS keys in fit sentences including unlabeled occurrences; main seen cohort requires a labeled fit occurrence. Threshold0 includes a class for every token in its POS group. No post-hoc model selection.'))
    save(OUT/'reference-failure-audit.json',failures);print(counts)
    for k,v in groups.items():
        if 'set99/' in k:print(k,v)
if __name__=='__main__':run()
