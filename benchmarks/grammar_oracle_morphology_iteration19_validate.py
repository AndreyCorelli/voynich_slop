"""Replay the missing-reading intervention without upstream dictionary access."""
import hashlib
from benchmarks.grammar_oracle_morphology_iteration19 import OUT,EIGHTEEN,SEVENTEEN,NINE,SIXTEEN,RESERVE,load,produce,oracle_readings,OverlayAdapter
from benchmarks.grammar_oracle_morphology_iteration19_evaluate import evaluate_oracle,audit
from benchmarks.grammar_construction_spans_iteration18_validate import check_witness
from benchmarks.grammar_relative_constituents_iteration15_validate import normalized


def validate():
    for path,digest in load(OUT/'manifest.json')['inputs'].items():assert hashlib.sha256(open(path,'rb').read()).hexdigest()==digest,path
    dev=load(NINE/'development-truth.json');models=load(SEVENTEEN/'models.json');lattice=load(EIGHTEEN/'morphology-lattice.json');additions=load(OUT/'oracle-readings.json')
    assert normalized(oracle_readings(dev))==additions
    rows=load(OUT/'predictions.json');baseline=load(EIGHTEEN/'predictions.json');truth=load(SIXTEEN/'evaluation-truth.json')
    assert produce(dev,models,lattice,additions)==rows
    index={(r['stream'],r['mode'],r['boundaries']):r['model'] for r in models if r['arm']=='units_open'}
    witnesses=0
    for b,r in zip(baseline,rows):
        assert r['model']['parents']['finite']==b['model']['parents']['finite']
        for arm in ('pos','typed'):
            for nf,parents in b['model']['parents'][arm].items():assert set(parents)<=set(r['model']['parents'][arm][nf])
        if r['stream'] not in {a['stream'] for a in additions}:assert r['model']==b['model']
        s=dev[r['stream']];adapter=OverlayAdapter(lattice,[a for a in additions if a['stream']==r['stream']]);m=index[r['stream'],r['mode'],r['boundaries']]
        for u in r['model']['units']:
            if u['typed']['status']=='supported':check_witness(s['tokens'],s['finite'],m['units'][u['unit']],u['typed'],adapter);witnesses+=1
        assert not r['model']['firm_claims']
    expected=evaluate_oracle(rows,baseline,truth);expected['leave_one_out']={}
    for a in additions:
        key=f"{a['stream']}:{a['position']}"
        ablated=produce(dev,models,lattice,[b for b in additions if b!=a])
        assert ablated==load(OUT/'leave-one-out.json')[key]
        expected['leave_one_out'][key]=evaluate_oracle(ablated,baseline,truth)
    assert expected==load(OUT/'evaluation.json')
    assert audit(rows,baseline,models,truth)==load(OUT/'audit.json')
    def ids(obj):
        if isinstance(obj,dict):return {str(v) for k,v in obj.items() if k=='sent_id'}|set().union(*(ids(v) for v in obj.values()))
        if isinstance(obj,list):return set().union(*(ids(v) for v in obj)) if obj else set()
        return set()
    reserved=ids(load(RESERVE));assert len(reserved)==200 and not reserved&ids(dev)
    print(f'264 oracle + 1320 leave-one-out replays; {witnesses} local witnesses; 200 reserved sentences unscored')

if __name__=='__main__':validate()
