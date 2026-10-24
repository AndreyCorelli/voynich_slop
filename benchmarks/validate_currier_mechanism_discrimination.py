"""Audit fresh passages, blind replay, generating truth and scoring."""
from collections import Counter
import json
from pathlib import Path
import tempfile
from benchmarks import currier_mechanism_discrimination as experiment
from benchmarks import currier_mechanism_comparison as base
from benchmarks import currier_alphabet_comparison as cipher
from voynich_smt.data.corpus import digest,write_json

def validate():
    out=experiment.OUT;p=json.loads((out/'prepared.json').read_text());public=json.loads((out/'public.json').read_text());truth=json.loads((out/'truth.json').read_text());pred=json.loads((out/'predictions.json').read_text());report=json.loads((out/'report.json').read_text())
    for path,sha in p['code_sha256'].items():assert digest(Path(path).read_text())==sha
    for path,sha in p['source_sha256'].items():assert digest(json.loads(Path(path).read_text()))==sha
    parent=json.loads(cipher.PARENT.read_text());assert digest(parent)==p['parent_sha256']
    for source,splits in p['passages'].items():
        intervals=[];stream=base.natural_stream(parent['sources'][source]);half=len(stream)//2
        for split,ps in splits.items():
            assert len(ps)==experiment.SIZES[split]
            for passage in ps:
                a,b=passage['start'],passage['end'];assert b-a==64 and stream[a:b]==passage['words']
                assert (b<=half if split!='evaluation' else a>=half)
                assert not any(old['start']<b and old['end']>a for old in parent['passages'][source])
                intervals.append((a,b))
        intervals.sort();assert all(a[1]<=b[0] for a,b in zip(intervals,intervals[1:]))
        counts=Counter(u for passage in splits['training'] for w in passage['words'] for u in w)
        alphabet=sorted({u for w in stream if w for u in w});expected={u:1 for u in alphabet}
        for u in sorted(alphabet,key=lambda u:(-counts[u],u))[:25-len(alphabet)]:expected[u]+=1
        assert p['allocations'][source]['allocated']==expected
    byid={r['id']:r for r in public['records']};assert len(byid)==600
    assert all(('label' in r)==(r['split']=='training') for r in public['records'])
    assert all(set(r)<=set(('id','source','split','passage_index','features','label')) for r in public['records'])
    assert set(byid)==set(truth['labels'])
    for r in truth['records']:
        assert truth['labels'][r['id']]==r['label']
        public_case=byid[r['id']];assert experiment.vector(r['metrics'])[0]==public_case['features']
        plain=p['passages'][r['source']][r['split']][r['passage_index']]['words']
        inverse={c[0]:u for u,cs in r['codebook'].items() for c in cs}
        assert len(inverse)==sum(map(len,r['codebook'].values()))<=25
        assert set(inverse)<=set(p['glyphs'])
        if r['label']=='renewal-6':
            for i,line in enumerate(r['payload']):assert ''.join(inverse[x] for w in line for x in w)==''.join(plain[16*i:16*(i+1)])
        else:assert [''.join(inverse[x] for x in w) for l in r['payload'] for w in l]==plain
        measured=base.measure(r['payload']);assert json.loads(json.dumps(measured))==r['metrics']
    # Replay prediction in a directory containing only the public feature file.
    # This proves prediction works without evaluation truth or prepared fixtures.
    with tempfile.TemporaryDirectory() as tmp:
        try:
            experiment.OUT=Path(tmp);write_json(experiment.OUT/'public.json',public);experiment.predict()
            assert json.loads((experiment.OUT/'predictions.json').read_text())==pred
        finally:experiment.OUT=out
    predictions={r['id']:r for r in pred['predictions']};assert len(predictions)==360
    assert all(byid[i]['split']!='training' for i in predictions)
    for s in report['summary']:
        selected=[(truth['labels'][i],r) for i,r in predictions.items() if byid[i]['source']==s['source'] and byid[i]['split']==s['split']]
        confusion=Counter((y,r['prediction']) for y,r in selected)
        assert [[y,k,n] for (y,k),n in sorted(confusion.items())]==s['confusion']
        assert sum(r['prediction']!='unresolved' for _,r in selected)==s['accepted']
        assert len(selected)==s['cases']
    assert report['prediction_sha256']==digest(pred)
    write_json(out/'validation.json',{'validated':True,'prepared_sha256':digest(p),'records':600,'predictions':360,'checks':'Frozen code/source hashes; disjoint fresh passages and halves; training-only homophone allocation; public-label omission; unique opaque IDs; alphabet capacity and direct inverse decoding; metric recomputation; blind prediction replay with only public features; independently recomputed confusion/acceptance counts.'})
    print('Validated600 generated records and360 blinded predictions')

if __name__=='__main__':validate()
