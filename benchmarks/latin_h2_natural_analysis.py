"""Independent source/coverage audit and summary of frozen natural H2 cases."""
from collections import Counter
from itertools import product
import json
import random
from benchmarks import latin_h2_natural as experiment
from voynich_smt.data.corpus import digest, write_json


def calculate():
    p=experiment.prepare(); compact=experiment.baseline.compact
    report=json.loads((compact.OUT/'report.json').read_text())
    automata={mode:compact.load_automaton(row['automaton']) for mode,row in report['modes'].items()}
    raw=json.loads(open(p['source_path']).read())
    previous=json.loads((experiment.passages.OUT/'prepared.json').read_text())
    selected=experiment.passages.select_passages(raw['records'],max(x['record_end_exclusive'] for x in previous['passages']),set(report['modes']['through-medieval-rare']['alphabet']['symbols']),7)
    assert selected==p['passages']
    summary=[]
    for i,(block,audit) in enumerate(zip(selected,p['audits'])):
        coverage={mode:{'missing_training':[w for w in block['train'] if not a.accepts(w)],'missing_held':[w for w in block['held'] if not a.accepts(w)]} for mode,a in automata.items()}
        assert coverage==audit['coverage']
        symbols=report['modes']['through-medieval-rare']['alphabet']['symbols']
        codes=[''.join(x) for x in product('qrstuvwx',repeat=2)]; random.Random(10201+i).shuffle(codes)
        key={letter:codes[2*j:2*j+2] for j,letter in enumerate(symbols)}
        assert len({c for cs in key.values() for c in cs})==2*len(key)
        positive,held=experiment.baseline.encrypt(block['train'],block['held'],key)
        observed={c for w in positive for c in w}
        unseen=sorted({c for w in held for c in w}-observed)
        assert unseen==audit['unseen_held_codes']
        admitted=not coverage['through-medieval-rare']['missing_training'] and not unseen
        assert admitted==audit['admitted']
        row={'id':audit['id'],'admitted':admitted,'training_words':48,'holdout_words':6,'novel_holdout_occurrences':sum(w not in block['train'] for w in block['held']),
             'observed_codes':len(observed),'training_letters':len(set(''.join(block['train']))),'missing_training':coverage['through-medieval-rare']['missing_training'],'unseen_held_codes':unseen}
        if admitted:
            fixture=next(f for f in p['fixtures'] if f['id']==audit['id'])
            assert fixture['truth']=={'train':block['train'],'held':block['held'],'key':key}
            assert fixture['arms']['positive']==positive and fixture['held_cipher']==held
            folder=experiment.OUT/audit['id']; results={task:json.loads((folder/f'{task}-result.json').read_text()) for task in ('positive','shuffle','ambiguity')}
            first=results['positive']; row.update(first_status=first['status'],training_exact=first.get('training_exact'),held_exact=first.get('held_exact'),shuffle_status=results['shuffle']['status'],alternative_status=results['ambiguity']['status'],timings=first.get('timings'))
            if first['status']=='SAT':
                true={c:l for l,cs in key.items() for c in cs if c in observed}
                row['first_key_exact']=first['recovered_key']==true
                assert max(Counter(first['recovered_key'].values()).values())<=2
        summary.append(row)
    return {'prepared_sha256':digest(p),'cases':summary,'scope':'Seven selected cases retained. Coverage failures are not UNSAT. First-key exactness only; no alternative rescoring. Adjacent natural continuations, same source, not independent languages/manuscript evidence.'}


if __name__=='__main__':
    experiment.validate(); result=calculate(); path=experiment.OUT/'analysis.json'
    if path.exists(): assert json.loads(path.read_text())==result
    else: write_json(path,result)
    print(json.dumps(result,indent=2))
