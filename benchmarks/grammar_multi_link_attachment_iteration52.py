"""Held-sentence multi-edge attachment with a non-subject option."""
from pathlib import Path
from collections import Counter
from benchmarks.grammar_factor_morphology_iteration49 import OUT as MORPH,SOURCE,EXAMPLES,RESERVE,fold,load,save,digest
from benchmarks.grammar_link_ranking_iteration51 import OUT as PREVIOUS
from voynich_smt.factor_morphology import predict
from voynich_smt.proper_name_uncertainty import candidates
from voynich_smt.source_morphology import domains,group
from voynich_smt.construction_interventions import readings_key
from voynich_smt.relational_compatibility import sv_lattice
from voynich_smt.multi_link_attachment import FEATURES,vector,fit,propose,distance_proposal,calibrate,accept,edge_metrics
OUT=PREVIOUS.parent/'iteration52'
ARMS=('distance','structural','local_morph')


def make_frames(sid,tokens,morph,cache):
    types={};probabilities={}
    for i,t in enumerate(tokens):
        if group(t['pos']) is None:continue
        key=readings_key(t)
        if key not in cache:
            r=predict(morph['model'],morph['policies'],t['word'],t['pos'])
            cache[key]=dict(sets={'current':candidates(t['word'],t['pos'],r['sets']['total99'],morph['model'],'proper_unseen')},probabilities=r['component_probabilities'])
        types[key]=cache[key];probabilities[i]=cache[key]['probabilities']
    pairs=sorted({tuple(c[:2]) for c in sv_lattice(domains(tokens,types,'current'))});frames=[]
    for s,t in enumerate(tokens):
        if t['pos'] not in ('NOUN','PROPN','PRON'):continue
        predicates=[v for u,v in pairs if u==s]
        frames.append(dict(sid=sid,subject=s,predicates=predicates,vectors={arm:[vector(tokens,s,v,probabilities,arm) for v in predicates] for arm in FEATURES}))
    return frames,pairs


def add_targets(frames,tokens):
    for f in frames:
        t=tokens[f['subject']];v=t['head']
        f['gold']=v if t['rel']=='nsubj' and v is not None and tokens[v]['pos'] in ('VERB','AUX') and tokens[v]['features'].get('VerbForm')=='Fin' else None
    return frames


def prepare(ids,data,morph,cache):
    frames=[]
    for sid in ids:frames.extend(add_targets(make_frames(sid,data[sid]['tokens'],morph,cache)[0],data[sid]['tokens']))
    return frames


def metrics(rows,arm,policy):
    gold={(r['sid'],r['subject'],r['gold']) for r in rows if r['gold'] is not None};predicted={(r['sid'],r['subject'],r['arms'][arm][policy]) for r in rows if r['arms'][arm][policy] is not None};m=edge_metrics(gold,predicted)
    m.update(frames=len(rows),abstained=sum(r['arms'][arm][policy] is None for r in rows),non_subject_frames=sum(r['gold'] is None for r in rows),non_subject_false_attachment=sum(r['gold'] is None and r['arms'][arm][policy] is not None for r in rows),wrong_governor=sum(r['gold'] is not None and r['arms'][arm][policy] is not None and r['arms'][arm][policy]!=r['gold'] for r in rows))
    return m


