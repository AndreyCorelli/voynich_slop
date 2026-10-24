"""Cross-fit attachment probability features while freezing candidate retrieval."""
from pathlib import Path
from collections import defaultdict
import copy,math
from benchmarks.grammar_none_gate_iteration53 import OUT as PREVIOUS,MORPH,SOURCE,EXAMPLES,RESERVE,load,save,digest,prepare,make_frames,metrics
from benchmarks.grammar_multi_link_attachment_iteration52 import add_targets
from voynich_smt.factor_morphology import fit as fit_morph,target
from voynich_smt.multi_link_attachment import fit as fit_attachment
from voynich_smt.crossfit_morphology import inner_plan,sentence_fold,probability_map,replace_probabilities
from voynich_smt.none_gate import best_edge,accept,calibrate
OUT=PREVIOUS.parent/'iteration54'
VARIANTS=('inner_exposed','crossfit')
ARMS=tuple(variant+'_'+mode for variant in VARIANTS for mode in ('map','free'))


def training_frames(ids,data,outer,plan,inner_models):
    frames={v:[] for v in VARIANTS};cache={};probability_caches=defaultdict(dict);diagnostics=defaultdict(lambda:dict(n=0,nll=0.,brier=0.));invariance=0
    for sid in ids:
        tokens=data[sid]['tokens'];base=add_targets(make_frames(sid,tokens,outer,cache)[0],tokens);g=str(sentence_fold(sid));record=plan[g];probabilities={}
        for variant in VARIANTS:
            excluded=record['crossfit_excluded' if variant=='crossfit' else 'exposed_excluded'];model=inner_models[str(excluded)];p=probability_map(tokens,model,probability_caches[str(excluded)]);probabilities[variant]=p;revised=replace_probabilities(base,tokens,p)
            assert [(r['sid'],r['subject'],r['predicates'],r['gold'],r['vectors']['structural']) for r in revised]==[(r['sid'],r['subject'],r['predicates'],r['gold'],r['vectors']['structural']) for r in base];invariance+=1
            frames[variant].extend(revised)
        probabilities['outer_insample']=probability_map(tokens,outer['model'],probability_caches['outer'])
        for i,t in enumerate(tokens):
            y=target(t,'role','expanded')
            if y is None:continue
            for variant,values in probabilities.items():
                p=values[i]['role'][1];r=diagnostics[variant];r['n']+=1;r['nll']-=math.log(max(1e-12,p if y=='YES' else 1-p));r['brier']+=(p-(y=='YES'))**2
    return frames,{v:dict(n=r['n'],mean_nll=r['nll']/r['n'],mean_brier=r['brier']/r['n']) for v,r in diagnostics.items()},invariance


