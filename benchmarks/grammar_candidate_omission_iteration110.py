"""Frozen long-context policy under exhaustive source candidate omissions."""
from benchmarks.grammar_volume_gate_iteration109 import *
from voynich_smt.candidate_omission import omit
from voynich_smt.combined_repair_gate import select as select_gate,evaluate as evaluate_gate
OUT=ROOT/'iteration110';PREVIOUS=ROOT/'iteration109';SOURCE=ROOT/'iteration102'


def run():
    assert not OUT.exists();OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),Path('src/voynich_smt/candidate_omission.py'),Path('src/voynich_smt/combined_repair_gate.py'),Path('src/voynich_smt/pair_uncertainty.py'),PREVIOUS/'verification-manifest.json',PREVIOUS/'policies.json',SOURCE/'verification-manifest.json',SOURCE/'calibration-cases.json',ROOT/'iteration93/types.json',ROOT/'iteration95/policies.json']
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='SOURCE-ONLY eligibility stress of109FROZENlongpolicy, no recalibration/modelchange. Existing102full829casesALL64crossswaps+3controls=67. ForEACH67case evaluatecompletepool andALL16single-candidateomissions irrespectiveoftruth=1139views(1072omissions). Catalog16source-defined93words/IDs saltcal98-full. RemoveALLpaircolumnscontainingomittedID; keepALLcontexttokens,publicanchorassignments,per-occurrenceprobs/counts,pointgainsand256jointbootstrapdraws unchanged. Recomputeunique-top/gap/stability versus remainingcompetitors, not automaticabstention iforiginalwinnerremoved. Attachreference supportAFTERfeatures, retaintruepairref/ALLerrors;128trueendpointomissionerrors vs896available errors;48controlomissions. PRIMARY109fullgain.3548459/gap0/stability.5 fixed; SECONDARY95pointgaincut.61747 fixed,no stabilitygate. Reportcompletepool/omissions/available/unavailable/controls andperomittedtype, allwrongrecommendations; candidateavailabilitydiagnosticNOTliteralwordabsence or unknowncontextanchorloss. Secondarymechanismsignaudit: endpointflipmargins ofeachselectedpairfromcachedqtotals; countnegativeendpointamonghits/wrongs, no newgate/adoption/thresholdfit. No author scoring/PPintegration/newannotation/reserve/sealedtest/nuclei; reusedsourcecaldata notindependent confirmation. No omittedwordchosenfromauthorfailures.'))
    source=[c for c in load(SOURCE/'calibration-cases.json') if c['block']=='full'];assert len(source)==67;words=load(ROOT/'iteration93/types.json')['candidates'];identities={__import__('hashlib').sha256(('cal98-full|'+w).encode()).hexdigest():w for w in words};assert len(identities)==16;save(OUT/'candidate-catalogue.json',identities)
    primary=load(PREVIOUS/'policies.json')['full'];oldcut=load(ROOT/'iteration95/policies.json')['joint_context']['threshold'];policies={'long109':primary,'point95':dict(threshold=oldcut,gap=0.,stability=0.)};save(OUT/'policies.json',policies);rows=[]
    for c in source:
        assert {i for p in c['pairs'] for i in p['pair']}==set(identities);payload=np.load(SOURCE/'full'/(c['case']+'.npz'));draws=payload['draws']
        for opaque in [None]+sorted(identities):
            changed=omit(c,draws,opaque);actions={};mechanism={}
            for arm,policy in policies.items():
                pair=select_gate(changed['features'],policy);actions[arm]=pair
                if pair is not None:
                    j=next(j for j,p in enumerate(c['pairs']) if p['pair']==pair);n=payload['counts'][j].sum(0);q=payload['sums'][j].sum(0);p=q/n;margins=np.log((p+1e-12)/(1-p+1e-12))*np.array([1 if tag=='ADP' else -1 for tag in c['proposed'][j]]);assert math.isclose(float(margins.sum()),c['pairs'][j]['gain'],rel_tol=1e-9,abs_tol=1e-10);mechanism[arm]=dict(endpoint_words=[identities[i] for i in pair],endpoint_margins=margins.tolist(),minimum_margin=float(margins.min()),one_endpoint_does_not_favor_flip=bool(np.any(margins<=0)))
            # Selection is complete before truth-derived strata are attached.
            ref=changed['reference'];unavailable=ref['error'] and not ref['supported'];rows.append(dict(case=c['case'],omitted_id=opaque,omitted_word=identities.get(opaque),regime='complete' if opaque is None else 'omission',features=changed['features'],source_pair_indices=changed['source_pair_indices'],reference=ref,true_endpoint_omitted=bool(ref['error'] and opaque in (ref['pair'] or [])),actions=actions,mechanism=mechanism))
        print('replayed',c['case'],flush=True)
    save(OUT/'cases.json',rows);save(OUT/'predictions-freeze.json',dict(inputs={str(p):digest(p) for p in [OUT/'cases.json',OUT/'policies.json',OUT/'candidate-catalogue.json']}));summary={}
    groups={'complete':[r for r in rows if r['regime']=='complete'],'all_omissions':[r for r in rows if r['regime']=='omission'],'available_errors':[r for r in rows if r['regime']=='omission' and r['reference']['error'] and r['reference']['supported']],'unavailable_errors':[r for r in rows if r['regime']=='omission' and r['reference']['error'] and not r['reference']['supported']],'controls':[r for r in rows if r['regime']=='omission' and not r['reference']['error']]}
    groups.update({'omit_'+w:[r for r in rows if r['omitted_word']==w] for w in words})
    for name,group_rows in groups.items():
        summary[name]={}
        for arm,policy in policies.items():
            normalized=[dict(r,regime='all') for r in group_rows];stats=evaluate_gate(normalized,policy)['all'];stats.update(precision=stats['hit']/stats['calls'] if stats['calls'] else None,wrong_fraction=stats['wrong']/stats['n'] if stats['n'] else None);summary[name][arm]=stats
    mechanism={}
    for arm in policies:
        buckets={}
        for r in rows:
            pair=r['actions'][arm]
            if pair is None:continue
            hit=pair==r['reference']['pair'];key=r['regime']+'/'+('hit' if hit else 'wrong');b=buckets.setdefault(key,dict(selected=0,nonpositive_endpoint=0,both_positive=0));b['selected']+=1;b['nonpositive_endpoint']+=r['mechanism'][arm]['one_endpoint_does_not_favor_flip'];b['both_positive']+=not r['mechanism'][arm]['one_endpoint_does_not_favor_flip']
        mechanism[arm]=buckets
    wrong=[dict(case=r['case'],omitted_word=r['omitted_word'],arm=a,pair=r['actions'][a],features=r['features'],reference_supported=r['reference']['supported'],mechanism=r['mechanism'][a]) for r in rows for a in policies if r['actions'][a] is not None and r['actions'][a]!=r['reference']['pair']]
    save(OUT/'summary.json',summary);save(OUT/'endpoint-sign-audit.json',mechanism);save(OUT/'all-wrong-actions.json',wrong);save(OUT/'run-summary.json',dict(source_cases=len(source),omission_cases=16*len(source),total_cases=len(rows),classifier_inferences=0,policy_refits=0));print(json.dumps({k:summary[k] for k in ['complete','all_omissions','available_errors','unavailable_errors','controls']},indent=2));print(json.dumps(mechanism,indent=2))
if __name__=='__main__':run()
