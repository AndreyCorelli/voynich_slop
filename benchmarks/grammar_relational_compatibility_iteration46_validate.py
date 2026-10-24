"""Replay roles, sampling, subject agreement interventions, and wrong-fact probes."""
from collections import Counter
from copy import deepcopy
import hashlib
import numpy as np
from benchmarks.grammar_relational_compatibility_iteration46 import OUT,PREVIOUS,SOURCE,RESERVE,load,save,digest,eligible_subjects
from voynich_smt.construction_interventions import interventions,summarize,value,FIELDS
from voynich_smt.relational_compatibility import pp_lattice,role_witness,sv_morphology,sv_domains,sv_lattice,sv_interventions,sv_summary,SV_FIELDS,sv_value


def validate():
    checks=0
    for filename in ('manifest.json','evaluation-freeze.json'):
        for p,h in load(OUT/filename)['inputs'].items():assert digest(p)==h,p;checks+=1
    data=load(SOURCE);reserve={r['sent_id'] for group in load(RESERVE)['authors'].values() for r in group};assert not set(data)&reserve;lex=load(PREVIOUS/'morphology-oracle.json');old={(r['sent_id'],r['construction']):r for r in load(PREVIOUS/'lattices.json')};pp=load(OUT/'pp-lattices.json');replays=0;restored=[]
    for e in pp:
        prior=old[e['sent_id'],e['construction']];tokens=data[e['sent_id']]['tokens'];candidates=pp_lattice(tokens,prior['prep'],prior['domains'],lex);assert candidates==e['candidates'];assert set(map(tuple,prior['arms']['oracle_word_type']['candidates']))<=set(map(tuple,candidates));assert e['reference'] in candidates
        if e['reference'] not in prior['arms']['oracle_word_type']['candidates']:restored.append(dict(sent_id=e['sent_id'],construction=e['construction'],roles=e['reference_roles']))
        for fs in interventions():
            key='none' if not fs else '+'.join(fs);assert summarize(candidates,e['reference'],fs)==e['summaries'][key]['roles'];assert summarize(prior['arms']['oracle_word_type']['candidates'],e['reference'],fs)==e['summaries'][key]['old'];replays+=2
    svlex=sv_morphology(s['tokens'] for s in data.values());assert svlex==load(OUT/'sv-morphology-oracle.json');pool,exclusions=eligible_subjects(data);sample=[]
    for author in ('Cicero','Palladius'):
        selected=sorted((r for r in pool if r['author']==author),key=lambda r:hashlib.sha256(f"{r['sent_id']}:{r['subject']}:{r['predicate']}".encode()).hexdigest());sample+=selected[:250]
    sv=load(OUT/'sv-lattices.json');assert [(e['sent_id'],e['subject'],e['predicate']) for e in sv]==[(e['sent_id'],e['subject'],e['predicate']) for e in sample];failures=[];mutation_replays=0
    for e in sv:
        tokens=data[e['sent_id']]['tokens'];domain=sv_domains(tokens,svlex);hidden=sv_domains(tokens,svlex,True);assert domain==e['domains'] and hidden==e['hidden_domains']
        mutated=deepcopy(tokens)
        for t in mutated:t['head']=None;t['rel']='CORRUPTED';t['features']={'Case':'Acc','Number':'CORRUPTED','Person':'CORRUPTED'}
        assert sv_domains(mutated,svlex)==domain and sv_domains(mutated,svlex,True)==hidden;mutation_replays+=1
        for arm in ('none','number','agreement','hidden'):
            candidates=sv_lattice(hidden if arm=='hidden' else domain,arm);assert candidates==e['arms'][arm]['candidates'];assert len(candidates)==len(set(map(tuple,candidates)))
            if arm=='none':assert e['reference'] in candidates
            if arm in ('number','agreement'):assert set(map(tuple,candidates))<=set(map(tuple,e['arms']['none']['candidates']))
            if arm=='agreement' and e['reference'] not in candidates:failures.append(dict(sent_id=e['sent_id'],reference=e['reference'],subject=tokens[e['subject']],predicate=tokens[e['predicate']],sentence=' '.join(t['word'] for t in tokens)))
            for fs in sv_interventions():
                key='none' if not fs else '+'.join(fs);summary=sv_summary(candidates,e['reference'],fs);assert summary==e['arms'][arm]['summaries'][key];replays+=1
                for f in SV_FIELDS:
                    if f not in fs:
                        more=sv_summary(candidates,e['reference'],tuple(g for g in SV_FIELDS if g in set(fs)|{f}));assert more['remaining']<=summary['remaining']
    # Independently reproduce paired wrong-token probes, including conditioning.
    rng=np.random.default_rng(46001);probes=[]
    for e in sv:
        for f in ('subject','predicate'):
            key='subjects' if f=='subject' else 'predicates';values=sorted({r[0] for r in e['domains'][key]});alternatives=[v for v in values if v!=sv_value(e['reference'],f)]
            if not alternatives:continue
            wrong=alternatives[int(rng.integers(len(alternatives)))];opposite='predicate' if f=='subject' else 'subject'
            for arm,a in e['arms'].items():
                candidates=[c for c in a['candidates'] if sv_value(c,f)==wrong];conditional=[c for c in candidates if sv_value(c,opposite)==sv_value(e['reference'],opposite)];probes.append(dict(sent_id=e['sent_id'],subject=e['subject'],predicate=e['predicate'],arm=arm,field=f,wrong_value=wrong,alone_nonempty=bool(candidates),conditional_nonempty=bool(conditional)))
    assert probes==load(OUT/'sv-wrong-fact-probes.json')
    save(OUT/'pp-restored-reference-audit.json',restored);save(OUT/'sv-reference-pruning-audit.json',failures);result=dict(hash_checks=checks,pp_examples=len(pp),pp_restored_references=len(restored),sv_pool=len(pool),sv_selected=len(sv),matrix_replays=replays,word_type_only_mutation_replays=mutation_replays,paired_wrong_fact_probes=len(probes),sv_exact_reference_readings_pruned=len(failures),reserved_unscored=len(reserve));save(OUT/'validation.json',result);print(result)
if __name__=='__main__':validate()
