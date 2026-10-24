"""Oracle feasibility and exact shared-carrier decoding of frozen unit scores."""
from pathlib import Path
from collections import Counter,defaultdict
import copy
import numpy as np
from benchmarks.grammar_typed_predicate_units_iteration57 import OUT as UNIT,MORPH,SOURCE,EXAMPLES,RESERVE,load,save,digest
from benchmarks.grammar_structural_head_evidence_iteration63 import OUT as PREVIOUS
from voynich_smt.typed_predicate_units import ROLES,choices,matrix
from voynich_smt.joint_unit_oracle import ARMS,context,reasons,allowed_indices,decode,shared_gold_conflicts
from voynich_smt.multi_link_attachment import edge_metrics
OUT=PREVIOUS.parent/'iteration64'


def make_frames(old_rows,tokens,weights,field):
    frames=[]
    for old in old_rows:
        if old['carrier_ambiguous']:continue
        gold=old['unit_gold'];v=old['arms']['carrierfit_carriercal']['f1'] if field=='pipeline' else gold[2] if gold else None
        if v is None:continue
        s=old['subject'];options=choices(tokens,s,v)
        frames.append(dict(subject=s,carrier=v,options=options,scores=matrix(tokens,s,v,options)@weights,gold=gold))
    return frames


def feasible_domains(frames,allowed,shared):
    domains={r['subject']:{r['options'][j] for j in allowed[r['subject']]} for r in frames}
    if shared:
        groups=defaultdict(list)
        for r in frames:groups[r['carrier']].append(r['subject'])
        for subjects in groups.values():
            common=set.intersection(*(domains[s] for s in subjects))
            for s in subjects:domains[s]=common
    return domains


def evaluate(rows):
    metrics={};per_role={};conditional={};true_type={}
    for scope in ('all_source','selected_sentences','Cicero_selected','Palladius_selected'):
        chosen=[r for r in rows if not r['carrier_ambiguous'] and (scope=='all_source' or r['selected_sentence'] and (scope=='selected_sentences' or r['author']==scope.split('_')[0]))];gold={(r['sid'],*r['unit_gold']) for r in chosen if r['unit_gold'] is not None}
        for arm in ARMS:
            pred={(r['sid'],*r['joint_pipeline'][arm]) for r in chosen if r['joint_pipeline'][arm] is not None};metrics[scope+'/'+arm]=edge_metrics(gold,pred)
            for role in ROLES:
                per_role[scope+'/'+arm+'/'+role]=edge_metrics({u for u in gold if u[-1]==role},{u for u in pred if u[-1]==role})
            for role in ('all',)+ROLES:
                positive=[r for r in chosen if r['unit_gold'] is not None and (role=='all' or r['unit_gold'][3]==role)]
                for field,record in (('joint_oracle_endpoint',conditional),('joint_true_type',true_type)):
                    record[scope+'/'+arm+'/'+role]=dict(n=len(positive),exact=sum(r[field][arm]==r['unit_gold'] for r in positive))
    return dict(unit_metrics=metrics,per_role=per_role,oracle_endpoint_accuracy=conditional,true_endpoint_and_type_accuracy=true_type)


def summarize_feasibility(records,candidates,sentence_audits):
    result={};competition={}
    for arm in ARMS:
        for role in ('all',)+ROLES:
            subset=[r for r in records if role=='all' or r['gold'][3]==role];bad=[r for r in subset if not r['arms'][arm]['gold_feasible']];counts=Counter(reason for r in subset for reason in r['arms'][arm]['local_reasons'])
            result[arm+'/'+role]=dict(n=len(subset),gold_kept=len(subset)-len(bad),local_reasons=dict(counts),excluded=[[r['sid'],r['gold'][0]] for r in bad])
        counts=Counter()
        for r in candidates:
            g=next(c for c in r['candidates'] if c['head']==r['gold'][1]);counts['frames']+=1;counts['gold_kept']+=g['kept'][arm]
            for c in r['candidates']:
                if c is g:continue
                counts['wrong_candidates']+=1;counts['wrong_blocked']+=not c['kept'][arm]
                if c['score']>g['score']+1e-10:
                    counts['baseline_outrankers']+=1;counts['outrankers_blocked']+=not c['kept'][arm]
                    counts['outrankers_blocked_preserving_gold']+=g['kept'][arm] and not c['kept'][arm]
        competition[arm]=dict(counts)
    sharing=Counter()
    for r in sentence_audits:
        for group in r['gold_groups']:
            sharing['carrier_groups']+=1;sharing['multiple_subject_groups']+=len(group['subjects'])>1
            if len(group['subjects'])>1:
                sharing['multiple_subject_units']+=len(group['subjects']);sharing['multiple_subject_cop_units']+=sum(u[3]=='cop' for u in group['units']);sharing['coordinated_multiple_subject_groups']+=group['one_coordination_component']
        sharing['coordinated_subject_units']+=len(r['coordinated_subjects'])
        sharing['shared_gold_conflict_groups']+=len(r['shared_gold_conflicts'])
    return dict(gold_feasibility=result,copular_competition=competition,sharing=dict(sharing),warning='Annotation/morphology arms are oracle diagnostics. True endpoints/types are supplied only in explicitly conditional outputs. This is a restricted shared-carrier joint model, not a full parse decoder.')


