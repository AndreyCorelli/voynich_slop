"""Role-correct PP filtering, followed by finite subject/predicate interventions."""
from pathlib import Path
from collections import Counter,defaultdict
import hashlib
import numpy as np
from benchmarks.grammar_construction_interventions_iteration45 import OUT as PREVIOUS,ROOT,RESERVE,load,save,digest
from voynich_smt.construction_interventions import interventions,summarize,value,FIELDS
from voynich_smt.relational_compatibility import role_witness,pp_lattice,sv_morphology,sv_domains,sv_lattice,sv_interventions,sv_summary,SV_FIELDS,sv_value
OUT=ROOT/'iteration46'
SOURCE=ROOT/'iteration44/annotations-truth.json'


def eligible_subjects(data):
    eligible=[];exclusions=Counter()
    for sid,row in data.items():
        tokens=row['tokens'];children=defaultdict(list)
        for i,t in enumerate(tokens):
            if t['head'] is not None:children[t['head']].append(i)
        for s,t in enumerate(tokens):
            if t['rel']!='nsubj':continue
            v=t['head'];fs=t['features']
            if v is None or tokens[v]['pos'] not in ('VERB','AUX') or tokens[v]['features'].get('VerbForm')!='Fin':exclusions['nonfinite_or_nonverbal_governor']+=1;continue
            if t['pos'] not in ('NOUN','PROPN','PRON') or 'Nom' not in fs.get('Case','').split(','):exclusions['non_nominal_or_non_nominative']+=1;continue
            if any(tokens[i]['rel']=='conj' for i in children[s]):exclusions['coordinated_subject']+=1;continue
            vf=tokens[v]['features'];sp='3' if t['pos'] in ('NOUN','PROPN') else fs.get('Person','');sn=fs.get('Number','');vn=vf.get('Number','');vp=vf.get('Person','')
            if sn not in ('Sing','Plur') or vn not in ('Sing','Plur') or sp not in ('1','2','3') or vp not in ('1','2','3'):exclusions['missing_or_nonatomic_agreement_features']+=1;continue
            eligible.append(dict(sent_id=sid,author=row['author'],subject=s,predicate=v,reference=[s,v,sn,sp,vn,vp]))
    return eligible,dict(exclusions)


