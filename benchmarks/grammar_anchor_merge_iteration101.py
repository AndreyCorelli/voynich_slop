"""Diagnose the ex/200-sentence failure with eligibility factorials and logit traces."""
from benchmarks.grammar_anchor_test_length_iteration100 import *
from voynich_smt.anchor_merge_diagnostic import eligibility_sets,eligible_pairs,trace_pair,equal_group_gain
OUT=ROOT/'iteration101';PREVIOUS=ROOT/'iteration100'


def public101(data,ids,anchors,block,replacements):
    base=ag.public_sentences([dict(sent_id=sid,**data[sid]) for sid in ids],anchors,'testlength100-'+block)
    return base,perturb(base,replacements,anchors)


def run():
    assert not OUT.exists();OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text());paths=[Path(__file__),Path('src/voynich_smt/anchor_merge_diagnostic.py'),Path('src/voynich_smt/paired_anchor_class.py'),ROOT/'iteration44/annotations-truth.json',ROOT/'iteration85/anchor-budgets.json',ROOT/'iteration93/models.json',ROOT/'iteration95/policies.json',ROOT/'iteration98/calibration-bank.json',PREVIOUS/'verification-manifest.json',PREVIOUS/'blocks.json',PREVIOUS/'core.json',PREVIOUS/'availability.json']
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='DIAGNOSTIC only of100mergefailures, no algorithmreplacement/exblacklist/retuning. Frozen93classifier/95cut/core8/countgate. Both200merges andALL15coreerrors+3controls, notonlybadcase. Eligibilityfactorial: evidenceleft100/right100/merged200 x candidateeligibilityleft/right/intersection/union determinedONLYuncorruptedpubliccounts; overridegatewithchosenfixedset, absenttypesneverfabricated. Override diagnostic notvalidoperationalpolicy. Same15errorspluscontrols alwaysreported; secondarysameintersectionendpointerrorsstratum. Cached100scalarpairgains usedfactorial, no newmodels. Exactpairtraces forallcoreADPxCCONJpairs/18cases/ALL9sourceblocks (162scenarios), both typesjointmasked; endpointmeans,countweightedgroupmeans,exoccurrenceprobabilitiesandlinearfeaturelogitcontributions. Allcorepairs traced, referenceonlyaftergeneration. Verifyper-occurrencefeatures/q unchanged parenttomerged; verifymergedmeansweightedreconstruction. Secondaryequal100parentprobabilityweight counterfactual onboth200merges, fixedeligibilityunion/intersection; diagnosticnotselectedpolicy. Compareallcases, no targetpickedexceptions; featuredecomposition isofoccurrencelogits, NOT additive decompositionofnonlinearpooledpairgain. No PPintegration, authorqueries,newannotations,reserve/sealedtest. Reuseddevelopmentfailurelocalization,notfreshconfirmation.'))
    data=load(ROOT/'iteration44/annotations-truth.json');anchors=load(ROOT/'iteration85/anchor-budgets.json')['195'];core=load(PREVIOUS/'core.json');blocks=load(PREVIOUS/'blocks.json');availability=load(PREVIOUS/'availability.json');bank={case:m for case,m in load(ROOT/'iteration98/calibration-bank.json').items() if not case.startswith('swap_') or set(m)<=set(core)};assert len(bank)==18;cut=load(ROOT/'iteration95/policies.json')['joint_context']['threshold'];model=load(ROOT/'iteration93/models.json')['context'];groups={sid:'100-'+str(i) for i in range(4) for sid in blocks['100-'+str(i)]};factorial={};traces={};summary={}
    for merge in range(2):
        left='100-'+str(2*merge);right='100-'+str(2*merge+1);merged='200-'+str(merge);sets=eligibility_sets(availability[left]['core_supported'],availability[right]['core_supported']);save(OUT/(merged+'-eligibility.json'),sets)
        for view in (left,right,merged):
            base,_=public101(data,blocks[view],anchors,view,{});inverse={t['id']:t['anchor'] for s in base for t in s['tokens'] if t['anchor'] in core}
            for case,replacements in bank.items():
                scores=load(PREVIOUS/view/(case+'.json'))['scores'];ref=reference_for(base,replacements,case.startswith('swap_'),scores,core);arms={}
                for gate,allowed in sets.items():
                    selected_scores=eligible_pairs(scores,allowed,inverse);row=curve_metrics(selected_scores,ref,cut);arms[gate]=dict(all=row,common=row if not ref['error'] or set(replacements)<=set(sets['intersection']) else None)
                factorial[merged+'/'+view+'/'+case]=arms
    for block,ids in blocks.items():
        folder=OUT/block;folder.mkdir();base,_=public101(data,ids,anchors,block,{});lookup={t['anchor']:t['id'] for s in base for t in s['tokens'] if t['anchor'] in core};inverse={v:k for k,v in lookup.items()};ex_id=lookup.get('ex')
        for case,replacements in bank.items():
            _,public=public101(data,ids,anchors,block,replacements);proposed={t['id']:t['tag'] for s in public for t in s['tokens'] if t['id'] in inverse};cached=load(PREVIOUS/block/(case+'.json'))['scores'];pairs=[r for r in cached if set(r['pair'])<=set(inverse)];rows=[]
            for p in pairs:
                trace=trace_pair(public,p['pair'],proposed,model,ex_id,groups);assert math.isclose(trace['gain'],p['gain'],rel_tol=1e-10,abs_tol=1e-12);trace['supported']=p['supported'];rows.append(trace)
            path=folder/(case+'.json');save(path,dict(traces=rows,identities=inverse));save(folder/(case+'.freeze.json'),dict(inputs={str(path):digest(path)}));traces[block+'/'+case]=rows
        print('traced',block,flush=True)
    # Same-view alternative pooling; the inference core is not reselected.
    equal={}
    for merge in range(2):
        block='200-'+str(merge);sets=load(OUT/(block+'-eligibility.json'));base,_=public101(data,blocks[block],anchors,block,{});inverse={t['id']:t['anchor'] for s in base for t in s['tokens'] if t['anchor'] in core}
        for case,replacements in bank.items():
            rows=traces[block+'/'+case];scores=[dict(pair=t['pair'],gain=equal_group_gain(t),supported=t['supported']) for t in rows];ref=reference_for(base,replacements,case.startswith('swap_'),scores,core);equal[block+'/'+case]={gate:curve_metrics(eligible_pairs(scores,allowed,inverse),ref,cut) for gate,allowed in sets.items()}
    for key,arms in factorial.items():
        merge,view,case=key.split('/')
        for gate,values in arms.items():
            for stratum,row in values.items():
                if row is not None:summary.setdefault(merge+'/'+view+'/'+gate+'/'+stratum,[]).append(row)
    save(OUT/'factorial.json',factorial);save(OUT/'factorial-summary.json',{k:aggregate(v) for k,v in summary.items()});save(OUT/'equal-parent.json',equal);save(OUT/'run-summary.json',dict(trace_scenarios=len(traces),factorial_scenarios=len(factorial),equal_parent_scenarios=len(equal)))
if __name__=='__main__':run()
