"""Oracle missing-reading ablation; candidate units and grammar remain frozen."""
from dataclasses import asdict
from pathlib import Path
import hashlib
from benchmarks.grammar_construction_spans_iteration18 import OUT as EIGHTEEN,SEVENTEEN,NINE,SIXTEEN,RESERVE,load,save
from benchmarks.grammar_relative_constituents_iteration15_validate import FrozenAdapter,normalized
from voynich_smt.grammar_diagnostic import MorphAnalysis
from voynich_smt.construction_spans import analyze

OUT=EIGHTEEN.parent/'iteration19'
TREEBANK=Path('data/latin-grammar-benchmark/proiel-r2.17/la_proiel-ud-train.conllu')
# Chosen from iteration 18's unknown-token audit, not used to change owner pools.
TARGETS=((34,42,'160132',8),(34,43,'160132',9),(49,2,'160174',3),
         (56,34,'160202',4),(61,14,'160216',7))


def oracle_readings(dev):
    source={}
    for block in TREEBANK.read_text().split('\n\n'):
        sid=next((l.split(' = ',1)[1] for l in block.splitlines() if l.startswith('# sent_id = ')),None)
        if sid not in {t[2] for t in TARGETS}:continue
        for line in block.splitlines():
            if line and not line.startswith('#'):
                fields=line.split('\t')
                if fields[0].isdigit():source[sid,int(fields[0])]=fields
    result=[]
    for stream,pos,sid,index in TARGETS:
        fields=source[sid,index];features=dict(x.split('=',1) for x in fields[5].split('|') if '=' in x)
        # Only morphological fields are projected. Heads and dependency roles are
        # not passed to the adapter, recognizer, or candidate generator.
        projected={k:{'Nom':'NOM','Acc':'ACC','Gen':'GEN','Dat':'DAT','Abl':'ABL','Loc':'LOC',
                      'Sing':'S','Plur':'P','Masc':'M','Fem':'F','Neut':'N'}.get(v,v)
                   for k,v in features.items() if k in ('Case','Gender','Number')}
        pos_tag={'NOUN':'N','DET':'ADJ'}[fields[3]]
        assert fields[1].lower().replace('v','u')==dev[stream]['tokens'][pos]
        result.append(dict(stream=stream,position=pos,sent_id=sid,source_id=index,word=dev[stream]['tokens'][pos],
            source_upos=fields[3],source_features=features,reading=asdict(MorphAnalysis(pos_tag,tuple(sorted(projected.items()))))))
    return result


class OverlayAdapter(FrozenAdapter):
    def __init__(self,lattice,additions):
        super().__init__(lattice);self.additions=additions
    def analyze(self,word):
        baseline=super().analyze(word)
        added=tuple(MorphAnalysis(a['reading']['pos'],tuple(map(tuple,a['reading']['features']))) for a in self.additions if a['word']==word)
        return tuple(sorted(set(baseline+added)))


def produce(dev,models,lattice,additions):
    rows=[]
    for row in models:
        if row['arm']!='units_open':continue
        stream=row['stream'];s=dev[stream]
        local=[a for a in additions if a['stream']==stream]
        adapter=OverlayAdapter(lattice,local)
        for a in local:
            assert s['tokens'].count(a['word'])==1, 'word-keyed overlay must identify exactly one token'
            assert not FrozenAdapter(lattice).analyze(a['word']), 'only absent readings may be supplied'
        result=analyze(s['tokens'],s['finite'],adapter,row['model'])
        rows.append(dict(stream=stream,mode=row['mode'],boundaries=row['boundaries'],model=result))
    return normalized(rows)


def run():
    if OUT.exists():raise ValueError('Preserve saved artifacts')
    dev=load(NINE/'development-truth.json');models=load(SEVENTEEN/'models.json');lattice=load(EIGHTEEN/'morphology-lattice.json')
    additions=normalized(oracle_readings(dev));rows=produce(dev,models,lattice,additions)
    # Each reading's contribution is tested without touching any other reading.
    leave_one_out={f"{a['stream']}:{a['position']}":produce(dev,models,lattice,[b for b in additions if b!=a]) for a in additions}
    OUT.mkdir();save(OUT/'oracle-readings.json',additions);save(OUT/'predictions.json',rows);save(OUT/'leave-one-out.json',leave_one_out)
    paths=[Path(__file__),Path('src/voynich_smt/construction_spans.py'),Path('src/voynich_smt/relative_constituents.py'),TREEBANK,
           EIGHTEEN/'predictions.json',EIGHTEEN/'morphology-lattice.json',SEVENTEEN/'models.json',NINE/'development-truth.json',RESERVE]
    save(OUT/'manifest.json',dict(inputs={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
         intervention='Five token-specific absent readings from source UPOS/case/number/gender; DET projected to ADJ.',
         frozen='Candidate units, infinitive/governor readings, scope conditions and grammar unchanged.',
         limitation='Oracle annotations on previously inspected development; not deployable morphology or an unbiased generalization estimate.'))
    print(f'{len(additions)} oracle readings; {len(rows)} conditions; five leave-one-out replays')

if __name__=='__main__':run()
