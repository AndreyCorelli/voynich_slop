"""Frozen replay and independent participial dependency/agreement checks."""
import hashlib
from benchmarks.grammar_participial_structures_iteration21 import OUT,ARMS,TWENTY,NINETEEN,SEVENTEEN,NINE,SIXTEEN,RESERVE,load,produce,analyze
from benchmarks.grammar_oracle_morphology_iteration19 import OverlayAdapter
from benchmarks.grammar_relative_constituents_iteration15_validate import normalized
from benchmarks.grammar_participial_structures_iteration21_evaluate import evaluate
from voynich_smt.construction_spans import decode


def flags(arm):return dict(coordination=True,attachment=True,perdere_frame=True,**ARMS[arm])

def check_structure(tokens,predicates,unit,result,structure,adapter,flags):
    fixed={int(p):decode(r) for p,r in unit['readings'].items()};selected={};covered=[];slots=[];groups=[];links=[]
    def add(p,v):
        r=decode(v);assert r in adapter.analyze(tokens[p])
        assert p not in selected or selected[p]==r
        assert p not in fixed or fixed[p]==r
        selected[p]=r;return r
    for segment in structure['witness']:
        covered.extend(segment['positions']);role=segment['role']
        if 'clause' in segment:
            clause=segment['clause'];subject=clause['subject'];part=clause['participle'];marker=clause['marker'];ts=segment['targets']
            assert flags['participles'] and role=='ablative_participial_clause'
            assert len(ts)==1 and ts[0] in {unit['parent'],*unit['members']}
            assert abs(subject-part)==1
            expected=sorted([subject,part]+([marker] if marker is not None else []))
            assert segment['positions']==expected
            assert expected==list(range(expected[0],expected[-1]+1))
            assert set(map(int,clause['analyses']))=={subject,part}
            noun=add(subject,clause['analyses'][str(subject)]);verb=add(part,clause['analyses'][str(part)])
            assert noun.pos in ('N','PRON') and verb.pos=='VPAR'
            assert noun.get('Case')==verb.get('Case')=='ABL'
            assert clause['agreement']['Case']=='ABL'
            for key,universe in [('Gender',{'M','F','N'}),('Number',{'S','P'})]:
                value=clause['agreement'][key];assert value in universe
                for r in (noun,verb):
                    source=r.get(key)
                    assert source in (None,'X','0',value) or key=='Gender' and source=='C' and value in ('M','F')
            assert not {subject,part}&{unit['parent'],*unit['members']}
            if marker is not None:
                assert flags['nisi_clause'] and tokens[marker]=='nisi' and marker==min(subject,part)-1
                reading=add(marker,clause['marker_reading']);assert reading.pos in ('ADV','CONJ')
                links.append([marker,part,'clause_marker'])
            else:assert clause['marker_reading'] is None
            groups.append({'role':role,'heads':[part],'targets':ts})
            links.append([subject,part,'participial_subject']);links.extend([part,t,'participial_adjunct'] for t in ts)
            continue
        if 'phrases' not in segment:
            assert len(segment['positions'])==1;p=segment['positions'][0]
            if segment['reading'] is not None:r=add(p,segment['reading'])
            else:assert role=='coordinator' and unit['cue']['kind']=='paired_ne_c' and tokens[p] in ('ne','c')
            if role=='governor':assert p==unit['parent']
            elif role=='infinitive':assert p in unit['members']
            elif role=='adverb':assert r.pos=='ADV'
            elif role=='particle':assert r.pos=='CONJ' and tokens[p] in ('enim','autem','ergo','igitur')
            else:assert role=='coordinator'
            continue
        phrases=segment['phrases'];ts=segment['targets'];heads=[p['head'] for p in phrases]
        sites=[]
        assert set(ts)<={unit['parent'],*unit['members']} and ts
        if len(phrases)>1:
            assert flags['coordination'] and len(phrases)==2 and role=='object'
            assert phrases[0]['end']+1==phrases[1]['start']
            assert phrases[0]['end'] in segment['markers']
        for marker in segment['markers']:
            assert tokens[marker] in ('et','uel') and any(r.pos=='CONJ' for r in adapter.analyze(tokens[marker]));sites.append(marker)
        for phrase in phrases:
            ps=list(range(phrase['start'],phrase['end']));sites.extend(ps)
            assert set(ps)==set(map(int,phrase['analyses']))
            rs={int(p):add(int(p),v) for p,v in phrase['analyses'].items()};head=phrase['head'];noun=rs[head]
            assert noun.pos in ('N','PRON')
            for feature,value in phrase['agreement'].items():
                assert noun.get(feature) in (None,'X','0',value) or noun.get(feature)=='C' and value in ('M','F')
            case=noun.get('Case')
            for t in ts:
                v=fixed[t]
                if role=='object':
                    assert t in unit['members'] and case=='ACC'
                    assert v.get('VerbKind')=='TRANS' or v.get('VerbRoot') in ({'hab','loc','perd'} if flags.get('perdere_frame') else {'hab','loc'})
                elif role=='matrix_subject':
                    person='1' if tokens[head] in ('ego','nos') else '2' if tokens[head] in ('tu','uos','vos') else '3'
                    assert t==unit['parent'] and case=='NOM' and phrase['agreement']['Number']==v.get('Number') and person==v.get('Person')
                elif role=='embedded_subject':assert case=='ACC' and any(p.get('embedded_subject')==head and p['nonfinite']==t for p in unit['parts'])
                elif role=='dative_argument':assert case=='DAT' and (v.get('VerbKind')=='DAT' or v.get('VerbRoot')=='noc')
                elif role=='genitive_argument':assert case=='GEN' and v.get('VerbKind')=='GEN'
                elif role=='ablative_argument':assert case=='ABL' and v.get('VerbKind')=='ABL'
                elif role=='unresolved_ablative':assert flags['attachment'] and case=='ABL'
                elif role=='passive_instrument':assert not flags['attachment'] and case=='ABL' and t==unit['parent'] and v.get('Voice')=='PASSIVE'
                elif role=='prepositional_oblique':
                    prep=phrase['argument_preposition'];assert prep in rs and rs[prep].pos=='PREP' and case in adapter.GOVERNMENT[tokens[prep]]
                else:raise AssertionError(role)
        assert sorted(sites)==segment['positions']
        if role not in ('prepositional_oblique','unresolved_ablative','passive_instrument'):slots.extend((role,t) for t in ts)
        if role in ('object','dative_argument','genitive_argument','ablative_argument','prepositional_oblique') and unit.get('cue'):
            exterior=segment['positions'][-1]<min(unit['members']) or segment['positions'][0]>max(unit['members'])
            if not flags['attachment'] or not exterior:
                target=unit['members'][0] if segment['positions'][-1]<min(unit['cue']['marker_positions']) else unit['members'][1]
                assert ts==[target]
        groups.append({'role':role,'heads':heads,'targets':ts});links.extend([h,t,role] for h in heads for t in ts)
    assert all(a['role']!='object' or b['role']!='object' for a,b in zip(structure['witness'],structure['witness'][1:]))
    assert covered==list(range(result['start'],result['end']))
    assert len(slots)==len(set(slots))
    assert all(selected.get(p)==r for p,r in fixed.items())
    assert all(p==unit['parent'] or p not in covered for p in predicates)
    assert all(('embedded_subject',p['nonfinite']) in slots for p in unit['parts'] if p['kind']=='perception_aci')
    assert sorted(links)==structure['links']
    assert sorted(groups,key=lambda g:(g['role'],g['heads'],g['targets']))==structure['groups']


