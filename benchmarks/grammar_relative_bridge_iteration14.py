"""Local relative→nominal→finite-governor feasibility, with explicit abstention."""
from collections import Counter
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
from voynich_smt.relative_bridge import BridgeAdapter, bridge
from voynich_smt.word_mapping.morphology import WhitakerAnnotator

OUT = Path('experiments/results/grammar-restoration/iteration14-v3')
NINE = OUT.parent/'iteration9'
TEN = OUT.parent/'iteration10'
RESERVE = Path('experiments/holdouts/grammar-construction-next.json')

# Fixed before inspecting natural predictions. Every probe has >=3 finite choices.
CONTROLLED = [
    ('subject', 'pueri currunt puella quae cantat hodie laete semper ridet', [1,4,8],3,4,[8]),
    ('object_different_case', 'puer currit puellam quae cantat hodie mater uehementer diligit', [1,4,8],3,4,[8]),
    ('relative_object', 'pueri currunt puella quam agricola diligit hodie laete ridet', [1,5,8],3,5,[8]),
    ('plural_subject', 'puer currit puellae quae cantant hodie laete semper rident', [1,4,8],3,4,[8]),
    ('mixed_analysis_trap', 'pueri currunt puellae quae cantat hodie laete semper ridet', [1,4,8],3,4,[]),
    ('ambiguous_governors', 'puer currit puella quae cantat hodie laete semper ridet', [1,4,8],3,4,[1,8]),
    ('gender_mismatch', 'pueri currunt puella qui cantat hodie laete semper ridet', [1,4,8],3,4,[]),
    ('relative_number_mismatch', 'puer currit puellam quae cantant hodie mater uehementer diligit', [1,4,8],3,4,[]),
    ('instrument_not_subject', 'pueri currunt animalia quibus excipiatur hodie laete semper currunt', [1,4,8],3,4,[1,8]),
    ('unknown_valency_abstains', 'puer currit puellam quae cantat hodie mater uehementer amat', [1,4,8],3,4,[]),
]


def load(path):
    return json.loads(path.read_text())


def save(path, obj):
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')


def summarize(rows):
    unique = [r for r in rows if r['result']['status']=='unique_parent']
    correct = sum(r['scope_correct'] and r['result']['parents']==[r['reference_parent']] for r in unique)
    reachable = sum(r['scope_correct'] and r['reference_parent'] in r['result']['parents'] for r in rows)
    return {'cases':len(rows),'status':dict(Counter(r['result']['status'] for r in rows)),
        'unique_claims':len(unique),'correct_unique':correct,
        'precision':correct/len(unique) if unique else None,
        'correct_coverage':correct/len(rows) if rows else None,
        'reference_parent_reachable':reachable,
        'scope_correct':sum(r['scope_correct'] for r in rows)}


def run():
    if OUT.exists():
        raise ValueError('Preserve existing output')
    adapter=BridgeAdapter(WhitakerAnnotator('data/vendor/whitakers-words',mode='upstream-default'))
    controlled=[]
    for name,text,predicates,marker,child,expected in CONTROLLED:
        tokens=text.split()
        result=bridge(tokens,predicates,marker,child,adapter)
        mixed=bridge(tokens,predicates,marker,child,adapter,consistent=False)
        controlled.append({'name':name,'tokens':tokens,'predicates':predicates,'marker':marker,'child':child,
            'expected_parents':expected,'result':result,'mixed_readings':mixed})
        assert result['parents']==expected,(name,result['parents'],expected)
    assert controlled[4]['mixed_readings']['parents']==[1]
    dev=load(NINE/'development-truth.json');old=load(TEN/'predictions.json')
    predictions=[next(r['prediction'] for r in old if (r['stream'],r['training'],r['features'],r['markers'],r['condition'])==(i,'oof','interactions','predicted','unrestricted')) for i in range(len(dev))]
    rows=[]
    for i,(stream,pred) in enumerate(zip(dev,predictions)):
        gold={int(m):v['target'] for m,v in stream['markers'].items() if v['kind']=='relative'}
        predicted={m['position']:m['target'] for m in pred['marker_attachments'] if 'relative' in m['kinds'] and m['target'] is not None}
        # All reference relatives, including unsupported free/noncanonical relatives.
        # Predicted arm also includes spurious relative-scope decisions.
        for mode,scopes in [('reference_scope',gold),('predicted_scope',predicted)]:
            markers=sorted(set(gold)|set(scopes))
            for bounded in (False,True):
                for marker in markers:
                    child=scopes.get(marker)
                    reference_child=gold.get(marker)
                    parent=stream['parents'].get(str(reference_child))
                    result=({'status':'missing_scope','parents':[],'bridges':[]} if child is None else
                        bridge(stream['tokens'],stream['finite'],marker,child,adapter,scopes=tuple(scopes.items()),
                            boundaries=stream['boundaries'] if bounded else ()))
                    rows.append({'stream':i,'mode':mode,'boundaries':'reference' if bounded else 'hidden',
                        'marker':marker,'surface':stream['tokens'][marker],'child':child,'reference_child':reference_child,
                        'scope_correct':reference_child is not None and child==reference_child,
                        'reference_parent':parent,'baseline_parent':pred['parents'].get(str(child)), 'result':result})
    report={'scope':'Reused source development only; finite positions supplied in all arms; partial local witnesses, not full parses.',
        'method':{'radius':8,'unknown_valency':'reject object','nominals':['N','PRON'],
            'governors':'direct finite only; no inferred nonfinite/copular chains','selection':'all feasible parents; abstain unless unique',
            'opaque_spans':'minimal marker..child intervals, not complete clause boundaries'},
        'controlled':{'passed':len(controlled),'total':len(CONTROLLED),'mixed_reading_false_bridge':True},
        'natural':{f'{mode}/{bounds}':summarize([r for r in rows if r['mode']==mode and r['boundaries']==bounds])
            for mode in ('reference_scope','predicted_scope') for bounds in ('hidden','reference')},
        'reserved_validation':'untouched; registry hash pinned in manifest',
        'limitations':['finite predicates are supplied','no gold antecedents or parent arcs enter inference',
            'free relatives, postposed antecedents and nonfinite governing chains unsupported',
            'dictionary X valency rejects valid objects; ABL passive instruments only a compatibility hypothesis',
            'minimal relative intervals and directness are restrictive approximations; witnesses do not establish a grammatical parse']}
    OUT.mkdir(parents=True)
    save(OUT/'controlled.json',controlled);save(OUT/'predictions.json',rows);save(OUT/'report.json',report)
    words=sorted({w for s in dev for w in s['tokens']}|{w for c in controlled for w in c['tokens']})
    save(OUT/'morphology-lattice.json',{w:[asdict(r) for r in adapter.analyze(w)] for w in words})
    inputs=[NINE/'development-truth.json',TEN/'predictions.json',RESERVE,Path(__file__),Path('src/voynich_smt/relative_bridge.py')]
    save(OUT/'manifest.json',{'inputs':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},
        'lexicon_resource':adapter.analyzer.resource})
    print(json.dumps(report,indent=2))

if __name__=='__main__':
    run()
