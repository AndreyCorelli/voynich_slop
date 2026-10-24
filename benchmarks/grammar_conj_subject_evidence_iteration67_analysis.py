"""Attribute learned conjunct evidence effects on the inspected coordination cases."""
from benchmarks.grammar_conj_subject_evidence_iteration67 import *


def run():
    rows=load(OUT/'frame-predictions.json');lookup={(r['sid'],r['subject']):r for r in rows};probes={(r['sid'],r['subject']):r for r in load(OUT/'probe-predictions.json')};cases=[]
    for r in load(PREVIOUS/'attribution.json')['cases']:
        item=dict(r);sid=r['sid'];s=r['subject'];item['context_prediction']=lookup[(sid,s)]['conj_unit']['context'];item['context_restores_exact']=item['context_prediction']==r['gold'];item['root_conj_probability']=probes[(sid,s)]['probabilities']['context'];item['rival_probabilities']=[dict(subject=q['subject'],same_component=q['same_component'],conj_probability=probes[(sid,q['subject'])]['probabilities']['context']) for q in r['rivals']];cases.append(item)
    changed=Counter()
    for r in rows:
        if r['carrier_ambiguous']:continue
        a=r['coord_unit']['competition65'];b=r['conj_unit']['context'];g=r['unit_gold']
        if a!=b:
            changed['changed']+=1
            if g is not None and a==g:changed['lost_exact']+=1
            if g is not None and b==g:changed['gained_exact']+=1
    metrics={}
    for mode in MODES:
        records=list(probes.values());p=np.asarray([r['probabilities'][mode] for r in records]);y=np.asarray([r['label'] for r in records],dtype=int);metrics[mode]=dict(n=len(y),positives=int(y.sum()),accuracy=float(np.mean((p>=.5)==y)),brier=float(np.mean((p-y)**2)))
    save(OUT/'posthoc-analysis.json',dict(unchanged_policies=True,changed=dict(changed),probe_metrics=metrics,cases=cases));print('Case recovery',sum(c['context_restores_exact'] for c in cases),'changes',dict(changed))
if __name__=='__main__':run()
