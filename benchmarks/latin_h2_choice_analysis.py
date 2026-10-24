"""Verify complete dictionary coverage and why discovered aliases fail random choice."""
from collections import Counter
import hashlib
import json
from pathlib import Path
from benchmarks import latin_h2_choice as experiment
from voynich_smt.data.corpus import digest, write_json


def calculate():
    root=experiment.OUT; p=json.loads((root/'prepared.json').read_text())
    assert json.loads((root/'validation.json').read_text())['verified']
    for path,checksum in p['code_sha256'].items(): assert digest(Path(path).read_text())==checksum
    full=p['complete_source_inventory']; assert hashlib.sha256(Path(full['path']).read_bytes()).hexdigest()==full['sha256']
    eligible={w for w in experiment.baseline.compact.inventory_lines(full['path']) if 3<=len(w)<=6}
    metadata=p['rungs'][0]['fixtures'][0]['inventory']
    assert hashlib.sha256(Path(metadata['path']).read_bytes()).hexdigest()==metadata['sha256']
    words=set(experiment.baseline.compact.inventory_lines(metadata['path']))
    assert words==eligible and len(words)==metadata['word_count']==p['eligible_count']
    records=[]
    for cyclic,random in zip(p['rungs'][::2],p['rungs'][1::2]):
        cf,rf=cyclic['fixtures'][0],random['fixtures'][0]
        assert cf['inventory']==rf['inventory']==metadata
        cfolder=root/cyclic['job']/cf['id']; rfolder=root/random['job']/rf['id']
        first=json.loads((cfolder/'positive-result.json').read_text()); exclusion=json.loads((cfolder/'ambiguity-result.json').read_text())
        if exclusion['status']!='SAT': continue
        true={code:letter for letter,codes in cf['truth']['key'].items() for code in codes if code in first['recovered_key']}
        key=first['recovered_key'] if first['recovered_key']!=true else exclusion['alternative_key']
        assert key!=true
        a=experiment.baseline.compact.load_automaton(cf['case']['automaton'])
        cwords=[''.join(key[c] for c in word) for word in cf['arms']['positive']]
        rwords=[''.join(key[c] for c in word) for word in rf['arms']['positive']]
        assert all(a.accepts(w) for w in cwords)
        same_hist=Counter(''.join(cwords))==Counter(''.join(rwords)); assert same_hist
        invalid=[{'position':i+1,'truth':t,'under_cyclic_alias':w} for i,(t,w) in enumerate(zip(rf['truth']['train'],rwords)) if not a.accepts(w)]
        rexclusion=json.loads((rfolder/'ambiguity-result.json').read_text())
        if rexclusion['status']=='UNSAT': assert invalid
        records.append({'pair':cyclic['pair'],'cyclic_fixture_sha256':digest(cf),'random_fixture_sha256':digest(rf),
                        'cyclic_first_sha256':digest(first),'cyclic_exclusion_sha256':digest(exclusion),
                        'alias_origin':'first-fit' if key==first['recovered_key'] else 'exclusion-fit',
                        'code_changes':[{'code':code,'generating':true[code],'alias':letter} for code,letter in sorted(key.items()) if true[code]!=letter],
                        'alias_plaintext_histogram_identical_across_choices':same_hist,'invalid_random_training_words':invalid})
    return {'prepared_sha256':digest(p),'analysis_code_sha256':digest(Path(__file__).read_text()),'complete_inventory_forms':len(eligible),
            'dictionary_equals_complete_length_subset':True,'records':records,
            'scope':'Check full finite-inventory length subset and discovered cyclic aliases against matched random ciphertext. No new fits, score changes, key selection or frequency-prior claim.'}


if __name__=='__main__':
    p=calculate(); path=experiment.OUT/'alias-analysis.json'
    if path.exists(): assert json.loads(path.read_text())==p
    else: write_json(path,p)
    print('Verified complete dictionary and cyclic-alias checks:',len(p['records']))
