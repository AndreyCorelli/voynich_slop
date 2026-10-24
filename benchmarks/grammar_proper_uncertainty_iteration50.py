"""Frozen-prediction uncertainty expansion; no fitting or reserve evaluation."""
from pathlib import Path
from collections import defaultdict
import copy
from benchmarks.grammar_factor_morphology_iteration49 import OUT as PREVIOUS,SOURCE,EXAMPLES,fold,load,save,digest
from voynich_smt.proper_name_uncertainty import POLICIES,candidates
from voynich_smt.source_morphology import domains,label,group
from voynich_smt.construction_interventions import readings_key
from voynich_smt.relational_compatibility import sv_lattice
from voynich_smt.morphology_stress import encode,link_summary,decode
OUT=PREVIOUS.parent/'iteration50'


def run():
    assert not OUT.exists()
    previous=load(PREVIOUS/'verification-manifest.json')
    for p,h in previous['inputs'].items():assert digest(p)==h,p
    OUT.mkdir()
    (OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),Path('src/voynich_smt/proper_name_uncertainty.py'),OUT/'proposal-design.md',PREVIOUS/'verification-manifest.json']
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},policies=POLICIES,scope='Post-error diagnostic on reused iteration49 folds. PROPN and fit number-label count only; preserve eligibility/person, no test morphology used in expansion. No reserve or prior query scoring.'))
    data=load(SOURCE);examples=load(EXAMPLES);models=load(PREVIOUS/'models.json');partitions=load(PREVIOUS/'manifest.json')['partitions'];oldrefs=load(PREVIOUS/'reference-evaluation.json');old={ (r['sent_id'],r['subject'],r['predicate']):r for r in oldrefs};predictions={};tokens=defaultdict(lambda:dict(n=0,covered=0,size=0,changed=0));replays=0;typechecks=0
    for f in range(5):
        raw=load(PREVIOUS/f'predictions-{f}.json')['types'];model=models[str(f)]['expanded']['model'];types={}
        for key,r in raw.items():
            word,pos=key.split('\t');original=r['sets']['expanded_total99'];sets={p:candidates(word,pos,original,model,p) for p in POLICIES}
            assert sets['baseline']==sorted(original)
            assert set(sets['baseline'])<=set(sets['proper_unseen'])<=set(sets['proper_sparse5'])<=set(sets['proper_all'])
            types[key]=dict(sets=sets);typechecks+=1
        predictions[f]=types
        for sid in partitions[str(f)]['test']:
            for t in data[sid]['tokens']:
                y=label(t)
                if y is None:continue
                for p in POLICIES:
                    states=types[readings_key(t)]['sets'][p]
                    for cohort in (group(t['pos']),'PROPN' if t['pos']=='PROPN' else 'non_PROPN'):
                        r=tokens[p+'/'+cohort];r['n']+=1;r['covered']+=y in states;r['size']+=len(states);r['changed']+=states!=types[readings_key(t)]['sets']['baseline']
    save(OUT/'type-predictions.json',predictions)
    save(OUT/'prediction-freeze.json',dict(inputs={str(p):digest(p) for p in OUT.glob('*.json')}))
    rows=[]
    for e in examples:
        sid=e['sent_id'];types=predictions[fold(sid)];ts=data[sid]['tokens'];arms={}
        for p in POLICIES:
            domain=domains(ts,types,p);mutated=[dict(t,features={},head=-1,rel='mutated',case='mutated') for t in ts]
            assert domain==domains(mutated,types,p)
            arms[p]={}
            for rule in ('none','agreement'):
                lattice=sv_lattice(domain,rule);packed=encode(lattice);assert sorted(decode(packed))==sorted(lattice);arms[p][rule]=link_summary(packed,e['reference']);replays+=1
            assert set(map(tuple,sv_lattice(domains(ts,types,'baseline'))))<=set(map(tuple,sv_lattice(domain)))
        prior=old[sid,e['subject'],e['predicate']]
        assert arms['baseline']==prior['arms']['expanded_total99']
        rows.append(dict(sent_id=sid,subject=e['subject'],predicate=e['predicate'],author=e['author'],clean_ambiguous=prior['clean_ambiguous'],arms=arms))
    result={};paired={}
    for cohort in ('all','clean_ambiguous','Cicero','Palladius'):
        chosen=[r for r in rows if cohort=='all' or cohort=='clean_ambiguous' and r['clean_ambiguous'] or r['author']==cohort]
        for p in POLICIES:
            scores=[r['arms'][p]['agreement'] for r in chosen]
            result[cohort+'/'+p]=dict(n=len(scores),**{k:sum(s[k] for s in scores) for k in ('reference_exact','reference_link','unique_correct','false_unique')},empty=sum(s['links']==0 for s in scores),mean_links=sum(s['links'] for s in scores)/len(scores))
    for p in POLICIES:
        paired[p]=dict(rescued=0,lost=0,unique_added=0,unique_removed=0)
        for r in rows:
            a=r['arms']['baseline']['agreement'];b=r['arms'][p]['agreement'];d=paired[p]
            d['rescued']+=b['reference_link'] and not a['reference_link'];d['lost']+=a['reference_link'] and not b['reference_link'];d['unique_added']+=b['unique_correct'] and not a['unique_correct'];d['unique_removed']+=a['unique_correct'] and not b['unique_correct']
    for r in tokens.values():r.update(coverage=r['covered']/r['n'],mean_size=r['size']/r['n'])
    save(OUT/'reference-evaluation.json',rows);save(OUT/'evaluation.json',dict(structure=result,tokens=dict(tokens),paired=paired))
    save(OUT/'validation.json',dict(previous_hashes=len(previous['inputs']),type_nesting_checks=typechecks,summary_decode_replays=replays,baseline_reproduced=326,heldout_annotation_mutation_invariant=True,reserved_unscored=200,prior_queries_scored=0))
    print({p:result['all/'+p] for p in POLICIES});print(paired)
if __name__=='__main__':run()
