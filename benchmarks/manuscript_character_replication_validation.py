"""Split/probability reconstruction for manuscript replication."""
from collections import Counter
import json
from benchmarks import manuscript_character_replication as m
from benchmarks import character_prediction as pred
from benchmarks.character_prediction_validation import manual
from benchmarks.character_calibration import summarize
from voynich_smt.data.corpus import digest, write_json


def inventory(blocks): return Counter((b['folio'],pred.prior.position_bin(n,4),len(w),''.join(w)) for b in blocks for n,w in zip(b['positions'],b['words']))


def validate():
    p=m.prepare(); raw=json.loads(__import__('pathlib').Path('data/processed/zl-eva.json').read_text())['records']; original=pred.prepare(); reports=[]; results={}; checked=0
    a=p['cases']['A']['heldout']; b=p['cases']['B']['heldout']; extra=p['cases']['additional-blocks']['heldout']; used=set()
    assert not {x['folio'] for x in a}&{x['folio'] for x in b}
    for block in a+b+extra:
        assert block['folio'] not in p['excluded_folios']; indices=set(range(block['start'],block['end_exclusive'])); assert not used&indices; used|=indices
        records=raw[block['start']:block['end_exclusive']]; assert len(records)==32
        assert block['words']==[r['tokens'] for r in records] and block['positions']==[r['word_in_locus'] for r in records]
        assert block['line_ids']==[f"{r['folio']}:{r['locus']}:{r['physical_line']}" for r in records]
    for i in range(1,8):
        r=json.loads((m.OUT/f'iteration-{i}.json').read_text()); assert r['plan']==json.loads((m.OUT/f'plan-{i}.json').read_text())
        assert r['plan']['prepared_sha256']==digest(p) and r['plan']['previous_sha256']==(digest(reports[-1]) if reports else None) and r['plan']['cases']==p['stages'][str(i)]; reports.append(r)
        for name,result in r['results'].items():
            case=p['cases'][name]; results[name]=result
            if case['variant']=='shuffle': assert inventory(case['train'])==inventory(original['development']) and inventory(case['heldout'])==inventory(a+b)
            for row,block in zip(result['rows'],case['heldout'],strict=True):
                for spec,gain in ((case['spec'],None),({**case['spec'],'gate':'none'},'gain_position')):
                    for t,(loss,novel) in zip(row['tokens'],manual(case['train'],block,spec),strict=True):
                        assert abs((t['loss'] if gain is None else t['loss']+t[gain])-loss)<1e-10 and t['novel']==novel; checked+=1
            assert pred.aggregate(result['rows'])==result and summarize(result)==r['summary'][name]
    originals={f['folio']:f for name in ('A','B') for f in results[name]['folios']}
    for name in (f'shuffle-{s}' for s in (30001,30002,30003)):
        for f in results[name]['folios']:
            base=originals[f['folio']]; assert abs((f['bits_per_character']+f['gain_position'])-(base['bits_per_character']+base['gain_position']))<1e-10
    write_json(m.OUT/'validation.json',{'status':'passed','stages':7,'independent_word_model_scores':checked,'unique_new_word_occurrences':len(used),'new_folios':116,'summary':{n:summarize(r) for n,r in results.items()},'scope':'Raw fields, statistical-folio exclusions, primary/additional disjointness, plan chains, independent likelihood scores and null inventories/baselines verified.'}); print('Validated',checked,'word/model scores;',len(used),'new occurrences',flush=True)

if __name__=='__main__': validate()
