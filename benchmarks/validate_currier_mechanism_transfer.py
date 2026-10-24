"""Fresh-source exclusion, conservation, blind replay and scoring audit."""
from collections import Counter
import json
from pathlib import Path
import tempfile
from benchmarks import currier_mechanism_transfer as experiment
from benchmarks import currier_mechanism_discrimination as prior
from benchmarks import currier_mechanism_comparison as base
from benchmarks import currier_alphabet_comparison as cipher
from voynich_smt.data.corpus import digest,write_json

def validate():
    out=experiment.OUT;p=json.loads((out/'prepared.json').read_text());public=json.loads((out/'public.json').read_text());truth=json.loads((out/'truth.json').read_text());pred=json.loads((out/'predictions.json').read_text());report=json.loads((out/'report.json').read_text())
    for path,sha in p['code_sha256'].items():assert digest(Path(path).read_text())==sha
    for path,sha in p['source_sha256'].items():assert digest(json.loads(Path(path).read_text()))==sha
    old=json.loads((prior.OUT/'prepared.json').read_text());oldpublic=json.loads((prior.OUT/'public.json').read_text());parent=json.loads(cipher.PARENT.read_text())
    assert digest(old)==p['prior_sha256'] and digest(oldpublic)==p['prior_public_sha256'] and digest(parent)==p['parent_sha256']
    assert public['training']==[r for r in oldpublic['records'] if r['split']=='training']
    assert len(public['training'])==240 and len(public['evaluation'])==600
    assert all(set(r)=={'id','source','passage_index','features'} for r in public['evaluation'])
    for source,ps in p['passages'].items():
        stream=base.natural_stream(parent['sources'][source]);intervals=[]
        excluded=parent['passages'][source]+[x for xs in old['passages'][source].values() for x in xs]
        assert len(ps)==8
        for x in ps:
            a,b=x['start'],x['end'];assert a>=len(stream)//2 and b-a==64 and stream[a:b]==x['words']
            assert not any(y['start']<b and y['end']>a for y in excluded);intervals.append((a,b))
        intervals.sort();assert all(a[1]<=b[0] for a,b in zip(intervals,intervals[1:]))
    byid={r['id']:r for r in public['evaluation']};labels={r['id']:r for r in truth['records']};assert len(byid)==len(labels)==600 and byid.keys()==labels.keys()
    for r in truth['records']:
        lines=r['payload'];payload=r['mono_payload'];label=r['label'];plain=p['passages'][r['source']][r['passage_index']]['words']
        assert r['outside_grid']==(label in experiment.OUTSIDERS)
        mono=cipher.key_for(p['allocations'][r['source']]['mono'],p['glyphs'],r['seed']);inverse={c[0]:u for u,cs in mono.codebook.items() for c in cs}
        assert [''.join(inverse[g] for g in w) for l in payload for w in l]==plain
        if label=='fixed-two':
            assert [[tuple(w[::2]) for w in l] for l in lines]==[[tuple(w) for w in l] for l in payload]
            assert all(w[i]==p['glyphs'][-1] for l in lines for w in l for i in range(1,len(w),2))
        elif label=='word-final-marker':assert [[w[:-1] for w in l] for l in lines]==payload
        elif label=='glyph-shuffle':
            assert Counter(g for l in lines for w in l for g in w)==Counter(g for l in payload for w in l for g in w)
            assert [[len(w) for w in l] for l in lines]==[[len(w) for w in l] for l in payload]
        elif label.startswith('renewal-'):assert [[g for w in l for g in w] for l in lines]==[[g for w in l for g in w] for l in payload]
        else:
            kind='allocated' if label.startswith('sparse') else 'mono'
            enc=cipher.key_for(p['allocations'][r['source']][kind],p['glyphs'],r['seed']);rev={c[0]:u for u,cs in enc.codebook.items() for c in cs}
            assert [''.join(rev[g] for g in w) for l in lines for w in l]==plain
        assert set(g for l in lines for w in l for g in w)<=set(p['glyphs'])
        assert json.loads(json.dumps(base.measure(lines)))==r['metrics']
        assert prior.vector(r['metrics'])[0]==byid[r['id']]['features']
    with tempfile.TemporaryDirectory() as tmp:
        try:
            experiment.OUT=Path(tmp);write_json(experiment.OUT/'public.json',public);experiment.predict()
            assert json.loads((experiment.OUT/'predictions.json').read_text())==pred
        finally:experiment.OUT=out
    assert len(pred['predictions'])==1632
    assert all(r['training_source']!=byid[r['id']]['source'] for r in pred['predictions'])
    for s in report['summary']:
        rows=[(labels[r['id']],r) for r in pred['predictions'] if r['mode']==s['mode'] and r['training_source']==s['training_source'] and labels[r['id']]['source']==s['evaluation_source'] and labels[r['id']]['outside_grid']==s['outside_grid']]
        confusion=Counter((t['label'],r['prediction']) for t,r in rows)
        assert [[a,b,n] for (a,b),n in sorted(confusion.items())]==s['confusion']
        assert len(rows)==s['cases'] and sum(r['prediction']!='unresolved' for _,r in rows)==s['accepted']
    assert digest(pred)==report['predictions_sha256']
    write_json(out/'validation.json',{'validated':True,'prepared_sha256':digest(p),'records':600,'transfer_predictions':1632,'checks':'Frozen provenance, exact training-only reuse; disjoint fresh passages; inverse decoding; fixed2/marker/shuffle/renewal conservation; glyph budget; recomputed metrics and features; blind replay with public file only; training source differs from target; independent confusion and acceptance counts.'})
    print('Validated600 records and1632 cross-source predictions')

if __name__=='__main__':validate()