def run():
    assert not OUT.exists()
    previous=load(PREVIOUS/'verification-manifest.json')
    for p,h in previous['inputs'].items():assert digest(p)==h,p
    OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),Path('benchmarks/grammar_joint_unit_oracle_iteration64_audit.py'),Path('src/voynich_smt/joint_unit_oracle.py'),Path('src/voynich_smt/copular_head_oracle.py'),Path('src/voynich_smt/typed_predicate_units.py'),Path('src/voynich_smt/predicate_carriers.py'),Path('tests/test_joint_unit_oracle.py'),SOURCE,EXAMPLES,RESERVE,MORPH/'manifest.json',UNIT/'models.json',UNIT/'frame-predictions.json',UNIT/'evaluation.json',UNIT/'verification-manifest.json',PREVIOUS/'verification-manifest.json',OUT/'proposal-design.md']
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},arms=ARMS,scope='Same4070 source sentences/five frozen57 models,3365 goldunits519 selected; no training or calibration. Existing56 endpoints fixed. Same unique-carrier task; ambiguous frame excluded from joint groups and evaluation. Reserve200 remainsunscored; no prior queries.',constraints='Shared: all active subjects assigned to one carrier share one(head,type), exact sum of frozen logits over intersected domains, mandatory frames; empty domains/ties abstain whole group. Assigned roles: head cannot also be another active subject globally (observable), or in same gold clause (oracle). Gold role: nominal source nsubj including subtype roles in same gold clause. Global role exclusion intentionally challenges embedding; no case/PP restriction. Unary phrase/clause uses58 annotation masks.',agreement='SV Number/Person intersects known feature sets; unknown passes, NOUN/PROPN missingPerson defaults3. Adjectival copular head Number/Gender/Case agreement only; predicate nouns unrestricted. Strict vscoord-permissive: goldconjcomponent adds Plur and highest-priority knownPerson to root alternatives, leaves rootNumber possible, suppressesGender restriction for coordinated subjects. This is permissive allowance, not full Latin agreement resolution. Case remainschecked. Gold morphology at all endpoints; oracleonly.',diagnostics='First measure goldtarget survival, sharedhead consistency, multiple-subject groups and coordination. Naive one-subject-percarrier diagnosed only, not imposed. At gold endpoints and actual predicted endpoints decode all fixed arms, plus true-type diagnostic. On650copunits measure local/extendable candidate feasibility and blocking of baseline outrankers. Compare unary phraseclause toincremental joint gain. Never choose arm/threshold by test outcome. Only baseline/shared/assigned_global use no extra annotations beyond existing POS; remaining arms explicitly oracle.'))
    data=load(SOURCE);parts=load(MORPH/'manifest.json')['partitions'];folds={sid:str(f) for f in range(5) for sid in parts[str(f)]['test']};models=load(UNIT/'models.json');old_rows=load(UNIT/'frame-predictions.json');by_sid=defaultdict(list)
    for r in old_rows:by_sid[r['sid']].append(r)
    reserve={r['sent_id'] for rs in load(RESERVE)['authors'].values() for r in rs};assert not set(data)&reserve
    rows=[];feasibility=[];candidates=[];sentence_audits=[];stats={};replays=mutations=0
    for sid in sorted(by_sid):
        tokens=data[sid]['tokens'];ctx=context(tokens);weights=np.asarray(models[folds[sid]]['model']['weights']);old=by_sid[sid];copies={r['subject']:copy.deepcopy(r) for r in old}
        for r in copies.values():
            for field in ('joint_pipeline','joint_oracle_endpoint','joint_true_type'):r[field]={a:None for a in ARMS}
        gold_frames=make_frames(old,tokens,weights,'oracle');pipeline=make_frames(old,tokens,weights,'pipeline');gold_assigned={r['subject'] for r in gold_frames};gold_results={r['subject']:dict(sid=sid,gold=r['gold'],arms={}) for r in gold_frames};cop_candidates={}
        for r in gold_frames:
            if r['gold'][3]=='cop':cop_candidates[r['subject']]=dict(sid=sid,gold=r['gold'],selected_sentence=copies[r['subject']]['selected_sentence'],candidates=[dict(head=h,score=float(r['scores'][j]),kept={}) for j,(h,role) in enumerate(r['options']) if role=='cop'])
        for arm,config in ARMS.items():
            for frames,field in ((gold_frames,'joint_oracle_endpoint'),(pipeline,'joint_pipeline')):
                allowed=allowed_indices(frames,tokens,ctx,config);predictions,counts=decode(frames,allowed,config.get('shared',False))
                for key,value in counts.items():stats[field+'/'+arm+'/'+key]=stats.get(field+'/'+arm+'/'+key,0)+value
                for r in frames:
                    copies[r['subject']][field][arm]=predictions[r['subject']]
                    if arm=='baseline':
                        assert predictions[r['subject']]==copies[r['subject']]['unit_pipeline' if field=='joint_pipeline' else 'unit_oracle_endpoint']['learned'];replays+=1
                if arm in ('baseline','shared','assigned_global') and any(r['selected_sentence'] for r in old):
                    masked=[dict(t,word='?',lemma='?',head=None,rel='?',features={}) for t in tokens];assert allowed_indices(frames,masked,None,config)==allowed;mutations+=1
                if field=='joint_oracle_endpoint':
                    domains=feasible_domains(frames,allowed,config.get('shared',False))
                    for r in frames:
                        option=tuple(r['gold'][1::2]);s=r['subject'];gold_results[s]['arms'][arm]=dict(local_reasons=reasons(r,option,tokens,ctx,config,gold_assigned),gold_feasible=option in domains[s])
                        if s in cop_candidates:
                            for c in cop_candidates[s]['candidates']:c['kept'][arm]=(c['head'],'cop') in domains[s]
                    typed={r['subject']:[j for j in allowed[r['subject']] if r['options'][j][1]==r['gold'][3]] for r in frames};typed_predictions,_=decode(frames,typed,config.get('shared',False))
                    for r in frames:copies[r['subject']]['joint_true_type'][arm]=typed_predictions[r['subject']]
        groups=defaultdict(list)
        for r in gold_frames:groups[r['carrier']].append(r)
        sentence_audits.append(dict(sid=sid,gold_groups=[dict(carrier=v,subjects=[r['subject'] for r in group],units=[r['gold'] for r in group],one_coordination_component=all(r['subject'] in ctx['coordination'][group[0]['subject']] for r in group)) for v,group in groups.items()],coordinated_subjects=[r['subject'] for r in gold_frames if len(ctx['coordination'][r['subject']])>1],shared_gold_conflicts=shared_gold_conflicts(gold_frames)))
        rows.extend(copies.values());feasibility.extend(gold_results.values());candidates.extend(cop_candidates.values())
    save(OUT/'frame-predictions.json',rows);save(OUT/'gold-feasibility.json',feasibility);save(OUT/'copular-candidates.json',candidates);save(OUT/'sentence-audit.json',sentence_audits);save(OUT/'decode-statistics.json',stats);save(OUT/'prediction-freeze.json',dict(inputs={str(p):digest(p) for p in OUT.glob('*.json')}));result=evaluate(rows);save(OUT/'evaluation.json',result);save(OUT/'feasibility-summary.json',summarize_feasibility(feasibility,candidates,sentence_audits));save(OUT/'validation.json',dict(previous_hashes=len(previous['inputs']),frozen_models=5,models_refitted=0,baseline_replays=replays,observable_masking_checks=mutations,gold_units=len(feasibility),copular_frames=len(candidates),reserve_unscored=200,prior_queries_scored=0))
    for k,v in result['unit_metrics'].items():
        if k.startswith(('all_source/','selected_sentences/')):print(k,v,flush=True)
    print('Sharing',load(OUT/'feasibility-summary.json')['sharing'],flush=True)
if __name__=='__main__':run()
