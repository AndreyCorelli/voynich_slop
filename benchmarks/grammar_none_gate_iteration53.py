"""Calibrate the NONE decision on frozen iteration52 models, with a MAP control."""
from pathlib import Path
import copy
from benchmarks.grammar_multi_link_attachment_iteration52 import OUT as PREVIOUS,MORPH,SOURCE,EXAMPLES,RESERVE,load,save,digest,prepare,make_frames,metrics
from voynich_smt.multi_link_attachment import propose
from voynich_smt.none_gate import best_edge,accept,calibrate
OUT=PREVIOUS.parent/'iteration53'
BASES=('structural','local_morph')
ARMS=tuple(base+'_'+mode for base in BASES for mode in ('map','free'))


def run():
    assert not OUT.exists()
    previous=load(PREVIOUS/'verification-manifest.json')
    for p,h in previous['inputs'].items():assert digest(p)==h,p
    OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),Path('src/voynich_smt/none_gate.py'),SOURCE,EXAMPLES,RESERVE,MORPH/'models.json',MORPH/'manifest.json',PREVIOUS/'models.json',PREVIOUS/'frame-predictions.json',PREVIOUS/'verification-manifest.json',OUT/'proposal-design.md']
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},scope='Same4070 source sentences,304 selected sentences,470 finite-subject edges and326 references as52. Same models/candidates/vectors, no refitting. No reserve/prior queries; readable Latin and supplied POS.',score='Unique best edge score minus fixed NONE score0. Edge ties abstain. Accept when margin>cutoff+1e-10. MAP control restricts cutoffs>=0; free includes negative cutoffs. Old52 probability-gated policies retained as frozen comparison.',calibration='Fixed grid -1000000,-8,-6,-4,-3,-2,-1.5,-1,-.5,0,.5,1,1.5,2,3,4,6,8,1000000. Outer calibration sentences only. Choose maximum microF1 (ties fewer predictions) or maxTP subject to empirical precision>=90% and>=20 predictions; no qualifying cutoff => abstain. No new model or target-based selection.'))
    data=load(SOURCE);parts=load(MORPH/'manifest.json')['partitions'];morphs=load(MORPH/'models.json');models=load(PREVIOUS/'models.json');reserve={r['sent_id'] for rs in load(RESERVE)['authors'].values() for r in rs};assert not set(data)&reserve;policies={}
    for f in range(5):
        p=parts[str(f)];assert not (set(p['fit'])&set(p['calibration']) or set(p['fit'])&set(p['test']) or set(p['calibration'])&set(p['test']));frames=prepare(p['calibration'],data,morphs[str(f)]['expanded'],{});policies[str(f)]={}
        for base in BASES:
            proposals=[best_edge(frame,models[str(f)][base]['model']) for frame in frames]
            for mode in ('map','free'):policies[str(f)][base+'_'+mode]=calibrate(frames,proposals,mode)
            assert policies[str(f)][base+'_free']['f1']['f1']>=policies[str(f)][base+'_map']['f1']['f1']
        print('Calibrated',f,{a:r['f1']['cutoff'] for a,r in policies[str(f)].items()},flush=True)
    save(OUT/'policies.json',policies);save(OUT/'policy-freeze.json',dict(inputs={str(p):digest(p) for p in OUT.glob('*.json')}))
    previous_rows=load(PREVIOUS/'frame-predictions.json');old={(r['sid'],r['subject']):r for r in previous_rows};output=[];mutation_checks=0;map_replays=0
    for f in range(5):
        cache={};morph=morphs[str(f)]['expanded']
        for sid in parts[str(f)]['test']:
            tokens=data[sid]['tokens'];frames,_=make_frames(sid,tokens,morph,cache)
            if any(old[sid,frame['subject']]['selected_sentence'] for frame in frames):
                masked=[dict(t,features={},head=None,rel='?',lemma='?') for t in tokens];other,_=make_frames(sid,masked,morph,cache);assert frames==other;mutation_checks+=1
            for frame in frames:
                r=copy.deepcopy(old[sid,frame['subject']]);assert r['candidate_predicates']==frame['predicates'];r['margins']={}
                for base in BASES:
                    proposal=best_edge(frame,models[str(f)][base]['model']);original=propose(frame,models[str(f)][base]['model']);assert original==r['proposals'][base]
                    assert (proposal['predicate'] if accept(proposal,0) else None)==original['predicate'];map_replays+=1;r['margins'][base]=proposal
                    for mode in ('map','free'):
                        arm=base+'_'+mode;r['arms'][arm]={policy:proposal['predicate'] if accept(proposal,policies[str(f)][arm][policy]['cutoff']) else None for policy in ('f1','precision90')}
                output.append(r)
    save(OUT/'frame-predictions.json',output);save(OUT/'prediction-freeze.json',dict(inputs={str(p):digest(p) for p in OUT.glob('*.json')}));result={};references={};paired={}
    for scope in ('selected_sentences','all_source','Cicero_selected','Palladius_selected'):
        selected=[r for r in output if scope=='all_source' or r['selected_sentence'] and (scope=='selected_sentences' or r['author']==scope.split('_')[0])]
        for arm in ARMS:
            for policy in ('f1','precision90'):result[scope+'/'+arm+'/'+policy]=metrics(selected,arm,policy)
        for base in BASES:
            for control in (base,base+'_map'):
                for policy in ('f1','precision90'):
                    counts=dict(correct_added=0,correct_removed=0,wrong_added=0,wrong_removed=0,attached_added=0,attached_removed=0)
                    for r in selected:
                        a=r['arms'][control][policy];b=r['arms'][base+'_free'][policy];gold=r['gold'];ac=a is not None and a==gold;bc=b is not None and b==gold;aw=a is not None and a!=gold;bw=b is not None and b!=gold
                        counts['correct_added']+=bc and not ac;counts['correct_removed']+=ac and not bc;counts['wrong_added']+=bw and not aw;counts['wrong_removed']+=aw and not bw;counts['attached_added']+=a is None and b is not None;counts['attached_removed']+=a is not None and b is None
                    paired[scope+'/'+base+'_free_vs_'+control+'/'+policy]=counts
    rows=[r for r in output if r['selected_reference'] is not None]
    for arm in ARMS:
        for policy in ('f1','precision90'):references[arm+'/'+policy]=dict(n=len(rows),correct=sum(r['arms'][arm][policy]==r['selected_reference'] for r in rows),wrong=sum(r['arms'][arm][policy] is not None and r['arms'][arm][policy]!=r['selected_reference'] for r in rows),abstained=sum(r['arms'][arm][policy] is None for r in rows))
    save(OUT/'evaluation.json',dict(edges=result,selected_references=references,paired=paired,baseline=str(PREVIOUS/'evaluation.json')));save(OUT/'validation.json',dict(previous_hashes=len(previous['inputs']),models_refitted=0,zero_cutoff_MAP_replays=map_replays,selected_sentence_inference_mutation_checks=mutation_checks,partitions_disjoint=True,reserve_unscored=200,prior_queries_scored=0))
    for k,r in result.items():
        if k.startswith('selected_sentences/'):print(k,r)
    print('Selected references',references)
if __name__=='__main__':run()