def run():
    assert not OUT.exists()
    for p,h in load(PREVIOUS/'verification-manifest.json')['inputs'].items():assert digest(p)==h,p
    data=load(SOURCE);reserve={r['sent_id'] for rows in load(RESERVE)['authors'].values() for r in rows};assert not set(data)&reserve
    OUT.mkdir();paths=[Path(__file__),Path('src/voynich_smt/relational_compatibility.py'),Path('src/voynich_smt/construction_interventions.py'),SOURCE,PREVIOUS/'verification-manifest.json',PREVIOUS/'lattices.json',PREVIOUS/'morphology-oracle.json',PREVIOUS/'wrong-fact-probes.json',RESERVE]
    save(OUT/'manifest.json',dict(inputs={str(p):digest(p) for p in paths},scope='Same reused source4070 Cicero/Palladius sentences; no old target queries/reserve. No trained scores. Oracle word-type morphology includes all source occurrences; POS and candidate anchors/eligibility are privileged.',
        pp_rule='ADJ/DET may be an agreeing modifier OR a genitive dependent if an explicit Gen reading exists. Genitive branch has its own number/gender and need not agree with head. Correction motivated by iteration45 failures, not independent confirmation. Candidate tuples unchanged, internal role existential.',
        pp_evaluation='Same879 examples, exact domains, original-vs-role alternatives; all16 fact interventions; reuse exact iteration45 wrong-fact values for oracle-word-type arm. Check correct survival, growth in alternatives, wrong-fact feasibility.',
        sv_eligibility='Direct overt nominal/pronominal nominative nsubj of VERB/AUX with reference VerbFormFin, known Sing/Plur and Person1/2/3 (NOUN/PROPN default3). Exclude coordinated subjects. Keep actual agreement mismatches as failures, never exclude by agreement.',
        sv_selection='From eligible pool, up to250 constructions per author sorted by SHA256(sent_id:subject:predicate). Freeze rule before enumeration. References available via same-source oracle dictionary, no gold tuple injection.',
        sv_candidates='All nominal tokens with oracle word-type Nom/unknown case readings and all VERB/AUX tokens with finite readings in whole sentence. Unknown number/person expanded to2/3 values. No gold clause boundaries, edges, distance ranking or shared-parent constraints.',
        sv_arms='none: same morphology no number/person equality; number: number equality only; agreement: number and person equality; hidden: mask both features (retain grammatical nominal third person) and enforce equality. No scores or token-specific reference morphology used in filter.',
        sv_facts='subject token, predicate token, subject(number,person), predicate(number,person); all16 subsets. Report exact tuple and link survival/uniqueness and extra unrevealed facts, common reference-surviving ambiguous-link cohort for paired comparisons.',
        wrong_facts='Seed46001 one alternate subject/predicate token from common raw domains, same probes across arms. Report alone and with the opposite reference token revealed. These are annotation contrasts, not proven ungrammatical alternatives.'))
    pp=[];lex=load(PREVIOUS/'morphology-oracle.json')
    for e in load(PREVIOUS/'lattices.json'):
        tokens=data[e['sent_id']]['tokens'];old=e['arms']['oracle_word_type']['candidates'];new=pp_lattice(tokens,e['prep'],e['domains'],lex);ref=e['reference'];pp.append(dict(sent_id=e['sent_id'],construction=e['construction'],reference=ref,candidates=new,old_count=len(old),reference_roles=role_witness(tokens,ref[0],ref[1],ref[2],ref[3],lex),summaries={('none' if not f else '+'.join(f)):dict(old=summarize(old,ref,f),roles=summarize(new,ref,f)) for f in interventions()}))
    pool,exclusions=eligible_subjects(data);sample=[]
    for author in ('Cicero','Palladius'):
        selected=[r for r in pool if r['author']==author];selected.sort(key=lambda r:hashlib.sha256(f"{r['sent_id']}:{r['subject']}:{r['predicate']}".encode()).hexdigest());sample+=selected[:250]
    svlex=sv_morphology(s['tokens'] for s in data.values());sv=[]
    for e in sample:
        tokens=data[e['sent_id']]['tokens'];domain=sv_domains(tokens,svlex);hidden=sv_domains(tokens,svlex,True);arms={}
        for arm in ('none','number','agreement','hidden'):
            candidates=sv_lattice(hidden if arm=='hidden' else domain,arm);arms[arm]=dict(candidates=candidates,summaries={('none' if not f else '+'.join(f)):sv_summary(candidates,e['reference'],f) for f in sv_interventions()})
        sv.append(dict(**e,domains=domain,hidden_domains=hidden,arms=arms))
    save(OUT/'pp-lattices.json',pp);save(OUT/'sv-morphology-oracle.json',svlex);save(OUT/'sv-lattices.json',sv);save(OUT/'selection-audit.json',dict(eligible_by_author=dict(Counter(e['author'] for e in pool)),selected_by_author=dict(Counter(e['author'] for e in sample)),exclusions=exclusions,raw_reference_agreement_mismatches=sum(e['reference'][2:4]!=e['reference'][4:6] for e in sample)))
    save(OUT/'evaluation-freeze.json',dict(inputs={str(p):digest(p) for p in OUT.glob('*.json')}));evaluate()