def validate():
    for p,h in load(OUT/'manifest.json')['inputs'].items():assert hashlib.sha256(open(p,'rb').read()).hexdigest()==h,p
    lattice=load(OUT/'morphology-lattice.json');additions=load(NINETEEN/'oracle-readings.json');dev=load(NINE/'development-truth.json');models=load(SEVENTEEN/'models.json')
    rows=load(OUT/'predictions.json');assert produce(dev,models,lattice,additions)==rows
    old={(r['stream'],r['mode'],r['boundaries'],r['morphology']):r['result'] for r in load(TWENTY/'predictions.json') if r['arm']=='joint'}
    idx={(r['stream'],r['mode'],r['boundaries']):r['model'] for r in models if r['arm']=='units_open'};count=0
    for row in rows:
        s=dev[row['stream']];m=idx[row['stream'],row['mode'],row['boundaries']];a=OverlayAdapter(lattice,[v for v in additions if v['stream']==row['stream']] if row['morphology']=='oracle_missing' else [])
        if row['arm']=='baseline':assert row['result']==old[row['stream'],row['mode'],row['boundaries'],row['morphology']]
        for u in row['result']['units']:
            for structure in u['result'].get('structures',[]):
                check_structure(s['tokens'],s['finite'],m['units'][u['unit']],u['result'],structure,a,flags(row['arm']));count+=1
        assert not row['result']['firm_claims']
    for c in load(OUT/'controlled.json'):
        a=OverlayAdapter(lattice,[])
        for arm,options in ARMS.items():
            assert normalized(analyze(c['tokens'],c['predicates'],a,c['model'],**options))==c['results'][arm]
            for u in c['results'][arm]['units']:
                for structure in u['result'].get('structures',[]):check_structure(c['tokens'],c['predicates'],c['model']['units'][u['unit']],u['result'],structure,a,flags(arm));count+=1
    metrics,audits=evaluate(rows,load(SIXTEEN/'evaluation-truth.json'),dev,models)
    assert metrics==load(OUT/'evaluation.json') and audits==load(OUT/'audit.json')
    def ids(o):
        if isinstance(o,dict):return {str(v) for k,v in o.items() if k=='sent_id'}|set().union(*(ids(v) for v in o.values()))
        if isinstance(o,list):return set().union(*(ids(v) for v in o)) if o else set()
        return set()
    reserved=ids(load(RESERVE));assert len(reserved)==200 and not reserved&ids(dev)
    print(f'1584 natural conditions + 11 controls replayed; {count} structures checked; baseline equals iteration 20; 200 reserved sentences unscored')

if __name__=='__main__':validate()
