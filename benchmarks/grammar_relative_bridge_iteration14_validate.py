"""Replay every decision with a frozen independent morphology snapshot."""
import hashlib
import json
from pathlib import Path
from voynich_smt.grammar_diagnostic import LatinAdapter,MorphAnalysis
from voynich_smt.relative_bridge import bridge
from benchmarks.grammar_relative_bridge_iteration14 import OUT,NINE,TEN,RESERVE,load,save,summarize

class FrozenBridgeAdapter(LatinAdapter):
    def __init__(self,lattice):self.lattice=lattice
    def analyze(self,word):
        return tuple(MorphAnalysis(r['pos'],tuple(map(tuple,r['features']))) for r in self.lattice[word])


def run():
    manifest=load(OUT/'manifest.json')
    for name,sha in manifest['inputs'].items():
        assert hashlib.sha256(Path(name).read_bytes()).hexdigest()==sha,name
    adapter=FrozenBridgeAdapter(load(OUT/'morphology-lattice.json'))
    controlled=load(OUT/'controlled.json');checks=0;witnesses=0
    for case in controlled:
        for consistent,key in [(True,'result'),(False,'mixed_readings')]:
            actual=bridge(case['tokens'],case['predicates'],case['marker'],case['child'],adapter,consistent=consistent)
            assert json.loads(json.dumps(actual))==case[key];checks+=1
        assert case['result']['parents']==case['expected_parents']
    dev=load(NINE/'development-truth.json');old=load(TEN/'predictions.json')
    rows=load(OUT/'predictions.json');report=load(OUT/'report.json')
    comparison={}
    for r in rows:
        s=dev[r['stream']]
        pred=next(x['prediction'] for x in old if (x['stream'],x['training'],x['features'],x['markers'],x['condition'])==(r['stream'],'oof','interactions','predicted','unrestricted'))
        scopes=({int(m):v['target'] for m,v in s['markers'].items() if v['kind']=='relative'} if r['mode']=='reference_scope' else
            {m['position']:m['target'] for m in pred['marker_attachments'] if 'relative' in m['kinds'] and m['target'] is not None})
        actual=({'status':'missing_scope','parents':[],'bridges':[]} if r['child'] is None else
            bridge(s['tokens'],s['finite'],r['marker'],r['child'],adapter,scopes=tuple(scopes.items()),
                boundaries=s['boundaries'] if r['boundaries']=='reference' else ()))
        assert json.loads(json.dumps(actual))==r['result'];checks+=1
        for w in actual['bridges']:
            assert w['nominal']==w['governing_nominal']
            for position,key in [(r['marker'],'pronoun'),(w['antecedent'],'nominal'),(r['child'],'child_verb'),(w['governor'],'governing_verb')]:
                v=w[key];reading=MorphAnalysis(v['pos'],tuple(map(tuple,v['features'])))
                assert reading in adapter.analyze(s['tokens'][position])
            witnesses+=1
    for mode in ('reference_scope','predicted_scope'):
        for bounded in ('hidden','reference'):
            selected=[r for r in rows if (r['mode'],r['boundaries'])==(mode,bounded)]
            assert summarize(selected)==report['natural'][f'{mode}/{bounded}']
            unique=[r for r in selected if r['result']['status']=='unique_parent']
            correct=lambda r:r['scope_correct'] and r['result']['parents']==[r['reference_parent']]
            comparison[f'{mode}/{bounded}']={'claims':len(unique),
                'baseline_correct':sum(r['scope_correct'] and r['baseline_parent']==r['reference_parent'] for r in unique),
                'bridge_correct':sum(correct(r) for r in unique),
                'corrections':sum(correct(r) and r['baseline_parent']!=r['reference_parent'] for r in unique),
                'regressions':sum(not correct(r) and r['baseline_parent']==r['reference_parent'] for r in unique)}
    reserved=load(RESERVE);reserved_ids=set()
    # Registry has its own independent validator from iteration13; pin byte hash
    # here and check no reserved sentence ID occurs among scored development IDs.
    def ids(obj):
        if isinstance(obj,dict):
            for k,v in obj.items():
                if k=='sent_id':yield str(v)
                else:yield from ids(v)
        elif isinstance(obj,list):
            for v in obj:yield from ids(v)
    reserved_ids=set(ids(reserved))
    assert reserved_ids and not reserved_ids & {s['sent_id'] for d in dev for s in d['sentences']}
    save(OUT/'validation.json',{'passed':True,'replayed_decisions':checks,'natural_witnesses_checked':witnesses,
        'reserved_ids_disjoint':len(reserved_ids),'baseline_on_unique_claims':comparison,
        'scope':'Exact independent artifact replay and lexical-membership checks, not an independent linguistic adjudication.'})
    print(load(OUT/'validation.json'))

if __name__=='__main__':run()
