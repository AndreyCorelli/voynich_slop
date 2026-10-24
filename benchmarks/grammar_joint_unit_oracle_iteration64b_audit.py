"""Replay all fixed oracle constraints and joint decisions from frozen inputs."""
from benchmarks.grammar_joint_unit_oracle_iteration64b import *


def run():
    hashes=0
    for name in ('design-freeze.json','prediction-freeze.json'):
        for p,h in load(OUT/name)['inputs'].items():assert digest(p)==h,p;hashes+=1
    data=load(SOURCE);parts=load(MORPH/'manifest.json')['partitions'];folds={sid:str(f) for f in range(5) for sid in parts[str(f)]['test']};models=load(UNIT/'models.json');prior=load(UNIT/'frame-predictions.json');rows=load(OUT/'frame-predictions.json');lookup={(r['sid'],r['subject']):r for r in rows};by_sid=defaultdict(list)
    for r in prior:
        assert all(lookup[(r['sid'],r['subject'])][k]==v for k,v in r.items());by_sid[r['sid']].append(r)
    gold_records={(r['sid'],r['gold'][0]):r for r in load(OUT/'gold-feasibility.json')};candidate_records={(r['sid'],r['gold'][0]):r for r in load(OUT/'copular-candidates.json')};predictions=typed_checks=feasibility_checks=candidate_checks=0
    for sid,old in by_sid.items():
        tokens=data[sid]['tokens'];ctx=context(tokens);w=np.asarray(models[folds[sid]]['model']['weights']);gold_frames=make_frames(old,tokens,w,'oracle');assigned={r['subject'] for r in gold_frames}
        for arm,config in ARMS.items():
            for frames,field in ((gold_frames,'joint_oracle_endpoint'),(make_frames(old,tokens,w,'pipeline'),'joint_pipeline')):
                allowed=allowed_indices(frames,tokens,ctx,config);actual,_=decode(frames,allowed,config.get('shared',False))
                for r in frames:
                    assert actual[r['subject']]==lookup[(sid,r['subject'])][field][arm];predictions+=1
                if field=='joint_oracle_endpoint':
                    domains=feasible_domains(frames,allowed,config.get('shared',False))
                    for r in frames:
                        g=r['gold'];saved=gold_records[(sid,r['subject'])]['arms'][arm]
                        assert saved==dict(local_reasons=reasons(r,tuple(g[1::2]),tokens,ctx,config,assigned),gold_feasible=tuple(g[1::2]) in domains[r['subject']]);feasibility_checks+=1
                        if g[3]=='cop':
                            saved_candidates=candidate_records[(sid,r['subject'])]['candidates']
                            for c in saved_candidates:
                                assert c['kept'][arm]==((c['head'],'cop') in domains[r['subject']]);assert c['score']==float(r['scores'][r['options'].index((c['head'],'cop'))]);candidate_checks+=1
                    typed={r['subject']:[j for j in allowed[r['subject']] if r['options'][j][1]==r['gold'][3]] for r in frames};actual,_=decode(frames,typed,config.get('shared',False))
                    for r in frames:assert actual[r['subject']]==lookup[(sid,r['subject'])]['joint_true_type'][arm];typed_checks+=1
    assert evaluate(rows)==load(OUT/'evaluation.json')
    assert summarize_feasibility(load(OUT/'gold-feasibility.json'),load(OUT/'copular-candidates.json'),load(OUT/'sentence-audit.json'))==load(OUT/'feasibility-summary.json')
    paired={}
    for arm in ARMS:
        if arm=='baseline':continue
        counts=Counter()
        for r in rows:
            if r['carrier_ambiguous']:continue
            a=r['joint_pipeline']['baseline'];b=r['joint_pipeline'][arm];g=r['unit_gold']
            if a!=b:
                counts['changed']+=1
                if g is not None and a==g:counts['lost_exact']+=1
                if g is not None and b==g:counts['gained_exact']+=1
        paired[arm]=dict(counts)
    save(OUT/'additional-audit.json',dict(paired=paired));save(OUT/'independent-validation.json',dict(freeze_hashes=hashes,decision_replays=predictions,true_type_replays=typed_checks,feasibility_replays=feasibility_checks,candidate_replays=candidate_checks,prior_fields_unchanged=True,evaluation_replayed=True,reserve_unscored=200,prior_queries_scored=0));print('Audit passed',predictions,typed_checks,feasibility_checks,candidate_checks,paired)
if __name__=='__main__':run()
