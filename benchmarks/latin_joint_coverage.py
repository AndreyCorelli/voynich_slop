"""Does an incomplete grammar reject unseen constructions or reinterpret them?"""
import argparse,hashlib,json,time
from dataclasses import asdict
from pathlib import Path
import z3
from benchmarks.latin_joint_identifiability import corpus,lexicon,encode,fingerprint
from voynich_smt.joint_grammar import Reading
from voynich_smt.joint_grammar_coverage import CoverageGrammar
from voynich_smt.data.corpus import write_json,digest
OUT=Path('experiments/results/latin-joint-coverage')


def vocabulary(level):
    e=lexicon('base' if level=='lean' else 'rich')
    for w,g in (('pueri','M'),('puellae','F'),('rosae','F')):
        e.setdefault(w,[])
        for r in (Reading('N','GEN','S',g),Reading('N','NOM','P',g)):
            if r not in e[w]:e[w].append(r)
    e['et']=[Reading('CC')];e['dormiunt']=[Reading('V',number='P',valency='intransitive')]
    return e


def datasets():
    base=corpus()[:6]
    omitted=(['puerum','amat'],['obj','root'],[1,-1])
    genitive=(['puella','pueri','dormit'],['nsubj','nmod:gen','root'],[2,0,-1])
    coord=(['puella','et','puer','dormiunt'],['nsubj','cc','conj','root'],[3,2,0,-1])
    allgen=[genitive,(['puella','currit'],['nsubj','root'],[1,-1]),(['puer','currit'],['nsubj','root'],[1,-1]),(['puer','puellae','dormit'],['nsubj','nmod:gen','root'],[2,0,-1]),(['rosa','currit'],['nsubj','root'],[1,-1]),(['rosa','rosae','dormit'],['nsubj','nmod:gen','root'],[2,0,-1])]
    # Same construction generated in changed constituent orders; fixed lexical meanings.
    reordered=[]
    for words,roles,heads in base:
        order=list(reversed(range(len(words))));remap={old:new for new,old in enumerate(order)}
        reordered.append(([words[i] for i in order],[roles[i] for i in order],[remap[heads[i]] if heads[i]>=0 else -1 for i in order]))
    return [('covered-six','covered',base),('covered-reordered','covered',reordered),('omitted-subject-alone','omitted_subject',[omitted]),('omitted-subject-repeated','omitted_subject',[omitted]*4),('omitted-subject-with-context','omitted_subject',base+[omitted]),('genitive-alone','genitive',[genitive]),('genitive-coherent-six','genitive',allgen),('genitive-with-context','genitive',base+[genitive]),('coordination-alone','coordination',[coord]),('coordination-with-context','coordination',base+[coord])]


def query_truth(solver,truth):
    exact=solver.query_structure(truth['roles'],truth['heads'])
    wrong=solver.query_structure(truth['roles'],truth['heads'],different=True)
    solver.solver.push();solver.solver.add(*[v==solver.word_index[truth['dictionary'][t]] for t,v in solver.mapping.items()]);fixed=solver.solver.check();fixed_structure=solver.query_structure(truth['roles'],truth['heads']);solver.solver.pop()
    return {'original_structure':exact,'wrong_structure':wrong,'true_dictionary_status':str(fixed),'true_dictionary_and_structure':fixed_structure}


def audit_example(example,lex,broad):
    for s in example['sentences']:
        rr=s['readings'];roles=s['roles'];heads=s['heads'];roots=[i for i,r in enumerate(roles) if r=='root'];assert len(roots)==1;root=roots[0];v=rr[root];assert v['pos']=='V' and heads[root]==-1
        for w,r in zip(s['words'],rr):assert Reading(**r) in lex[w]
        subjects=[i for i,r in enumerate(roles) if r=='nsubj'];objects=[i for i,r in enumerate(roles) if r=='obj'];assert len(subjects)<=1
        assert len(objects)==(v['valency']=='transitive')
        if not broad:assert len(subjects)==1 and not any(r in ('nmod:gen','cc','conj') for r in roles)
        for i in subjects:assert rr[i]['pos']=='N' and rr[i]['case']=='NOM' and heads[i]==root
        if any(r=='conj' for r in roles):
            assert subjects and v['number']=='P';sub=subjects[0];conj=[i for i,r in enumerate(roles) if r=='conj'];cc=[i for i,r in enumerate(roles) if r=='cc'];assert len(conj)==len(cc)==1
            assert rr[conj[0]]['pos']=='N' and rr[conj[0]]['case']=='NOM' and heads[conj[0]]==sub
            assert rr[cc[0]]['pos']=='CC' and heads[cc[0]]==conj[0]
        elif subjects:assert rr[subjects[0]]['number']==v['number']
        for i in objects:assert rr[i]['pos']=='N' and rr[i]['case']=='ACC' and heads[i]==root
        for i,r in enumerate(roles):
            if r=='nmod:gen':assert broad and rr[i]['pos']=='N' and rr[i]['case']=='GEN' and rr[heads[i]]['pos']=='N'
            if r=='amod':assert rr[i]['pos']=='ADJ' and rr[heads[i]]['pos']=='N' and all(rr[i][f]==rr[heads[i]][f] for f in ('case','number','gender'))
            if r=='case':assert rr[i]['pos']=='ADP' and rr[heads[i]]['case']==rr[i]['government']
            if r=='xcomp':assert rr[i]['pos']=='ADJ' and rr[i]['case']=='NOM' and subjects and all(rr[i][f]==rr[subjects[0]][f] for f in ('number','gender'))
        for i in range(len(roles)):
            seen=set();j=i
            while j!=-1:assert j not in seen;seen.add(j);j=heads[j]
            assert root in seen


