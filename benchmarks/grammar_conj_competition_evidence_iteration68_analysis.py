"""Post hoc paired analysis of the restricted coordination treatment."""
from benchmarks.grammar_conj_competition_evidence_iteration68 import *


def run():
    rows=[r for r in load(OUT/'frame-predictions.json') if not r['carrier_ambiguous']];lookup={(r['sid'],r['subject']):r for r in rows};probes={(r['sid'],r['subject']):r for r in load(OUT/'probe-predictions.json')};cases=[];changes=Counter();coordination_changes=dict(gained=[],lost=[])
    for r in load(PREVIOUS.parent/'iteration66'/'attribution.json')['cases']:
        item=dict(r);sid=r['sid'];s=r['subject'];item['context_prediction']=lookup[(sid,s)]['contest_unit']['context'];item['context_restores_exact']=item['context_prediction']==r['gold'];item['root_conj_probability']=probes[(sid,s)]['probabilities']['context'];item['rival_probabilities']=[dict(subject=q['subject'],same_component=q['same_component'],conj_probability=probes[(sid,q['subject'])]['probabilities']['context']) for q in r['rivals']];cases.append(item)
    by_sid=defaultdict(list)
    for r in rows:
        by_sid[r['sid']].append(r);g=r['unit_gold'];a=r['coord_unit']['competition65'];b=r['contest_unit']['context'];ac=g is not None and a==g;bc=g is not None and b==g
        if a!=b:
            changes['changed']+=1
            if ac:changes['lost_exact']+=1
            if bc:changes['gained_exact']+=1
        if r['coordination_subject'] and ac!=bc:coordination_changes['gained' if bc else 'lost'].append([r['sid'],r['subject']])
    data=load(SOURCE);rng=np.random.default_rng(6801);bootstrap={}
    for scope in ('all_source','selected_sentences'):
        ids=list(data) if scope=='all_source' else sorted({r['sid'] for r in rows if r['selected_sentence']});groups=defaultdict(list)
        for sid in ids:groups[data[sid]['author']].append(sid)
        for control in ('competition65','pos'):
            blocks=[]
            for ids_author in groups.values():
                values=[]
                for sid in ids_author:
                    rs=by_sid[sid];entry=[sum(r['unit_gold'] is not None for r in rs)]
                    for arm in (control,'context'):entry.extend((sum(unit(r,arm) is not None and unit(r,arm)==r['unit_gold'] for r in rs),sum(unit(r,arm) is not None for r in rs)))
                    values.append(entry)
                blocks.append(np.asarray(values,dtype=int))
            differences=[]
            for _ in range(2000):
                g,t0,p0,t1,p1=sum((b[rng.integers(0,len(b),size=len(b))].sum(axis=0) for b in blocks),np.zeros(5,dtype=int));differences.append(2*t1/(g+p1)-2*t0/(g+p0))
            bootstrap[scope+'/context-vs-'+control]=dict(samples=2000,delta_f1_percentile95=(np.percentile(differences,[2.5,97.5])*100).tolist(),warning='Posthoc; conditional on frozen policies; adaptive reused development data, not fresh confirmation.')
    save(OUT/'posthoc-analysis.json',dict(changes=dict(changes),coordination_changes=coordination_changes,cases=cases,bootstrap=bootstrap));print('changes',dict(changes),'case recoveries',sum(r['context_restores_exact'] for r in cases),'coordination',coordination_changes);print(bootstrap)
if __name__=='__main__':run()
