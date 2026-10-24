"""Frozen replay, independent witness accounting/role checks and metric replay."""
import hashlib
from collections import Counter
from benchmarks.grammar_construction_spans_iteration18 import OUT,SEVENTEEN,NINE,SIXTEEN,RESERVE,load
from benchmarks.grammar_construction_spans_iteration18_evaluate import evaluate
from benchmarks.grammar_relative_constituents_iteration15_validate import FrozenAdapter,normalized
from voynich_smt.construction_spans import analyze,decode


def check_witness(tokens,predicates,unit,result,adapter):
    assert result['status']=='supported'
    fixed={int(p):decode(v) for p,v in unit['readings'].items()}
    selected={};covered=[];slots=[];embedded=set()
    def add(p,value):
        reading=decode(value)
        assert reading in adapter.analyze(tokens[p])
        assert p not in selected or selected[p]==reading
        assert p not in fixed or fixed[p]==reading
        selected[p]=reading
        return reading
    for segment in result['witness']:
        positions=segment['positions'];covered.extend(positions);role=segment['role']
        if 'phrase' not in segment:
            assert len(positions)==1
            p=positions[0];value=segment['reading']
            if value is not None:r=add(p,value)
            else:
                assert role=='coordinator' and unit['cue']['kind']=='paired_ne_c'
                assert tokens[p] in ('ne','c')
            if role=='governor':assert p==unit['parent']
            elif role=='infinitive':assert p in unit['members']
            elif role=='adverb':assert r.pos=='ADV'
            elif role=='particle':assert r.pos=='CONJ' and tokens[p] in ('enim','autem','ergo','igitur')
            else:assert role=='coordinator'
            continue
        phrase=segment['phrase'];head=phrase['head'];target=segment['target']
        assert positions==list(range(phrase['start'],phrase['end']))
        assert set(map(int,phrase['analyses']))==set(positions)
        readings={int(p):add(int(p),v) for p,v in phrase['analyses'].items()}
        noun=readings[head];assert noun.pos in ('N','PRON')
        for feature,value in phrase['agreement'].items():
            source=noun.get(feature)
            assert source in (None,'X','0',value) or source=='C' and value in ('M','F')
        case=noun.get('Case');verb=fixed[target]
        if role=='matrix_subject':
            person='1' if tokens[head] in ('ego','nos') else '2' if tokens[head] in ('tu','uos','vos') else '3'
            assert case=='NOM' and target==unit['parent'] and phrase['agreement']['Number']==verb.get('Number') and person==verb.get('Person')
        elif role=='object':assert case=='ACC' and (verb.get('VerbKind')=='TRANS' or verb.get('VerbRoot') in ('hab','loc'))
        elif role=='embedded_subject':
            assert case=='ACC' and any(p.get('embedded_subject')==head and p['nonfinite']==target for p in unit['parts'])
            embedded.add(target)
        elif role=='dative_argument':assert case=='DAT' and (verb.get('VerbKind')=='DAT' or verb.get('VerbRoot')=='noc')
        elif role=='genitive_argument':assert case=='GEN' and verb.get('VerbKind')=='GEN'
        elif role=='ablative_argument':assert case=='ABL' and verb.get('VerbKind')=='ABL'
        elif role=='passive_instrument':assert case=='ABL' and target==unit['parent'] and verb.get('Voice')=='PASSIVE'
        elif role=='prepositional_oblique':
            prep=phrase['argument_preposition'];assert prep in readings and readings[prep].pos=='PREP'
            assert case in adapter.GOVERNMENT[tokens[prep]]
        else:raise AssertionError(role)
        if role not in ('prepositional_oblique','passive_instrument'):slots.append((role,target))
        if unit.get('cue') and target in unit['members']:
            split=min(unit['cue']['marker_positions'])
            assert target==(unit['members'][0] if phrase['end']<=split else unit['members'][1])
    assert covered==list(range(result['start'],result['end']))
    assert len(slots)==len(set(slots))
    assert all(p==unit['parent'] or p not in range(result['start'],result['end']) for p in predicates)
    assert all(p['nonfinite'] in embedded for p in unit['parts'] if p['kind']=='perception_aci')
    assert all(selected.get(p)==r for p,r in fixed.items())


def validate():
    for path,digest in load(OUT/'manifest.json')['inputs'].items():assert hashlib.sha256(open(path,'rb').read()).hexdigest()==digest,path
    adapter=FrozenAdapter(load(OUT/'morphology-lattice.json'));count=0
    for c in load(OUT/'controlled.json'):
        assert normalized(analyze(c['tokens'],c['predicates'],adapter,c['model']))==c['result']
        for r in c['result']['units']:
            if r['typed']['status']=='supported':check_witness(c['tokens'],c['predicates'],c['model']['units'][r['unit']],r['typed'],adapter);count+=1
    dev=load(NINE/'development-truth.json');models={(r['stream'],r['mode'],r['boundaries']):r['model'] for r in load(SEVENTEEN/'models.json') if r['arm']=='units_open'}
    rows=load(OUT/'predictions.json')
    for row in rows:
        s=dev[row['stream']];model=models[row['stream'],row['mode'],row['boundaries']]
        assert normalized(analyze(s['tokens'],s['finite'],adapter,model))==row['model']
        assert normalized(analyze(s['tokens'],s['finite'],adapter,model,dative_frame=False)['parents']['typed'])==row['parents']['typed_no_added_dative']
        for nf,raw in row['parents']['raw'].items():
            assert set(row['parents']['typed'][nf])<=set(row['parents']['pos'][nf])<=set(row['parents']['finite'][nf])<=set(raw)
        for r in row['model']['units']:
            if r['typed']['status']=='supported':check_witness(s['tokens'],s['finite'],model['units'][r['unit']],r['typed'],adapter);count+=1
        assert row['model']['firm_claims']==[]
    assert evaluate(rows,load(SIXTEEN/'evaluation-truth.json'))==load(OUT/'evaluation.json')
    def ids(obj):
        if isinstance(obj,dict):return {str(v) for k,v in obj.items() if k=='sent_id'}|set().union(*(ids(v) for v in obj.values()))
        if isinstance(obj,list):return set().union(*(ids(v) for v in obj)) if obj else set()
        return set()
    reserved=ids(load(RESERVE));assert len(reserved)==200 and not reserved&ids(dev)
    print(f'14 controlled and 264 natural replays; {count} independently checked witnesses; 200 reserved sentences unscored')

if __name__=='__main__':validate()
