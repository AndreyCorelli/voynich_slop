"""Find forced relationships by direct SAT queries, independent of enumeration caps."""
import hashlib,json
from collections import Counter
from pathlib import Path
import z3
from voynich_smt.joint_grammar import Reading
from voynich_smt.joint_grammar_coverage import CoverageGrammar
from benchmarks.latin_joint_coverage import OUT
from voynich_smt.data.corpus import write_json


def run():
    report=json.loads((OUT/'report.json').read_text());results=[]
    for case in report['cases']:
        level,name=case['inventory'],case['case'];public=json.loads((OUT/'inputs'/level/f'{name}.json').read_text());truth=json.loads((OUT/'truth'/level/f'{name}.json').read_text());lex={w:[Reading(**r) for r in rr] for w,rr in public['lexicon'].items()}
        solver=CoverageGrammar(lex,public['ciphertext'],broad=case['broader_solver'],**public['settings']);status=solver.solver.check();row={'inventory':level,'case':name,'broader_solver':case['broader_solver'],'status':str(status)}
        if status==z3.sat:
            witness=solver.solver.model();expected=[];names=[]
            for si,(roles,heads) in enumerate(zip(truth['roles'],truth['heads'])):
                expected.extend(solver.rolelabels.index(r) for r in roles);expected.extend(heads);names.extend([('role',si,j) for j in range(len(roles))]+[('head',si,j) for j in range(len(heads))])
            forced=[];ambiguous=unknown=0
            for v,gold,location in zip(solver.structures,expected,names):
                value=witness.eval(v).as_long();solver.solver.push();solver.solver.add(v!=value);other=solver.solver.check();solver.solver.pop()
                if other==z3.unsat:forced.append({'kind':location[0],'sentence':location[1],'token':location[2],'value':value,'correct':value==gold})
                elif other==z3.sat:ambiguous+=1
                else:unknown+=1
            row.update({'forced':forced,'forced_correct':sum(x['correct'] for x in forced),'forced_wrong':sum(not x['correct'] for x in forced),'ambiguous_variables':ambiguous,'unknown_queries':unknown,'total_structure_variables':len(expected)})
        results.append(row)
        print('BACKBONE',level,name,case['broader_solver'],row.get('forced_correct'),row.get('forced_wrong'),flush=True)
    mismatches=[c for c in report['cases'] if c['family']!='covered' and not c['broader_solver']]
    summary=Counter(c['classification'] for c in mismatches)
    counts=Counter(('broader' if c['broader_solver'] else 'narrow',c['classification']) for c in report['cases'])
    audit={'forced_relationships':results,'unsupported_narrow_case_classifications':dict(summary),'classifications':{str(k):v for k,v in counts.items()},'note':'Forced means conditional logical necessity under this grammar/candidate pool, not confidence in grammar adequacy. Gold used only to audit correctness.'}
    write_json(OUT/'audit.json',audit);paths=[Path(__file__),OUT/'report.json',Path('src/voynich_smt/joint_grammar_coverage.py')];write_json(OUT/'audit-manifest.json',{'sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}})
    print('SUMMARY',dict(summary),flush=True)
if __name__=='__main__':run()
