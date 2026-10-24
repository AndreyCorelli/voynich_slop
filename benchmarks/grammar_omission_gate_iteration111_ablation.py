"""Post-fit component attribution: disable only the fixed stability requirement."""
from benchmarks.grammar_omission_gate_iteration111 import *
from voynich_smt.combined_repair_gate import select as select_gate


def run():
    paths=[Path(__file__),OUT/'policies.json',OUT/'routing.json',OUT/'actions.json',SOURCE/'cases.json',PREVIOUS/'pair-cases.json',OLD/'routes.json']
    save(OUT/'ablation-inputs.json',dict(inputs={str(p):digest(p) for p in paths},scope='POSTFIT descriptiveablationonly: disablefullpolicystabilitycut, keepgain/gap/routingandshortOFF. No refit/defaultselection/generalbootstrapclaim.'))
    policies=load(OUT/'policies.json');bands=load(OUT/'routing.json');ablated=dict(policies,full=dict(policies['full'],stability=0.));source=load(SOURCE/'cases.json');targets=load(PREVIOUS/'pair-cases.json');sizes={v:r['sentences'] for v,r in load(OLD/'routes.json').items()};author_actions=load(OUT/'actions.json');source_diff=[];author_diff=[]
    for r in source:
        before=select_gate(r['features'],policies['full']);after=select_gate(r['features'],ablated['full'])
        if before!=after:source_diff.append(dict(case=r['case'],omitted_word=r['omitted_word'],before=before,after=after))
    for r in targets:
        key=r['block']+'/'+r['case'];before=select_conditional(r['features'],sizes[r['block']],policies,bands);after=select_conditional(r['features'],sizes[r['block']],ablated,bands);assert before==author_actions[key]
        if before!=after:author_diff.append(dict(case=key,before=before,after=after))
    save(OUT/'stability-ablation.json',dict(source_views=len(source),author_views=len(targets),source_action_changes=source_diff,author_action_changes=author_diff,thresholds_refit=False,default_changed=False,interpretation='Atthisfixedoperatingpointgain/gapalonegiveidenticalknown-source/authoractions. Stabilitytestnotresponsiblefortheseoutcomes; no claimofequivalenceonnewinputs.'))
    print(load(OUT/'stability-ablation.json'))
if __name__=='__main__':run()
