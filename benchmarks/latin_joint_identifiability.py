"""Synthetic identifiability of jointly inferred dictionary/readings/structures."""
import argparse,hashlib,json,random,time
from dataclasses import asdict
from itertools import product
from pathlib import Path
from voynich_smt.joint_grammar import JointGrammar,Reading,syntax
from voynich_smt.data.corpus import write_json,digest
OUT=Path('experiments/results/latin-joint-identifiability')


def lexicon(level):
    e={}
    def add(w,*readings):e[w]=list(readings)
    def noun(case,gender,number='S'):return Reading('N',case,number,gender)
    for w,g in [('puella','F'),('rosa','F')]:add(w,noun('NOM',g),noun('ABL',g))
    add('puer',noun('NOM','M'));add('puellam',noun('ACC','F'));add('rosam',noun('ACC','F'));add('puerum',noun('ACC','M'))
    for w in ('amat','videt'):add(w,Reading('V',number='S',valency='transitive'))
    for w in ('dormit','currit'):add(w,Reading('V',number='S',valency='intransitive'))
    if level in ('syncretic','rich'):
        for w in ('donum','bellum'):add(w,noun('NOM','N'),noun('ACC','N'))
    if level=='rich':
        add('bona',Reading('ADJ','NOM','S','F'),Reading('ADJ','ABL','S','F'),Reading('ADJ','NOM','P','N'),Reading('ADJ','ACC','P','N'))
        add('bonus',Reading('ADJ','NOM','S','M'));add('bonam',Reading('ADJ','ACC','S','F'))
        add('bonum',Reading('ADJ','ACC','S','M'),Reading('ADJ','NOM','S','N'),Reading('ADJ','ACC','S','N'))
        add('bonae',Reading('ADJ','NOM','P','F'));add('boni',Reading('ADJ','NOM','P','M'))
        add('puellae',noun('NOM','F','P'));add('pueri',noun('NOM','M','P'));add('puellas',noun('ACC','F','P'));add('pueros',noun('ACC','M','P'))
        add('amant',Reading('V',number='P',valency='transitive'));add('dormiunt',Reading('V',number='P',valency='intransitive'))
        add('est',Reading('V',number='S',valency='copular'));add('sunt',Reading('V',number='P',valency='copular'))
        add('cum',Reading('ADP',government='ABL'));add('ad',Reading('ADP',government='ACC'));add('in',Reading('ADP',government='ACC'),Reading('ADP',government='ABL'))
    return e


def corpus():
    # Intended structures are evaluation-only. Surface order varies legitimately.
    return [
        (['puella','puerum','amat'],['nsubj','obj','root'],[2,2,-1]),
        (['puella','dormit'],['nsubj','root'],[1,-1]),
        (['puer','dormit'],['nsubj','root'],[1,-1]),
        (['puer','puellam','amat'],['nsubj','obj','root'],[2,2,-1]),
        (['rosa','dormit'],['nsubj','root'],[1,-1]),
        (['rosa','rosam','amat'],['nsubj','obj','root'],[2,2,-1]),
        (['puella','bona','puerum','amat'],['nsubj','amod','obj','root'],[3,0,3,-1]),
        (['puer','bonus','puellam','amat'],['nsubj','amod','obj','root'],[3,0,3,-1]),
        (['puellae','bonae','pueros','amant'],['nsubj','amod','obj','root'],[3,0,3,-1]),
        (['pueri','boni','dormiunt'],['nsubj','amod','root'],[2,0,-1]),
        (['puella','puerum','amat','cum','rosa'],['nsubj','obj','root','case','obl'],[2,2,-1,4,2]),
        (['puella','est','bona'],['nsubj','root','xcomp'],[1,-1,1]),
    ]


def encode(rows,seed=3109):
    words=sorted({w for s,_,_ in rows for w in s});rng=random.Random(seed);ids=[f'c{i:02d}' for i in range(len(words))];rng.shuffle(ids);encoding=dict(zip(words,ids))
    return {'ciphertext':[[encoding[w] for w in s] for s,_,_ in rows]}, {'dictionary':{t:w for w,t in encoding.items()},'roles':[r for _,r,_ in rows],'heads':[h for _,_,h in rows],'plaintext':[s for s,_,_ in rows]}


def audit_example(example,lex):
    # Independent concrete constraints, not calls to the SMT compiler.
    for s in example['sentences']:
        roles=s['roles'];heads=s['heads'];rr=s['readings'];roots=[i for i,r in enumerate(roles) if r=='root'];assert len(roots)==1;v=roots[0];verb=rr[v];assert verb['pos']=='V' and heads[v]==-1
        subj=[i for i,r in enumerate(roles) if r=='nsubj'];obj=[i for i,r in enumerate(roles) if r=='obj'];assert len(subj)==1;sub=subj[0]
        for w,r in zip(s['words'],rr):assert Reading(**r) in lex[w]
        assert rr[sub]['pos']=='N' and rr[sub]['case']=='NOM' and rr[sub]['number']==verb['number'] and heads[sub]==v
        assert len(obj)==(verb['valency']=='transitive')
        for j in obj:assert rr[j]['pos']=='N' and rr[j]['case']=='ACC' and heads[j]==v
        pred=[i for i,r in enumerate(roles) if r=='xcomp'];assert len(pred)==(verb['valency']=='copular')
        for j in pred:assert rr[j]['pos']=='ADJ' and rr[j]['case']=='NOM' and heads[j]==v and all(rr[j][f]==rr[sub][f] for f in ('number','gender'))
        for j,r in enumerate(roles):
            if r=='amod':assert rr[j]['pos']=='ADJ' and rr[heads[j]]['pos']=='N' and all(rr[j][f]==rr[heads[j]][f] for f in ('case','number','gender'))
            if r=='case':assert rr[j]['pos']=='ADP' and rr[heads[j]]['case']==rr[j]['government']
            if r in ('obl','nmod'):assert rr[j]['pos']=='N' and any(r2=='case' and h==j for r2,h in zip(roles,heads))
        # Selected heads form an acyclic connected tree.
        for j in range(len(roles)):
            seen=set();x=j
            while x!=-1:assert x not in seen;seen.add(x);x=heads[x]
            assert v in seen


