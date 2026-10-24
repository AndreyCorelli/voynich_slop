"""Check discovered alternative keys on holdouts and richer matched cases."""
import hashlib
import json
from pathlib import Path
from benchmarks import latin_h2_layout as experiment
from voynich_smt.data.corpus import digest, write_json


def calculate():
    root=experiment.OUT; p=json.loads((root/'prepared.json').read_text())
    assert json.loads((root/'validation.json').read_text())['verified']
    for path,checksum in p['code_sha256'].items(): assert digest(Path(path).read_text())==checksum
    full=experiment.baseline.compact.prepare()['inventories']['upstream-default']['inventory']
    assert hashlib.sha256(Path(full['path']).read_bytes()).hexdigest()==full['sha256']
    eligible={w for w in experiment.baseline.compact.inventory_lines(full['path']) if 3<=len(w)<=6}
    records=[]
    for rung in p['rungs']:
        fixture=rung['fixtures'][0]; folder=root/rung['job']/fixture['id']
        exclusion=json.loads((folder/'ambiguity-result.json').read_text())
        if exclusion['status']!='SAT': continue
        first=json.loads((folder/'positive-result.json').read_text()); key=exclusion['alternative_key']
        a=experiment.baseline.compact.load_automaton(fixture['case']['automaton'])
        assert key!=first['recovered_key'] and exclusion['verified']
        train=[''.join(key[c] for c in word) for word in fixture['arms']['positive']]
        assert train==exclusion['training_words'] and all(a.accepts(w) for w in train)
        held=[''.join(key[c] for c in word) for word in fixture['held_cipher']]
        checks=[]
        for target in p['rungs']:
            tf=target['fixtures'][0]
            if target['layout']!=rung['layout'] or tf['id']!=fixture['id'] or len(tf['truth']['train'])<=len(fixture['truth']['train']): continue
            assert tf['inventory']==fixture['inventory'] and tf['truth']['key']==fixture['truth']['key']
            n=len(fixture['truth']['train'])//2
            assert tf['arms']['positive'][:n]==fixture['arms']['positive'][:n]
            assert all(c in key for word in tf['arms']['positive'] for c in word)
            failures=[]
            for i,(word,cipher) in enumerate(zip(tf['truth']['train'],tf['arms']['positive'])):
                fitted=''.join(key[c] for c in cipher)
                if not a.accepts(fitted):
                    failures.append({'position':i+1,'truth':word,'alternative':fitted,'new_type':word not in fixture['truth']['train'],
                                     'first_pass':i<len(tf['truth']['train'])//2,'in_complete_length_inventory':fitted in eligible})
            checks.append({'job':target['job'],'fixture_sha256':digest(tf),'first_pass_prefix_unchanged':True,'invalid_training_words':failures})
        records.append({'job':rung['job'],'fixture_sha256':digest(fixture),'first_result_sha256':digest(first),'alternative_result_sha256':digest(exclusion),
                        'code_changes':[{'code':c,'first':first['recovered_key'][c],'alternative':letter} for c,letter in sorted(key.items()) if first['recovered_key'][c]!=letter],
                        'training_changes':[{'position':i+1,'truth':t,'alternative':w} for i,(t,w) in enumerate(zip(fixture['truth']['train'],train)) if t!=w],
                        'first_held_exact':first['held_exact'],'alternative_held_words':held,'alternative_held_exact':sum(x==y for x,y in zip(held,fixture['truth']['held'])),
                        'alternative_held_members':sum(a.accepts(w) for w in held),'richer_case_checks':checks})
    return {'prepared_sha256':digest(p),'analysis_code_sha256':digest(Path(__file__).read_text()),'complete_inventory_sha256':full['sha256'],'records':records,
            'scope':'Diagnostic continuation of verified alternative keys and checks against richer cases. First-key scores unchanged; no alternative selection, new solver run or universal uniqueness inference.'}


if __name__=='__main__':
    p=calculate(); path=experiment.OUT/'alternative-analysis.json'
    if path.exists(): assert json.loads(path.read_text())==p
    else: write_json(path,p)
    print('Verified alternative continuation and richer-case checks:',len(p['records']))
