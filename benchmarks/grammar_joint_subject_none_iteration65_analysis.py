"""Post hoc error attribution and sentence bootstrap of frozen policies."""
from benchmarks.grammar_joint_subject_none_iteration65_control import *


def metrics_for(rows,arm):
    gold={(r['sid'],*r['unit_gold']) for r in rows if r['unit_gold'] is not None};pred={(r['sid'],*r['competition_unit'][arm]) for r in rows if r['competition_unit'][arm] is not None}
    return edge_metrics(gold,pred)


def run():
    rows=[r for r in load(CONTROL/'frame-predictions.json') if not r['carrier_ambiguous']];data=load(SOURCE);parts=load(MORPH/'manifest.json')['partitions'];result=dict(posthoc=True,models_and_policies_unchanged=True);changes={}
    for arm in ARMS[1:]:
        counts=Counter()
        for r in rows:
            a=r['competition_carrier']['baseline'];b=r['competition_carrier'][arm];g=r['unit_gold']
            if a==b:continue
            kind='dropped' if b is None else 'added' if a is None else 'rerouted';counts[kind]+=1
            ac=g is not None and r['competition_unit']['baseline']==g;bc=g is not None and r['competition_unit'][arm]==g
            if ac:counts[kind+'_previously_exact']+=1
            if bc:counts[kind+'_now_exact']+=1
        changes[arm]=dict(counts)
    result['changes']=changes
    groups=load(PREVIOUS/'sentence-audit.json');coord={(r['sid'],s) for r in groups for s in r['coordinated_subjects']};multi={(r['sid'],s) for r in groups for g in r['gold_groups'] if len(g['subjects'])>1 for s in g['subjects']}
    result['positive_cohorts']={}
    for name,keys in (('coordination',coord),('multiple_gold_subjects',multi)):
        rs=[r for r in rows if (r['sid'],r['subject']) in keys and r['unit_gold'] is not None]
        result['positive_cohorts'][name]=dict(n=len(rs),exact={a:sum(r['competition_unit'][a]==r['unit_gold'] for r in rs) for a in ARMS})
    result['fold_metrics']={str(f):{a:metrics_for([r for r in rows if r['sid'] in set(parts[str(f)]['test'])],a) for a in ARMS} for f in range(5)}
    result['author_metrics']={author:{a:metrics_for([r for r in rows if r['author']==author],a) for a in ARMS} for author in sorted({r['author'] for r in rows})}
    by_sid=defaultdict(list)
    for r in rows:by_sid[r['sid']].append(r)
    rng=np.random.default_rng(6501);bootstrap={}
    for scope in ('all_source','selected_sentences'):
        ids=list(data) if scope=='all_source' else sorted({r['sid'] for r in rows if r['selected_sentence']});by_author=defaultdict(list)
        for sid in ids:by_author[data[sid]['author']].append(sid)
        for control in ('baseline','threshold_carrier','threshold_unit'):
            blocks=[]
            for ids_author in by_author.values():
                block=[]
                for sid in ids_author:
                    rs=by_sid[sid];g=sum(r['unit_gold'] is not None for r in rs);values=[g]
                    for arm in (control,'carrier_cal'):
                        values.extend((sum(r['competition_unit'][arm] is not None and r['competition_unit'][arm]==r['unit_gold'] for r in rs),sum(r['competition_unit'][arm] is not None for r in rs)))
                    block.append(values)
                blocks.append(np.asarray(block,dtype=int))
            differences=[]
            for _ in range(2000):
                totals=sum((b[rng.integers(0,len(b),size=len(b))].sum(axis=0) for b in blocks),np.zeros(5,dtype=int));g,t0,p0,t1,p1=totals;differences.append(2*t1/(g+p1)-2*t0/(g+p0))
            bootstrap[scope+'/carrier_cal-vs-'+control]=dict(samples=2000,author_stratified=True,delta_f1_percentile95=(np.percentile(differences,[2.5,97.5])*100).tolist(),warning='Conditional on frozen policies; reused development data and training uncertainty not modeled.')
    result['bootstrap']=bootstrap;save(OUT/'posthoc-analysis.json',result);print(result)
if __name__=='__main__':run()