def evaluate():
    pp=load(OUT/'pp-lattices.json');probes=load(PREVIOUS/'wrong-fact-probes.json');pindex={(e['sent_id'],e['construction']):e for e in pp};ppeval={}
    for fields in interventions():
        key='none' if not fields else '+'.join(fields);ppeval[key]={}
        for arm in ('old','roles'):
            s=[e['summaries'][key][arm] for e in pp];ppeval[key][arm]=dict(reference_retained=sum(x['reference_retained'] for x in s),uniquely_correct=sum(x['uniquely_correct'] for x in s),false_unique=sum(x['false_unique'] for x in s),total_candidates=sum(x['remaining'] for x in s))
    wrongpp={}
    for f in FIELDS:
        selected=[r for r in probes if r['arm']=='oracle_word_type' and r['field']==f];old=[r for r in selected if r['baseline_reference_retained']];common=[r for r in old if pindex[r['sent_id'],r['construction']]['summaries']['none']['roles']['reference_retained']]
        def count(rs):
            counts=[sum(value(c,f)==(tuple(r['wrong_value']) if f=='boundary' else r['wrong_value']) for c in pindex[r['sent_id'],r['construction']]['candidates']) for r in rs];return dict(n=len(rs),old_nonempty=sum(r['remaining']>0 for r in rs),roles_nonempty=sum(n>0 for n in counts),old_unique_wrong=sum(r['unique_wrong'] for r in rs),roles_unique_wrong=sum(n==1 for n in counts))
        wrongpp[f]=count(common)
    sv=load(OUT/'sv-lattices.json');matrix={};wrong=[];rng=np.random.default_rng(46001)
    for e in sv:
        domain=e['domains'];ref=e['reference'];raw={f:sorted({r[0] for r in domain['subjects' if f=='subject' else 'predicates']}) for f in ('subject','predicate')}
        for f in ('subject','predicate'):
            alternatives=[v for v in raw[f] if v!=sv_value(ref,f)]
            if not alternatives:continue
            v=alternatives[int(rng.integers(len(alternatives)))];opposite='predicate' if f=='subject' else 'subject'
            for arm,a in e['arms'].items():
                alone=[c for c in a['candidates'] if sv_value(c,f)==v];conditional=[c for c in alone if sv_value(c,opposite)==sv_value(ref,opposite)];wrong.append(dict(sent_id=e['sent_id'],subject=e['subject'],predicate=e['predicate'],arm=arm,field=f,wrong_value=v,alone_nonempty=bool(alone),conditional_nonempty=bool(conditional)))
    for cohort in ('all','common_ambiguous'):
        chosen=[e for e in sv if cohort=='all' or (e['arms']['none']['summaries']['none']['reference_retained'] and e['arms']['agreement']['summaries']['none']['reference_retained'] and e['arms']['none']['summaries']['none']['links']>1)]
        for fs in sv_interventions():
            key='none' if not fs else '+'.join(fs)
            for arm in ('none','number','agreement','hidden'):
                s=[e['arms'][arm]['summaries'][key] for e in chosen];base=[e['arms'][arm]['summaries']['none'] for e in chosen];matrix[f'{cohort}/{key}/{arm}']=dict(n=len(s),reference_retained=sum(x['reference_retained'] for x in s),reference_link_retained=sum(x['reference_link_retained'] for x in s),unique_tuple_correct=sum(x['unique_tuple_correct'] for x in s),unique_link_correct=sum(x['unique_link_correct'] for x in s),false_unique_link=sum(x['false_unique_link'] for x in s),mean_links=float(np.mean([x['links'] for x in s])) if s else None,newly_resolved={f:sum(x['unrevealed_resolved'].get(f,False) and not b['unrevealed_resolved'].get(f,False) for x,b in zip(s,base)) for f in SV_FIELDS if f not in fs})
    wrongsv={}
    for arm in ('none','number','agreement','hidden'):
        for f in ('subject','predicate'):
            selected=[r for r in wrong if r['arm']==arm and r['field']==f];wrongsv[f'{arm}/{f}']=dict(n=len(selected),alone_nonempty=sum(r['alone_nonempty'] for r in selected),with_correct_opposite_nonempty=sum(r['conditional_nonempty'] for r in selected))
    save(OUT/'sv-wrong-fact-probes.json',wrong);save(OUT/'evaluation.json',dict(pp=ppeval,pp_wrong=wrongpp,sv=matrix,sv_wrong=wrongsv));print('Selection',load(OUT/'selection-audit.json'));print('PP',ppeval['none'],wrongpp)
    for k,v in matrix.items():
        if k.startswith('common_ambiguous/') and k.split('/')[1] in ('none','subject','predicate','subject_features','predicate_features'):print(k,v)
    print('SV wrong',wrongsv)
if __name__=='__main__':run()
