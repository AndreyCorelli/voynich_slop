"""Independent likelihood checks and training-selection audit."""
import json
from statistics import mean
from benchmarks import joint_predictor_calibration as m
from benchmarks.character_prediction_validation import manual
from benchmarks.shared_inventory_validation import inventories
from voynich_smt.data.corpus import digest, write_json


def validate():
    base,p=m.prepare(); reports=[]; checked=decoded=0
    for i in range(1,8):
        r=json.loads((m.OUT/f'iteration-{i}.json').read_text())
        assert r['plan']==json.loads((m.OUT/f'plan-{i}.json').read_text())
        assert r['plan']['prepared_sha256']==digest(p)
        assert r['plan']['previous_sha256']==(digest(reports[-1]) if reports else None)
        reports.append(r)
    for source,c in reports[1]['calibration'].items():
        chosen=min(m.RATES,key=lambda rate:(abs(c['candidates'][str(rate)]['excess']-c['target']['excess']),rate))
        assert chosen==c['selected_rate']
        a={s for b in base['sources'][source]['training'][:16] for s in b['source_slots']}
        b={s for block in base['sources'][source]['training'][16:] for s in block['source_slots']}
        held={s for block in base['sources'][source]['heldout'] for s in block['source_slots']}
        assert not a&b and not (a|b)&held
        for result in [c['target'],*c['candidates'].values()]:
            assert abs(result['excess']-(result['active']['gain_position']-mean(n['gain_position'] for n in result['nulls'])))<1e-12
    for report in reports[2:6]:
        source=report['source']; assert report['rate']==reports[1]['calibration'][source]['selected_rate']
        for name,result in report['results'].items():
            seed=int(name.rsplit('-',1)[1]); pair=result['payload']
            for plain,original,split in zip(pair,(base['sources'][source]['training'],base['sources'][source]['heldout']),('train','heldout')):
                assert inventories(plain,True)==inventories(original,True)
                enc,key=m.joint.prior.encoding.encoder(plain,seed,.0625,split=split); inverse={v:k for k,v in key['payload'].items()}
                for a,z in zip(plain,enc,strict=True):
                    for i,(truth,word) in enumerate(zip(a['words'],z['words'],strict=True)):
                        marked=i>0 and z['line_ids'][i]==z['line_ids'][i-1] and i%16==0
                        if marked: assert word[0]==key['marker'][z['words'][i-1][-1]]
                        assert [inverse[x] for x in (word[1:] if marked else word)]==truth; decoded+=1
            encoded=m.encoded_pair(*pair,seed)
            cases=[(encoded,result['active'])]
            for ns,record in zip(m.NULLS,result['nulls'],strict=True):
                shuffled=[m.reorder(blocks,0,m.stream_seed(ns,split))[0] for blocks,split in zip(encoded,('train','heldout'))]
                for a,b in zip(encoded,shuffled,strict=True): assert inventories(a)==inventories(b)
                cases.append((shuffled,record))
            for (train,held),record in cases:
                for row,block in zip(record['rows'],held,strict=True):
                    for spec,gain in ((p['spec'],False),({**p['spec'],'gate':'none'},True)):
                        for token,(loss,novel) in zip(row['tokens'],manual(train,block,spec),strict=True):
                            assert abs(token['loss']+(token['gain_position'] if gain else 0)-loss)<1e-10
                            assert token['novel']==novel; checked+=1
                assert m.pred.aggregate(record['rows'])==record
            assert abs(result['excess']-(result['active']['gain_position']-mean(n['gain_position'] for n in result['nulls'])))<1e-12
            assert abs(result['repeat']-m.joint.prior.summarize(encoded[1])['adjusted'])<1e-12
    expected={r['source']:{'rate':r['rate'],**{kind:{metric:mean(r['results'][f'{kind}-{seed}'][metric] for seed in m.SEEDS) for metric in ('excess','repeat')} for kind in ('prose','calibrated')}} for r in reports[2:6]}
    assert reports[-1]['grouped']==expected
    report={'status':'passed','independent_evaluation_word_model_scores':checked,'decoded_words':decoded,'training_only_selection_and_disjoint_slots':True,'scope':'Independent active/position likelihood reconstruction on heldout and nulls; calibration selection arithmetic audited, calibration likelihoods not independently recomputed. Cached parser and optimizer reused.'}
    write_json(m.OUT/'validation.json',report); print(report,flush=True)

if __name__=='__main__': validate()
