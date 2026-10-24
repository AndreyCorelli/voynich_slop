"""Local construction interiors: finite barrier, POS cover, typed role cover."""
from dataclasses import asdict
import hashlib
from pathlib import Path
import time
from voynich_smt.complement_units import ComplementModel
from voynich_smt.construction_spans import analyze
from voynich_smt.relative_constituents import ConstituentAdapter
from voynich_smt.word_mapping.morphology import WhitakerAnnotator
from benchmarks.grammar_complement_units_iteration17 import OUT as SEVENTEEN,NINE,SIXTEEN,RESERVE,load,save

OUT=SEVENTEEN.parent/'iteration18'
# Expected typed parent sets; ambiguity is intentionally retained.
PROBES=[
 ('equal_distance_number','puella ridet debet pueri laborare pueri debent',('ridet','debet','debent'),(),{'laborare':['debent']}),
 ('equal_distance_case','puella ridet solent hortos nocere hortis debebunt',('ridet','solent','debebunt'),(),{'nocere':['debebunt']}),
 ('equal_distance_ambiguous','puella ridet debent pueri laborare pueri possunt',('ridet','debent','possunt'),(),{'laborare':['debent','possunt']}),
 ('agreeing_modifier','pueri currunt debet puellam bonam capere puella ridet',('currunt','debet','ridet'),(),{'capere':['debet']}),
 ('bad_modifier','pueri currunt debet puellam bonis capere puella ridet',('currunt','debet','ridet'),(),{'capere':[]}),
 ('preposition_case','pueri currunt debet sine urbe laborare puella ridet',('currunt','debet','ridet'),(),{'laborare':['debet']}),
 ('bad_preposition_case','pueri currunt debet sine urbem laborare puella ridet',('currunt','debet','ridet'),(),{'laborare':[]}),
 ('perception_subject','pueri currunt instare malum uiderint puella ridet',('currunt','uiderint','ridet'),(),{'instare':['uiderint']}),
 ('relative_finite_barrier','puella ridet debet laborare quae cantat diligere potest',('ridet','debet','cantat','potest'),(('quae','cantat'),),{'laborare':['debet'],'diligere':['potest']}),
 ('unknown_inside','creditur zzznominal fecundare puella ridet pueri currunt',('creditur','ridet','currunt'),(),{'fecundare':[]}),
 ('coordinated_objects','pueri currunt debet puellam capere et librum accipere puella ridet',('currunt','debet','ridet'),(),{'capere':['debet'],'accipere':['debet']}),
 ('objects_wrong_segment','pueri currunt debet puellam librum capere et accipere puella ridet',('currunt','debet','ridet'),(),{'capere':[],'accipere':[]}),
 ('normalized_coordination','pueri currunt ne c conlocare ne c aperire debemus puella ridet',('currunt','debemus','ridet'),(),{'conlocare':['debemus'],'aperire':['debemus']}),
 ('nested_not_a_complete_clause','pueri currunt posse laborare debet puella ridet',('currunt','debet','ridet'),(),{'posse':[],'laborare':['debet']}),
]


def arguments(probe):
    name,text,pwords,scope_words,expected_words=probe;t=text.split()
    return t,[t.index(w) for w in pwords],tuple((t.index(m),t.index(c)) for m,c in scope_words),{str(t.index(nf)):sorted(t.index(p) for p in parents) for nf,parents in expected_words.items()}


def run():
    if OUT.exists():raise ValueError('Preserve saved artifacts')
    start=time.monotonic();adapter=ConstituentAdapter(WhitakerAnnotator('data/vendor/whitakers-words',mode='upstream-default'));controlled=[]
    for probe in PROBES:
        tokens,predicates,scopes,expected=arguments(probe);model=ComplementModel(tokens,predicates,adapter,scopes=scopes).serializable()
        result=analyze(tokens,predicates,adapter,model)
        assert result['parents']['typed']==expected,(probe[0],result['parents']['typed'],expected)
        controlled.append(dict(name=probe[0],tokens=tokens,predicates=predicates,scopes=scopes,expected=expected,model=model,result=result))
    dev=load(NINE/'development-truth.json');models=[r for r in load(SEVENTEEN/'models.json') if r['arm']=='units_open'];rows=[]
    for row in models:
        s=dev[row['stream']];result=analyze(s['tokens'],s['finite'],adapter,row['model'])
        without=analyze(s['tokens'],s['finite'],adapter,row['model'],dative_frame=False)
        eligible=set(result['parents']['typed'])
        raw={nf:sorted({u['parent'] for u in row['model']['units'] if u['kind']!='shared_subject_participle' and int(nf) in u['members']}) for nf in eligible}
        nearest={nf:[p for p in values if abs(p-int(nf))==min(abs(q-int(nf)) for q in values)] if values else [] for nf,values in raw.items()}
        rows.append(dict(stream=row['stream'],mode=row['mode'],boundaries=row['boundaries'],
            model=result,parents={'raw':raw,'nearest':nearest,**result['parents'],'typed_no_added_dative':without['parents']['typed']}))
    OUT.mkdir(parents=True);save(OUT/'controlled.json',controlled);save(OUT/'predictions.json',rows)
    words=sorted({w for s in dev for w in s['tokens']}|{w for c in controlled for w in c['tokens']})
    save(OUT/'morphology-lattice.json',{w:[asdict(r) for r in adapter.analyze(w)] for w in words})
    paths=[Path(__file__),Path('src/voynich_smt/construction_spans.py'),Path('src/voynich_smt/relative_constituents.py'),
        Path('src/voynich_smt/complement_units.py'),SEVENTEEN/'models.json',NINE/'development-truth.json',RESERVE]
    save(OUT/'manifest.json',{'inputs':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        'lexicon_resource':adapter.analyzer.resource,'span':'minimal interval containing unit anchors and candidate evidence',
        'new_argument_license':'nocere + dative; dictionary-only ablation retained','max_np':8,
        'scope':'Infinitive construction interiors only; unknown owners retained; inspected development.',
        'elapsed_seconds':time.monotonic()-start})
    print(f'{len(controlled)} probes passed; {len(rows)} natural conditions; {time.monotonic()-start:.2f}s')

if __name__=='__main__':run()