def run():
    assert not OUT.exists()
    previous=load(PREVIOUS/'verification-manifest.json')
    for p,h in previous['inputs'].items():assert digest(p)==h,p
    OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),Path('src/voynich_smt/multi_link_attachment.py'),Path('src/voynich_smt/factor_morphology.py'),Path('src/voynich_smt/proper_name_uncertainty.py'),SOURCE,EXAMPLES,RESERVE,MORPH/'models.json',MORPH/'manifest.json',PREVIOUS/'verification-manifest.json',OUT/'proposal-design.md']
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},scope='Same4070 source sentences and outer partitions. Primary304 selected sentences,326 reference recall; secondary full4070 source cross-validation. No reserve or prior queries. Readable Latin and supplied POS. No supplied subject/predicate anchors.',design='Per NOUN/PROPN/PRON softmax over broad compatible predicates plus NONE. Multiple subjects may attach and multiple links per sentence; no tree/coordination constraints. Gold finite nsubj is target; other nominal roles NONE. Omit unrepresentable positive fit rows, retain all in calibration/evaluation denominators. Inference features never read dependency or gold morphology.',training='Frozen49 expanded morphology model and policies for each outer split; proper_unseen50. Fit morphology probabilities on fit tokens are in-sample, an overfitting limitation. Structural: bias/logdistance/direction/log boundary counts/subjectPOS. local_morph adds immediate neighborPOS and log eligibility odds and number/person compatibility. Fixed L2=.01; L-BFGS convergence required. Distance baseline unique nearest compatible predicate or abstain.',calibration='For each arm separately choose F1 threshold (ties fewer predictions) or empirical precision>=90% with>=20 predictions, maximizing true positives. No qualifying high-precision threshold => abstain. Fixed probability0,.1,.2,.3,.4,.5,.6,.7,.8,.85,.9,.95,.975,.99,1.1; distance0,1,2,3,4,6,8,12,16,24,32,64,1000000. No test selection.'))
    data=load(SOURCE);examples=load(EXAMPLES);parts=load(MORPH/'manifest.json')['partitions'];morphs=load(MORPH/'models.json');reserve={r['sent_id'] for rs in load(RESERVE)['authors'].values() for r in rs};assert not set(data)&reserve;models={}
    for f in range(5):
        p=parts[str(f)];assert not (set(p['fit'])&set(p['calibration']) or set(p['fit'])&set(p['test']) or set(p['calibration'])&set(p['test']));cache={};morph=morphs[str(f)]['expanded'];training=prepare(p['fit'],data,morph,cache);calibration=prepare(p['calibration'],data,morph,cache);models[str(f)]={}
        for arm in ARMS:
            model=fit(training,arm) if arm!='distance' else None
            proposals=[propose(r,model) if model else distance_proposal(r) for r in calibration]
            models[str(f)][arm]=dict(model=model,thresholds=calibrate(calibration,proposals,arm=='distance'))
        print('Fit/calibrated',f,[(a,models[str(f)][a]['thresholds']['f1']['threshold']) for a in ARMS],flush=True)
    save(OUT/'models.json',models);save(OUT/'model-freeze.json',dict(inputs={str(p):digest(p) for p in OUT.glob('*.json')}))
    output=[];checks=0;selected={e['sent_id'] for e in examples};references={(e['sent_id'],e['subject']):e['predicate'] for e in examples};previousrefs=load(PREVIOUS.parent/'iteration50/reference-evaluation.json');previouslinks={(r['sent_id'],r['subject'],r['predicate']):r['arms']['proper_unseen']['agreement']['reference_link'] for r in previousrefs}
    for f in range(5):
        cache={};morph=morphs[str(f)]['expanded']
        for sid in parts[str(f)]['test']:
            tokens=data[sid]['tokens'];frames,pairs=make_frames(sid,tokens,morph,cache)
            if sid in selected:
                masked=[dict(t,features={},head=None,rel='?',lemma='?') for t in tokens];other,otherpairs=make_frames(sid,masked,morph,cache);assert frames==other and pairs==otherpairs;checks+=1
            for frame in add_targets(frames,tokens):
                r=dict(sid=sid,author=data[sid]['author'],subject=frame['subject'],gold=frame['gold'],candidate_predicates=frame['predicates'],selected_sentence=sid in selected,selected_reference=references.get((sid,frame['subject'])),arms={},proposals={})
                for arm in ARMS:
                    record=models[str(f)][arm];proposal=propose(frame,record['model']) if arm!='distance' else distance_proposal(frame);r['proposals'][arm]=proposal;r['arms'][arm]={policy:proposal['predicate'] if accept(proposal,record['thresholds'][policy]['threshold'],arm=='distance') else None for policy in ('f1','precision90')}
                if r['selected_reference'] is not None:assert (r['selected_reference'] in frame['predicates'])==previouslinks[sid,frame['subject'],r['selected_reference']]
                output.append(r)
    save(OUT/'frame-predictions.json',output);save(OUT/'prediction-freeze.json',dict(inputs={str(p):digest(p) for p in OUT.glob('*.json')}))
    result={};reference_result={}
    for scope in ('selected_sentences','all_source','Cicero_selected','Palladius_selected'):
        chosen=[r for r in output if scope=='all_source' or r['selected_sentence'] and (scope=='selected_sentences' or r['author']==scope.split('_')[0])]
        for arm in ARMS:
            for policy in ('f1','precision90'):result[scope+'/'+arm+'/'+policy]=metrics(chosen,arm,policy)
    for arm in ARMS:
        for policy in ('f1','precision90'):
            rows=[r for r in output if r['selected_reference'] is not None];reference_result[arm+'/'+policy]=dict(n=len(rows),correct=sum(r['arms'][arm][policy]==r['selected_reference'] for r in rows),wrong=sum(r['arms'][arm][policy] is not None and r['arms'][arm][policy]!=r['selected_reference'] for r in rows),abstained=sum(r['arms'][arm][policy] is None for r in rows))
    opportunity={}
    for scope in ('selected_sentences','all_source'):
        rows=[r for r in output if scope=='all_source' or r['selected_sentence']];opportunity[scope]=dict(frames=len(rows),sentences=len({r['sid'] for r in rows}),gold_edges=sum(r['gold'] is not None for r in rows),gold_retrievable=sum(r['gold'] is not None and r['gold'] in r['candidate_predicates'] for r in rows),candidate_edges=sum(len(r['candidate_predicates']) for r in rows))
    save(OUT/'evaluation.json',dict(edges=result,selected_references=reference_result,opportunity=opportunity));save(OUT/'validation.json',dict(previous_hashes=len(previous['inputs']),selected_sentence_inference_mutation_checks=checks,selected_reference_survival_replays=len(references),partitions_disjoint=True,source_sentences=len(data),reserve_unscored=200,prior_queries_scored=0))
    print(opportunity)
    for k,r in result.items():
        if k.startswith('selected_sentences/'):print(k,r)
    print('Selected references',reference_result)
if __name__=='__main__':run()