def fingerprint(report):
    """Strip machine-dependent solver timing and witnesses before replay comparison."""
    if isinstance(report,dict):return {k:fingerprint(v) for k,v in report.items() if k not in ('elapsed_seconds','examples','example','projections','total_elapsed_seconds')}
    if isinstance(report,list):return [fingerprint(x) for x in report]
    return report


def run(validate=False):
    OUT.mkdir(parents=True,exist_ok=True);started=time.perf_counter();rows=corpus();cases=[];datasets={}
    plans=[('base',n,False) for n in (1,2,4,6)]+[('syncretic',n,False) for n in (1,2,4,6)]+[('rich',n,False) for n in (6,8,10,11,12)]+[('rich',11,True)]
    for level,n,noun_attach in plans:
        selected=rows[:n];inputs,truth=encode(selected);lex=lexicon(level);name=f'{level}-{n}'+('-noun-attachment' if noun_attach else '')
        settings={'max_adjectives':2 if level=='rich' else 0,'allow_pp':level=='rich','noun_attachment':noun_attach}
        # Input to inference excludes plaintext, intended roles and intended heads.
        write_json(OUT/'inputs'/f'{name}.json',{**inputs,'lexicon':{w:[asdict(r) for r in rr] for w,rr in lex.items()},'grammar':settings,'candidate_policy':'Every ciphertext type receives the same full surface inventory; no gold POS/profile filtering.'})
        write_json(OUT/'truth'/f'{name}.json',truth);datasets[name]=digest({'inputs':inputs,'lexicon':{w:[asdict(r) for r in rr] for w,rr in lex.items()},'settings':settings})
        for shared in (False,True):
            solver=JointGrammar(lex,inputs['ciphertext'],shared=shared,**settings)
            structures=solver.enumerate('structure',limit=2000)
            exact=solver.query_structure(truth['roles'],truth['heads']);wrong=solver.query_structure(truth['roles'],truth['heads'],different=True)
            supplied={t:w for t,w in truth['dictionary'].items()} if shared else {(si,t):truth['dictionary'][t] for si,s in enumerate(inputs['ciphertext']) for t in s}
            assert solver.query_mapping(supplied)=='sat';assert exact['status']=='sat'
            for ex in structures['examples']+[q['example'] for q in (exact,wrong) if q['example']]:audit_example(ex,lex)
            dictionaries=solver.enumerate('dictionary',limit=1000) if shared and level!='rich' else None
            if dictionaries:
                for ex in dictionaries['examples']:audit_example(ex,lex)
            result={'case':name,'level':level,'sentence_count':n,'token_count':sum(map(len,inputs['ciphertext'])),'cipher_types':len(truth['dictionary']),'candidate_surfaces':len(lex),'shared_dictionary':shared,'grammar':settings,'syntactic_branches_per_sentence':solver.parse_counts,'structures':structures,'original_structure_feasible':exact,'wrong_structure_feasible':wrong,'dictionary_count':dictionaries,'original_dictionary_feasible':True}
            cases.append(result);print('CASE',name,'shared',shared,'structures',structures['count'],structures['status'],'wrong',wrong['status'], 'seconds',round(structures['elapsed_seconds'],2),flush=True)
        # Each sentence separately, then count their Cartesian structural product.
        independent=[]
        for s in inputs['ciphertext']:
            result=JointGrammar(lex,[s],**settings).enumerate('structure',limit=2000)
            independent.append({'count':result['count'],'status':result['status']})
        if all(x['status']=='complete' for x in independent):
            expected=1
            for x in independent:expected*=x['count']
            # Enumerating the entire independent passage may hit the cap.
            previous=cases[-2]
            if previous['structures']['status']=='complete':assert expected==previous['structures']['count']
            previous['independent_sentence_structural_product']=expected
        cases[-2]['individual_sentences']=independent
    manifest={'files_sha256':{p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in ('src/voynich_smt/joint_grammar.py',str(Path(__file__)))},'datasets':datasets,'seeds':[3109],'structural_enumeration_cap':2000,'dictionary_enumeration_cap':1000,'per_check_timeout_ms':10000,'grammar':'Explicit finite artificial fragment with NP adjectives, complete valency, subject agreement, selected-analysis agreement/government, all constituent permutations. No semantic or learned scores.','projection':'Sentence dependency roles and token-index heads; lexical identities and inflection choices marginalized.','scope':'Hand-constructed synthetic identifiability diagnostic, not unrestricted Latin or held-out natural-text recovery.'}
    report={'cases':cases,'manifest_sha256':digest(manifest),'total_elapsed_seconds':time.perf_counter()-started}
    if validate:
        assert json.loads((OUT/'manifest.json').read_text())==manifest
        assert fingerprint(json.loads((OUT/'report.json').read_text()))==fingerprint(report)
        write_json(OUT/'validation.json',{'complete_experiment_replay':True,'counts_sat_unsat_and_independent_products_reproduced':True,'examples_pass_concrete_constraint_audit':True})
    else:write_json(OUT/'manifest.json',manifest);write_json(OUT/'report.json',report)
    print('FINISHED',len(cases),'cases',flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--validate',action='store_true');run(p.parse_args().validate)
