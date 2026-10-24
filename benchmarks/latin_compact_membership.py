"""Exact compact finite inventory membership and standalone SMT prototype."""
import argparse
from dataclasses import asdict
import gzip
import hashlib
import json
from pathlib import Path
from time import perf_counter
from benchmarks import latin_form_inventory as inventory
from benchmarks import latin_morphology_coverage as morphology
from voynich_smt.data.corpus import digest,write_json
from voynich_smt.language.word_automaton import WordAutomaton
from voynich_smt.models.alphabet import Alphabet
from voynich_smt.solver.automaton_membership import AutomatonMembership

OUT=Path('experiments/results/latin-compact-membership')


def inventory_lines(path):
    with gzip.open(path,'rt') as stream:
        for line in stream:yield line.rstrip('\n')


def prepare():
    source=inventory.prepare();report=json.loads((inventory.OUT/'report.json').read_text())
    if not report['complete'] or report['prepared_sha256']!=digest(source):raise ValueError('Unmatched inventory')
    paths=(Path(__file__),Path('src/voynich_smt/language/word_automaton.py'),Path('src/voynich_smt/solver/automaton_membership.py'))
    identity={'source_sha256':digest(source),'report_sha256':digest(report),'code_sha256':{str(p):digest(p.read_text()) for p in paths}}
    path=OUT/'prepared.json'
    if path.exists():
        p=json.loads(path.read_text())
        if p['identity']!=identity:raise ValueError('Frozen sources/code changed')
        return p
    protocol={'identity':identity,'modes':list(report['modes']),'cipher_recovery_runs':0,
        'selection':'Build exact suffix-sharing minimal acyclic deterministic automata from entire sorted generated inventories, without target selection, approximation or pruning. Shared SMT constant arrays for state/token transitions and accepting states; bounded symbolic traversal and padding. Old strict/experimental solver paths unchanged.',
        'scope':'Exact inventory representation, not new morphology rules or cipher recovery. Validate accepted word count, every inventory spelling, all frozen query types and deterministic negative controls. Standalone shared-array construction measured separately from source-generation/trie build. Does not establish full solver search performance or accidental-fit rate; canonical i/u remains.'}
    p={'identity':identity,'protocol':protocol,'inventories':report['modes']};write_json(OUT/'protocol.json',protocol);write_json(path,p);return p


def save_automaton(mode,a):
    path=OUT/(mode+'-automaton.json.gz');raw=json.dumps(asdict(a),separators=(',',':')).encode();path.write_bytes(gzip.compress(raw,mtime=0))
    return {'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}


def load_automaton(metadata):
    path=Path(metadata['path']);raw=path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=metadata['sha256']:raise ValueError('Automaton hash changed')
    p=json.loads(gzip.decompress(raw));return WordAutomaton(p['root'],tuple((terminal,tuple((s,c) for s,c in edges)) for terminal,edges in p['states']))


def check(a,metadata,source):
    path=Path(metadata['path'])
    if hashlib.sha256(path.read_bytes()).hexdigest()!=metadata['sha256']:raise ValueError('Inventory hash changed')
    count=0;prefix_tokens=0
    for word in inventory_lines(path):
        if not a.accepts(word):raise RuntimeError('Missing generated form')
        count+=1;prefix_tokens+=len(word)
    assert count==metadata['word_count']==a.accepted_word_count()
    expected=set(morphology.canonical(w) for w in source['query_words'])
    # Exact inventory lookup for positives/negatives; no membership assumption.
    import random
    rng=random.Random(4801)
    controls={''.join(rng.sample(w,len(w))) for w in sorted(expected)}
    lookup=expected|controls;members={w for w in inventory_lines(path) if w in lookup}
    assert all(a.accepts(w)==(w in members) for w in lookup)
    return {'all_inventory_words':count,'inventory_letter_occurrences':prefix_tokens,'query_and_control_types':len(lookup),'disagreements':0}


def run():
    p=prepare();source=morphology.prepare();path=OUT/'report.json'
    r=json.loads(path.read_text()) if path.exists() else {'prepared_sha256':digest(p),'modes':{},'complete':False}
    if r['prepared_sha256']!=digest(p):raise ValueError('Checkpoint changed')
    for mode,record in p['inventories'].items():
        if mode in r['modes']:continue
        print(mode,'building full inventory automaton',flush=True)
        start=perf_counter();a=WordAutomaton.from_sorted(inventory_lines(record['inventory']['path']));build=perf_counter()-start
        start=perf_counter();checks=check(a,record['inventory'],source);validation=perf_counter()-start
        edges=sum(len(e) for _,e in a.states);alphabet=Alphabet(tuple(sorted({symbol for _,edges in a.states for symbol,_ in edges})))
        print(mode,len(a.states),'states',edges,'edges; constructing shared SMT table',flush=True)
        start=perf_counter();table=AutomatonMembership(a,alphabet);construction=perf_counter()-start
        # Construction only: large-array search awaits separate calibrated integration.
        row={'automaton':save_automaton(mode,a),'word_count':record['inventory']['word_count'],'states':len(a.states),'edges':edges,
             'automaton_build_seconds':build,'validation_seconds':validation,'shared_smt_table_construction_seconds':construction,'checks':checks,
             'alphabet':asdict(alphabet),'smt_table_entries':edges+sum(t for t,_ in a.states)}
        r['modes'][mode]=row;write_json(path,r);print(mode,row,flush=True)
        del table
    r['complete']=True;write_json(path,r);return r


def validate():
    p=prepare();source=morphology.prepare();r=json.loads((OUT/'report.json').read_text())
    assert r['complete'] and r['prepared_sha256']==digest(p) and set(r['modes'])==set(p['inventories'])
    for mode,row in r['modes'].items():
        a=load_automaton(row['automaton']);assert len(a.states)==row['states'] and sum(len(e) for _,e in a.states)==row['edges']
        assert check(a,p['inventories'][mode]['inventory'],source)==row['checks']
    write_json(OUT/'validation.json',{'verified':True,'modes':len(r['modes']),'checks':['source/code/hash identity','acyclic accepted-language count','every generated word','exact frozen/randomized membership'],'cipher_recovery_runs':0})
    print('Validated compact Latin membership')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run',action='store_true');parser.add_argument('--validate',action='store_true');a=parser.parse_args()
    if a.validate:validate()
    elif a.run:run()
    else:prepare();print('Frozen exact compact membership prototype')
