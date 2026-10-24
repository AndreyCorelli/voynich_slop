"""Attribute coordination losses and test target-aligned gold-conj exclusion."""
from benchmarks.grammar_joint_subject_none_iteration65 import OUT as PREVIOUS,UNIT,MORPH,SOURCE,RESERVE,load,save,digest,decode_sentences,unit_predictions
from voynich_smt.joint_unit_oracle_v2 import coordination
from voynich_smt.multi_link_attachment import edge_metrics
from pathlib import Path
from collections import defaultdict,Counter
import copy
OUT=PREVIOUS.parent/'iteration66'
ARMS=('baseline','competition65','oracle_conj')


def remove_conj(frames,data):
    result=[]
    for r in frames:
        other=dict(r)
        if data[r['sid']]['tokens'][r['subject']]['rel'].split(':')[0]=='conj':
            assert r['gold'] is None
            other.update(predicates=[],scores=[])
        result.append(other)
    return result


def evaluate(rows):
    metrics={};roles={};cohort={}
    for scope in ('all_source','selected_sentences','Cicero_all','Palladius_all'):
        rs=[r for r in rows if not r['carrier_ambiguous'] and (scope=='all_source' or scope=='selected_sentences' and r['selected_sentence'] or scope.endswith('_all') and r['author']==scope[:-4])];gold={(r['sid'],*r['unit_gold']) for r in rs if r['unit_gold'] is not None}
        for arm in ARMS:
            pred={(r['sid'],*r['coord_unit'][arm]) for r in rs if r['coord_unit'][arm] is not None};metrics[scope+'/'+arm]=edge_metrics(gold,pred)
            for role in ('direct','cop','aux'):roles[scope+'/'+arm+'/'+role]=edge_metrics({u for u in gold if u[-1]==role},{u for u in pred if u[-1]==role})
            positives=[r for r in rs if r['coordination_subject'] and r['unit_gold'] is not None];cohort[scope+'/'+arm]=dict(n=len(positives),exact=sum(r['coord_unit'][arm]==r['unit_gold'] for r in positives))
    return dict(unit_metrics=metrics,per_role=roles,coordination=cohort)


def attribution(rows,data):
    by_sid=defaultdict(list);cases=[];counts=Counter()
    for r in rows:by_sid[r['sid']].append(r)
    for r in rows:
        if not r['coordination_subject'] or r['unit_gold'] is None:continue
        a=r['coord_unit']['baseline']==r['unit_gold'];b=r['coord_unit']['competition65']==r['unit_gold']
        if a==b:continue
        kind='lost' if a else 'gained';counts[kind]+=1;s=r['subject'];v=r['carrier_gold'];tokens=data[r['sid']]['tokens'];component=coordination(tokens,s);rivals=[]
        for other in by_sid[r['sid']]:
            u=other['subject']
            if u==s or not (other['coord_carrier']['baseline']==v or other['coord_carrier']['competition65']==v):continue
            rivals.append(dict(subject=u,word=tokens[u]['word'],rel=tokens[u]['rel'],same_component=u in component,gold_carrier=other['carrier_gold'],before=other['coord_carrier']['baseline'],after=other['coord_carrier']['competition65']))
        counts[kind+'_with_same_component_conj_rival']+=any(q['same_component'] and q['rel'].split(':')[0]=='conj' for q in rivals)
        cases.append(dict(sid=r['sid'],subject=s,word=tokens[s]['word'],gold=r['unit_gold'],kind=kind,change='abstained' if r['coord_carrier']['competition65'] is None else 'rerouted',component=sorted(component),rivals=rivals,oracle_prediction=r['coord_unit']['oracle_conj'],oracle_restores_exact=r['coord_unit']['oracle_conj']==r['unit_gold']))
    return dict(counts=dict(counts),cases=cases)


def run():
    assert not OUT.exists()
    for p,h in load(PREVIOUS/'verification-manifest.json')['inputs'].items():assert digest(p)==h,p
    OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text());paths=[Path(__file__),Path('benchmarks/grammar_coordination_oracle_iteration66_audit.py'),SOURCE,RESERVE,MORPH/'manifest.json',PREVIOUS/'test-lattices.json',PREVIOUS/'policies.json',PREVIOUS/'frame-predictions.json',PREVIOUS/'verification-manifest.json',UNIT/'models.json',Path('src/voynich_smt/joint_subject_none.py'),Path('src/voynich_smt/joint_unit_oracle_v2.py'),OUT/'proposal-design.md']
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},scope='Same4070source/frozen65 primary policy/56edge and57unit scores/3365units519selected. Attribute allcoordination122goldunit changes, including gains. No training/calibration/cutoff/penalty changes. Reserve200 unscored.',oracle='Suppress all nominal subjects with source dependencybase=conj by emptying their outgoing domains; require carrier goldNone. This is aligned to existing nsubj-head-only task, not a claim conjuncts have no grammaticalsubjectrole. Source goldconj annotation is oracle-only; no targetprojection/relabeling. Keep otherframes/alternatives/NONE unchanged. No blanket penalty waiver. If encouraging for coordination and overallunitF1, test learned observableconj evidence in a separate iteration.'))
    data=load(SOURCE);parts=load(MORPH/'manifest.json')['partitions'];reserve={r['sent_id'] for rs in load(RESERVE)['authors'].values() for r in rs};assert not set(data)&reserve;models=load(UNIT/'models.json');policies=load(PREVIOUS/'policies.json');lattices=load(PREVIOUS/'test-lattices.json');rows=load(PREVIOUS/'frame-predictions.json');lookup={(r['sid'],r['subject']):r for r in rows}
    for r in rows:
        r['coordination_subject']=bool(r['unit_gold'] is not None and len(coordination(data[r['sid']]['tokens'],r['subject']))>1);r['coord_unit']={'baseline':r['competition_unit']['baseline'],'competition65':r['competition_unit']['carrier_cal'],'oracle_conj':None};r['coord_carrier']={'baseline':r['competition_carrier']['baseline'],'competition65':r['competition_carrier']['carrier_cal'],'oracle_conj':None}
    for f in range(5):
        record=policies[str(f)];p,_=decode_sentences(remove_conj(lattices[str(f)],data),record['cutoff'],record['selected']['carrier']['penalty']);u=unit_predictions(p,data,models[str(f)]['model'],{})
        for key,v in p.items():lookup[key]['coord_carrier']['oracle_conj']=v;lookup[key]['coord_unit']['oracle_conj']=u[key]
    save(OUT/'frame-predictions.json',rows);save(OUT/'prediction-freeze.json',dict(inputs={str(p):digest(p) for p in OUT.glob('*.json')}));result=evaluate(rows);save(OUT/'evaluation.json',result);save(OUT/'attribution.json',attribution(rows,data));print(result);print(load(OUT/'attribution.json'))
if __name__=='__main__':run()
