"""Selection challenge: frozen candidates, label-free features, tie-preserving probes."""
from pathlib import Path
import hashlib
from benchmarks.grammar_participial_structures_iteration21 import OUT as TWENTYONE,SEVENTEEN,NINE,SIXTEEN,RESERVE,load,save
from voynich_smt.structure_preferences import features,POLICIES,select

OUT=TWENTYONE.parent/'iteration22'


def produce(rows,models,dev):
    index={(m['stream'],m['mode'],m['boundaries']):m['model'] for m in models if m['arm']=='units_open'}
    records=[]
    for row in rows:
        if row['arm']!='participles_nisi' or row['mode']!='reference_scope' or row['boundaries']!='hidden':continue
        model=index[row['stream'],row['mode'],row['boundaries']]
        for entry in row['result']['units']:
            r=entry['result']
            if r['status']!='supported':continue
            unit=model['units'][entry['unit']];vectors=[features(dev[row['stream']]['tokens'],unit,s) for s in r['structures']]
            records.append(dict(stream=row['stream'],morphology=row['morphology'],unit=entry['unit'],members=unit['members'],parent=unit['parent'],
                start=r['start'],end=r['end'],features=vectors,selected={policy:select(vectors,policy) for policy in POLICIES}))
    return records


def run():
    if OUT.exists():raise ValueError('Preserve existing artifacts')
    rows=produce(load(TWENTYONE/'predictions.json'),load(SEVENTEEN/'models.json'),load(NINE/'development-truth.json'))
    OUT.mkdir();save(OUT/'predictions.json',rows)
    paths=[Path(__file__),Path('src/voynich_smt/structure_preferences.py'),TWENTYONE/'predictions.json',TWENTYONE/'morphology-lattice.json',SEVENTEEN/'models.json',NINE/'development-truth.json',RESERVE]
    save(OUT/'manifest.json',dict(inputs={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        scope='Fixed primary inspected-development condition; both morphology arms; source labels never enter features or selection.',
        policy_status='Post-hoc diagnostic preferences, including a reporting-versus-other-frame attachment default; no learned or validated model.',
        ties='All top candidates retained; no index, surface word, or annotation tie-break.'))
    print(f'{len(rows)} supported unit records; label-free selections saved')

if __name__=='__main__':run()
