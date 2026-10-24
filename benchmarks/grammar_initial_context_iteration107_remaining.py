"""Diagnose every remaining wrong action; no counterfactual policy adoption."""
from benchmarks.grammar_initial_context_iteration107 import *


def group(sid):return 'original100' if not sid.startswith('unlabeled104-') else sid.split('-')[1]


def run():
    paths=[Path(__file__),OUT/'pair-cases.json',OUT/'actions.json']+[OUT/('public-'+v+'.json') for v in ['base','civil','expanded']]
    save(OUT/'remaining-inputs.json',dict(inputs={str(p):digest(p) for p in paths},scope='POSTRESULT decomposition ofALL3added-contextwrongactions, no model/threshold/viewselection. Reportall5bookdeletioninfluencesfor2primarywrongs as diagnosticONLY.'))
    cases=load(OUT/'pair-cases.json');actions=load(OUT/'actions.json');rows=[]
    for view in ['civil','expanded']:
        public=load(OUT/('public-'+view+'.json'));groups=np.array([group(s['sent_id']) for s in public])
        for c in [c for c in cases if c['block']==view and c['reference']['error']]:
            chosen=actions['frozen95'][view+'/'+c['case']]
            if chosen is None or chosen==c['reference']['pair']:continue
            payload=np.load(OUT/view/(c['case']+'.npz'));pairs=[]
            for kind,pair in [('selected',chosen),('true',c['reference']['pair'])]:
                if pair is None:continue
                j=next(j for j,p in enumerate(c['pairs']) if p['pair']==pair);n,q=payload['counts'][j],payload['sums'][j];endpoints=[]
                for k,opaque in enumerate(pair):
                    parts={}
                    for g in sorted(set(groups)):
                        mask=groups==g;count=int(n[mask,k].sum())
                        if count:parts[g]=dict(n=count,sentences=int((n[mask,k]>0).sum()),p_cconj=float(q[mask,k].sum()/count))
                    p=float(q[:,k].sum()/n[:,k].sum());tag=c['proposed'][j][k];margin=float(np.log((p+1e-12)/(1-p+1e-12))*(1 if tag=='ADP' else -1));endpoints.append(dict(word=c['identities'][opaque],proposed=tag,mean_p_cconj=p,margin=margin,groups=parts))
                pairs.append(dict(kind=kind,gain=c['pairs'][j]['gain'],endpoints=endpoints))
            influence=[]
            if view=='expanded':
                for removed in sorted(set(groups)-{'original100'}):
                    mask=groups!=removed;scores=[]
                    for j,p in enumerate(c['pairs']):
                        n=payload['counts'][j][mask];q=payload['sums'][j][mask];gain=float(gains_from_totals(n.sum(0),q.sum(0),c['proposed'][j]));supported=all(n[:,k].sum()>=5 and (n[:,k]>0).sum()>=3 for k in range(2));scores.append(dict(pair=p['pair'],gain=gain,supported=bool(supported)))
                    f=pair_features(scores);selectedpair=selected(f,load(OUT/'policies.json')['frozen95']);influence.append(dict(removed_book=removed,features=f,selected_words=[c['identities'][i] for i in selectedpair] if selectedpair else None,exact_hit=selectedpair is not None and selectedpair==c['reference']['pair']))
            rows.append(dict(case=view+'/'+c['case'],pair_components=pairs,leave_one_book_out=influence))
    save(OUT/'remaining-errors.json',dict(all_added_context_wrong_cases=rows,policy_changed=False,limits='Bookdeletions are correlated postresult counterfactuals, not selection ofnewcontext/default. No labels or new predictions consumed.'))
    profiles=0;deletions=0
    for row in rows:
        for p in row['pair_components']:
            assert math.isclose(sum(e['margin'] for e in p['endpoints']),p['gain'],rel_tol=1e-9,abs_tol=1e-10)
            for e in p['endpoints']:
                mean=sum(g['n']*g['p_cconj'] for g in e['groups'].values())/sum(g['n'] for g in e['groups'].values());assert math.isclose(mean,e['mean_p_cconj'],rel_tol=1e-12,abs_tol=1e-12);profiles+=1
        deletions+=len(row['leave_one_book_out'])
    assert len(rows)==3 and deletions==10
    assert load(OUT/'policies.json')==load(CONTEXT/'policies.json')
    save(OUT/'remaining-audit.json',dict(wrong_cases_decomposed=len(rows),endpoint_group_means_reconstructed=profiles,all_book_deletion_counterfactuals=deletions,no_policy_change=True))
    for row in rows:print(json.dumps(row))
if __name__=='__main__':run()
