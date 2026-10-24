"""Project new-context evidence onto old sentences; isolate intrinsic parse ambiguity."""
import hashlib,json,time
from pathlib import Path
import z3
from benchmarks.latin_joint_identifiability import OUT,corpus,encode,lexicon,audit_example
from voynich_smt.joint_grammar import JointGrammar
from voynich_smt.data.corpus import write_json


def project(solver,variables,limit=10000):
    solver.solver.push();n=0;started=time.perf_counter();status='limit'
    while n<limit:
        result=solver.solver.check()
        if result!=z3.sat:status='complete' if result==z3.unsat else 'unknown';break
        m=solver.solver.model();vs=[m.eval(v).as_long() for v in variables];n+=1
        solver.solver.add(z3.Or([v!=x for v,x in zip(variables,vs)]))
    solver.solver.pop();return {'count':n,'status':status,'elapsed_seconds':time.perf_counter()-started}


def run():
    report=json.loads((OUT/'report.json').read_text());result=[]
    for c in report['cases']:
        if not c['shared_dictionary']:continue
        level=c['level'];n=c['sentence_count'];inputs,truth=encode(corpus()[:n]);lex=lexicon(level);solver=JointGrammar(lex,inputs['ciphertext'],**c['grammar']);prefix_tokens=sum(len(s) for s in inputs['ciphertext'][:6])
        prefix=project(solver,solver.structures[:2*prefix_tokens]);first=project(solver,solver.structures[:2*len(inputs['ciphertext'][0])])
        solver.solver.push();solver.solver.add(*[v==solver.word_index[truth['dictionary'][t]] for t,v in solver.mapping.items()]);fixed=solver.enumerate('structure');wrongfixed=solver.query_structure(truth['roles'],truth['heads'],different=True);solver.solver.pop()
        for ex in fixed['examples']:audit_example(ex,lex)
        result.append({'case':c['case'],'first_sentence_structure':first,'first_six_sentences_structure':prefix,'structures_with_true_dictionary':{'count':fixed['count'],'status':fixed['status']},'wrong_structure_with_true_dictionary':wrongfixed})
        print('PROJECT',c['case'],first['count'],prefix['count'],'true_dictionary',fixed['count'],flush=True)
    # A hand-fixed counterexample isolates nominative/accusative syncretism.
    inputs,truth=encode(corpus()[:6]);lex=lexicon('syncretic');solver=JointGrammar(lex,inputs['ciphertext'],max_adjectives=0,allow_pp=False)
    alternative=dict(truth['dictionary']);reverse={w:t for t,w in alternative.items()};alternative[reverse['puella']]='bellum';alternative[reverse['puerum']]='donum'
    solver.solver.add(*[v==solver.word_index[alternative[t]] for t,v in solver.mapping.items()]);rr=[list(x) for x in truth['roles']];hh=[list(x) for x in truth['heads']];rr[0]=['obj','nsubj','root']
    witness=solver.query_structure(rr,hh);assert witness['status']=='sat';audit_example(witness['example'],lex)
    # The single globally mapped surface bellum is nominative in one occurrence,
    # accusative in another; that is legitimate contextual analysis, not key drift.
    first=witness['example']['sentences'][0]['readings'][0];second=witness['example']['sentences'][1]['readings'][0]
    assert first['case']=='ACC' and second['case']=='NOM'
    audit={'projected_cases':result,'syncretic_counterexample':witness,'note':'Prefix projections hold the lexicon fixed; complete full-passage counts can grow merely by adding sentence positions. True dictionary only a diagnostic, never an input to primary runs.'}
    write_json(OUT/'audit.json',audit)
    paths=[Path(__file__),OUT/'report.json',Path('src/voynich_smt/joint_grammar.py')];write_json(OUT/'audit-manifest.json',{'sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}})
if __name__=='__main__':run()