def run():
    assert not OUT.exists()
    previous=load(PREVIOUS/'verification-manifest.json')
    for p,h in previous['inputs'].items():assert digest(p)==h,p
    OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),Path('src/voynich_smt/crossfit_morphology.py'),Path('src/voynich_smt/factor_morphology.py'),Path('src/voynich_smt/multi_link_attachment.py'),Path('src/voynich_smt/none_gate.py'),SOURCE,EXAMPLES,RESERVE,MORPH/'models.json',MORPH/'manifest.json',PREVIOUS/'frame-predictions.json',PREVIOUS/'verification-manifest.json',OUT/'proposal-design.md']
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},scope='Same4070 source/outer folds,304 selected sentences470 edges326 references. Readable Latin/oracle POS retained. No reserve or prior query evaluation.',crossfit='Outer fit has three original sentence folds sorted ascending. Train three expanded morphology probability models each excluding one fit fold. For fit sentence in foldg, crossfit uses model excludingg; inner_exposed uses model excluding next fit fold cyclically and therefore includesg. Same three two-fold models reused in both arms; fold sizes differ slightly, so size matching is approximate. Sentence-level exclusion, not word-type exclusion.',fixed='All candidates still come from frozen outer49 model/policies and50 fallback. Only last4 local_morph probability features change on attachment fit sentences; structural/localPOS features unchanged. Outer calibration/test probability features unchanged. Fixed attachment L2/optimizer from52; no tuning. No inner conformal calibration since only probabilities change. Frozen candidate policies already use outer calibration labels as in52; this is not full-pipeline cross-fitting.',evaluation='Refit local_morph attachment for exposed/crossfit; recalibrate53 MAP/free margin policies on outer calibration only using unchanged grids/F1/precision90 objectives. Compare frozen53 baseline. No new hyperparameters or target-based selection.'))
    data=load(SOURCE);parts=load(MORPH/'manifest.json')['partitions'];morphs=load(MORPH/'models.json');reserve={r['sent_id'] for rs in load(RESERVE)['authors'].values() for r in rs};assert not set(data)&reserve
    plans={};inner_models={}
    for f in range(5):
        part=parts[str(f)];a,b,c=(set(part[k]) for k in ('fit','calibration','test'));assert not (a&b or a&c or b&c);plan=inner_plan(part['fit']);plans[str(f)]=plan;inner_models[str(f)]={}
        for excluded in plan:
            ids=[sid for sid in part['fit'] if sentence_fold(sid)!=int(excluded)];assert set(ids)<=a and not set(ids)&(b|c)
            inner_models[str(f)][excluded]=fit_morph((data[sid]['tokens'] for sid in ids),'expanded')
        for g,r in plan.items():
            held=set(r['held_ids']);excluded=r['crossfit_excluded'];fitids={sid for sid in a if sentence_fold(sid)!=excluded};assert not held&fitids
            exposed={sid for sid in a if sentence_fold(sid)!=r['exposed_excluded']};assert held<=exposed
    save(OUT/'inner-plans.json',plans);save(OUT/'inner-morphology-models.json',inner_models);save(OUT/'inner-fit-freeze.json',dict(inputs={str(p):digest(p) for p in OUT.glob('*.json')}));models={};diagnostics={};invariance_checks=0
    for f in range(5):
        part=parts[str(f)];outer=morphs[str(f)]['expanded'];frames,diagnostic,checks=training_frames(part['fit'],data,outer,plans[str(f)],inner_models[str(f)]);diagnostics[str(f)]=diagnostic;invariance_checks+=checks;cal=prepare(part['calibration'],data,outer,{});models[str(f)]={}
        for variant in VARIANTS:
            model=fit_attachment(frames[variant],'local_morph');proposals=[best_edge(frame,model) for frame in cal];policies={mode:calibrate(cal,proposals,mode) for mode in ('map','free')};models[str(f)][variant]=dict(model=model,policies=policies)
        print('Fit/calibrated',f,{v:dict(cutoff=models[str(f)][v]['policies']['free']['f1']['cutoff'],cal_f1=models[str(f)][v]['policies']['free']['f1']['f1']) for v in VARIANTS},flush=True)
    save(OUT/'models.json',models);save(OUT/'training-role-diagnostics.json',diagnostics);save(OUT/'model-freeze.json',dict(inputs={str(p):digest(p) for p in OUT.glob('*.json')}))
    prior=load(PREVIOUS/'frame-predictions.json');lookup={(r['sid'],r['subject']):r for r in prior};rows=[];mutation_checks=0
    for f in range(5):
        outer=morphs[str(f)]['expanded'];cache={}
        for sid in parts[str(f)]['test']:
            tokens=data[sid]['tokens'];frames,_=make_frames(sid,tokens,outer,cache)
            if any(lookup[sid,frame['subject']]['selected_sentence'] for frame in frames):
                masked=[dict(t,features={},head=None,rel='?',lemma='?') for t in tokens];other,_=make_frames(sid,masked,outer,cache);assert frames==other;mutation_checks+=1
            for frame in frames:
                r=copy.deepcopy(lookup[sid,frame['subject']]);assert r['candidate_predicates']==frame['predicates'];r['crossfit_proposals']={}
                for variant in VARIANTS:
                    record=models[str(f)][variant];proposal=best_edge(frame,record['model']);r['crossfit_proposals'][variant]=proposal
                    for mode in ('map','free'):
                        r['arms'][variant+'_'+mode]={policy:proposal['predicate'] if accept(proposal,record['policies'][mode][policy]['cutoff']) else None for policy in ('f1','precision90')}
                rows.append(r)
    save(OUT/'frame-predictions.json',rows);save(OUT/'prediction-freeze.json',dict(inputs={str(p):digest(p) for p in OUT.glob('*.json')}));result={};references={};paired={}
    for scope in ('selected_sentences','all_source','Cicero_selected','Palladius_selected'):
        chosen=[r for r in rows if scope=='all_source' or r['selected_sentence'] and (scope=='selected_sentences' or r['author']==scope.split('_')[0])]
        for arm in ARMS:
            for policy in ('f1','precision90'):result[scope+'/'+arm+'/'+policy]=metrics(chosen,arm,policy)
        for control in ('local_morph_free','inner_exposed_free'):
            counts=dict(correct_added=0,correct_removed=0,wrong_added=0,wrong_removed=0)
            for r in chosen:
                a=r['arms'][control]['f1'];b=r['arms']['crossfit_free']['f1'];gold=r['gold'];ac=a is not None and a==gold;bc=b is not None and b==gold;aw=a is not None and a!=gold;bw=b is not None and b!=gold
                counts['correct_added']+=bc and not ac;counts['correct_removed']+=ac and not bc;counts['wrong_added']+=bw and not aw;counts['wrong_removed']+=aw and not bw
            paired[scope+'/crossfit_vs_'+control]=counts
    for arm in ARMS:
        for policy in ('f1','precision90'):
            chosen=[r for r in rows if r['selected_reference'] is not None];references[arm+'/'+policy]=dict(n=len(chosen),correct=sum(r['arms'][arm][policy]==r['selected_reference'] for r in chosen),wrong=sum(r['arms'][arm][policy] is not None and r['arms'][arm][policy]!=r['selected_reference'] for r in chosen),abstained=sum(r['arms'][arm][policy] is None for r in chosen))
    save(OUT/'evaluation.json',dict(edges=result,selected_references=references,paired=paired,baseline=str(PREVIOUS/'evaluation.json')));save(OUT/'validation.json',dict(previous_hashes=len(previous['inputs']),inner_morphology_models=15,attachment_models=10,fit_sentence_candidate_structural_invariance_checks=invariance_checks,selected_sentence_inference_mutation_checks=mutation_checks,partitions_disjoint=True,inner_crossfit_excludes_scored_sentences=True,outer_test_calibration_not_used_in_inner_probability_fits=True,reserve_unscored=200,prior_queries_scored=0))
    for k,r in result.items():
        if k.startswith('selected_sentences/'):print(k,r)
    print('References',references)
if __name__=='__main__':run()