def run(validate=False):
    OUT.mkdir(parents=True,exist_ok=True);started=time.perf_counter();plans=datasets();cases=[];inputhashes={}
    # All plans/parameters fixed before any inference.
    manifest={'files_sha256':{str(p):hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in (Path(__file__),Path('src/voynich_smt/joint_grammar_coverage.py'),Path('src/voynich_smt/joint_grammar.py'),Path('benchmarks/latin_joint_identifiability.py'))},'plan':[{'name':n,'family':f,'sentences':len(rows)} for n,f,rows in plans],'lexicons':['lean','richer'],'grammars':['narrow','broader'],'structure_cap':512,'per_check_timeout_ms':10000,'seed':3219,'candidate_policy':'Every type gets the same full surface inventory; no truth-derived filtering.','scope':'Hand-constructed synthetic grammar-mismatch controls; broader generator covers omission/genitives/coordination. Both grammars remain finite fragments. No learned score/confidence.'}
    for level in ('lean','richer'):
        lex=vocabulary(level);settings={'max_adjectives':0 if level=='lean' else 2,'allow_pp':level=='richer','noun_attachment':level=='richer'}
        for name,family,rows in plans:
            inputs,truth=encode(rows,seed=3219);key=level+'/'+name
            public={**inputs,'lexicon':{w:[asdict(r) for r in rr] for w,rr in lex.items()},'settings':settings}
            inputhashes[key]=digest(public);write_json(OUT/'inputs'/level/f'{name}.json',public);write_json(OUT/'truth'/level/f'{name}.json',truth)
            for broad in (False,True):
                solver=CoverageGrammar(lex,inputs['ciphertext'],broad=broad,**settings);solutions=solver.enumerate('structure',limit=512);queries=query_truth(solver,truth)
                if broad:assert queries['true_dictionary_and_structure']['status']=='sat',(key,queries)
                if family=='covered':assert queries['true_dictionary_and_structure']['status']=='sat',(key,queries)
                for ex in solutions['examples']+[q['example'] for q in (queries['original_structure'],queries['wrong_structure'],queries['true_dictionary_and_structure']) if q['example']]:audit_example(ex,lex,broad)
                status='no_solution' if solutions['count']==0 and solutions['status']=='complete' else 'unique_original' if solutions['count']==1 and solutions['status']=='complete' and queries['original_structure']['status']=='sat' else 'unique_wrong' if solutions['count']==1 and solutions['status']=='complete' and queries['original_structure']['status']=='unsat' else 'ambiguous' if solutions['count']>1 else 'unknown'
                cases.append({'inventory':level,'case':name,'family':family,'broader_solver':broad,'sentences':len(rows),'candidate_surfaces':len(lex),'cipher_types':len(truth['dictionary']),'classification':status,'solutions':solutions,**queries})
                print('CASE',key,'broad',broad,'count',solutions['count'],solutions['status'],status,'truekey',queries['true_dictionary_status'],flush=True)
    manifest['inputs_sha256']=inputhashes;report={'manifest_sha256':digest(manifest),'cases':cases,'total_elapsed_seconds':time.perf_counter()-started}
    if validate:
        assert json.loads((OUT/'manifest.json').read_text())==manifest
        assert fingerprint(json.loads((OUT/'report.json').read_text()))==fingerprint(report)
        write_json(OUT/'validation.json',{'full_replay':True,'counts_sat_unsat_and_classifications_reproduced':True,'all_saved_witnesses_concretely_audited':True})
    else:write_json(OUT/'manifest.json',manifest);write_json(OUT/'report.json',report)
    print('FINISHED',len(cases),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--validate',action='store_true');run(p.parse_args().validate)
