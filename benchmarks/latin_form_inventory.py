"""Independent enumeration of the pinned recognizer's finite morphology rules."""
import argparse
from collections import defaultdict
import gzip
import hashlib
import json
from pathlib import Path
from time import perf_counter
from benchmarks import latin_morphology_coverage as morphology
from voynich_smt.data.corpus import digest,write_json

OUT=Path('experiments/results/latin-form-inventory')


def enumerate_forms(engine):
    from whitakers_words.matcher import Matcher
    data=engine.data;by_pos=defaultdict(list)
    for group in data.inflects.values():
        for definitions in group.values():
            for infl in definitions:
                if 1<=len(infl['ending'])<=7:by_pos[infl['pos']].append(infl)
    bases=defaultdict(set);pairs=0
    for orth,stems in data.stems.items():
        for stem in stems:
            entry=data.lookup_stem(stem['wid'])
            if not entry or not entry.get('parts'):continue
            candidates=by_pos[stem['pos']]+(by_pos['VPAR'] if stem['pos']=='V' else [])
            for infl in candidates:
                # The parser never strips the entire query as an ending.
                word=orth+infl['ending']
                if not orth or not word.isalpha() or not Matcher(stem,infl).check():continue
                bases[word].add(stem['pos']);pairs+=1
            if orth in data.wordkeys:
                for infl in data.empty.get(stem['pos'],[]):
                    if Matcher(stem,infl).check() and orth.isalpha():bases[orth].add(stem['pos']);pairs+=1
    uniques=set()
    for word,entries in data.uniques.items():
        if word.isalpha() and entries:uniques.add(word);bases[word].update(e['pos'] for e in entries)
    words=set(bases);clitic_count=0
    for word,positions in bases.items():
        addons=data.addons['tackons']+data.addons['packons' if word.startswith('qu') else 'not_packons']
        for addon in addons:
            pos=addon['pos'].split()[0]
            # Unique analyses bypass the regular enclitic-position filter upstream.
            if word in uniques or pos in ('X','PACK') or pos in positions:
                surface=word+addon['orth']
                if surface.isalpha():words.add(surface);clitic_count+=1
    return words,{'base_forms':len(bases),'unique_forms':len(uniques),'matched_stem_inflection_pairs':pairs,'clitic_derivations':clitic_count}


def prepare():
    source=morphology.prepare()
    identity={'morphology_source_sha256':digest(source),'generator_sha256':digest(Path(__file__).read_text())}
    path=OUT/'prepared.json'
    if path.exists():
        p=json.loads(path.read_text())
        if p['identity']!=identity:raise ValueError('Frozen data/code changed')
        return p
    protocol={'identity':identity,'modes':morphology.MODES,'solver_runs':0,
        'selection':'Enumerate all filtered upstream stems with compatible filtered endings through Matcher, eligible empty-ending entries and unique forms; apply one built-in enclitic layer with upstream position rules. No target queries, target-word additions, size cap, frequency reranking or rule tuning. Canonical i/u spelling as resource, not original u/v-preserving cipher alphabet.',
        'scope':'Finite inventory of this pinned implementation, not complete historical Latin. Known analyzer/filter limitations remain. Verify equivalence on all frozen 3406 query types plus deterministic independent sample; generation completeness is relative to documented finite rules. Full inventories and their union with canonical attested vocabulary audited; no new cipher solves or claims of solver readiness/performance.'}
    p={'identity':identity,'protocol':protocol};write_json(OUT/'protocol.json',protocol);write_json(path,p);return p


def write_inventory(mode,words):
    path=OUT/(mode+'.txt.gz')
    data=('\n'.join(sorted(words))+'\n').encode()
    path.write_bytes(gzip.compress(data,mtime=0))
    return {'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'word_count':len(words),'uncompressed_sha256':hashlib.sha256(data).hexdigest(),
            'minimum_length':min(map(len,words)),'maximum_length':max(map(len,words))}


def audit(words,source):
    canonical=morphology.canonical
    def block(plain):
        missing=[''.join(w) for w in plain if canonical(''.join(w)) not in words]
        return {'missing_occurrences':len(missing),'missing_words':missing}
    passage=source['fixed_passage'];grid=[block(b['words'])['missing_occurrences'] for b in source['grid_windows']]
    return {'training':block(passage['plaintext']['words']),'holdout':block(passage['holdout_plaintext']['words']),
            'grid':{'windows':len(grid),'at_most_one_missing':sum(n<=1 for n in grid),'median_missing':sorted(grid)[len(grid)//2]}}


def verify_equivalence(words,engine,source):
    mismatches=[]
    for query in source['query_words']:
        recognized=morphology.evidence(engine,query)['recognized']
        if (morphology.canonical(query) in words)!=recognized:mismatches.append(query)
    if mismatches:raise RuntimeError('Inventory/parser disagreement: '+repr(mismatches[:20]))
    # Independent lexical sample, no target-based sampling or adjustments.
    ordered=sorted(words);step=max(1,len(ordered)//1024);sample=ordered[::step][:1024]
    bad=[w for w in sample if not morphology.evidence(engine,w)['recognized']]
    if bad:raise RuntimeError('Generated forms unrecognized: '+repr(bad[:20]))
    return {'target_query_types':len(source['query_words']),'independent_generated_sample':len(sample),'disagreements':0}


def run():
    p=prepare();source=morphology.prepare();path=OUT/'report.json'
    r=json.loads(path.read_text()) if path.exists() else {'prepared_sha256':digest(p),'modes':{},'complete':False}
    if r['prepared_sha256']!=digest(p):raise ValueError('Checkpoint changed')
    attested={morphology.canonical(''.join(w)) for w in source['attested_words']}
    for mode in morphology.MODES:
        if mode in r['modes']:continue
        print(mode,'enumerating independently',flush=True)
        engine=morphology.parser(mode);start=perf_counter();words,stats=enumerate_forms(engine)
        checks=verify_equivalence(words,engine,source)
        row={'inventory':write_inventory(mode,words),'generation':stats,'generation_and_check_seconds':perf_counter()-start,'equivalence':checks,
             'coverage':audit(words,source),'combined_coverage':audit(words|attested,source)}
        r['modes'][mode]=row;write_json(path,r);print(mode,len(words),'forms',row['coverage'],flush=True)
    r['complete']=True;write_json(path,r);return r


def validate():
    p=prepare();source=morphology.prepare();r=json.loads((OUT/'report.json').read_text())
    assert r['complete'] and r['prepared_sha256']==digest(p) and set(r['modes'])==set(morphology.MODES)
    attested={morphology.canonical(''.join(w)) for w in source['attested_words']}
    for mode,row in r['modes'].items():
        path=Path(row['inventory']['path']);raw=gzip.decompress(path.read_bytes())
        assert hashlib.sha256(path.read_bytes()).hexdigest()==row['inventory']['sha256'] and hashlib.sha256(raw).hexdigest()==row['inventory']['uncompressed_sha256']
        words=set(raw.decode().splitlines());assert len(words)==row['inventory']['word_count']
        generated,stats=enumerate_forms(morphology.parser(mode));assert generated==words and stats==row['generation']
        assert digest(verify_equivalence(words,morphology.parser(mode),source))==digest(row['equivalence'])
        assert digest(audit(words,source))==digest(row['coverage']) and digest(audit(words|attested,source))==digest(row['combined_coverage'])
    write_json(OUT/'validation.json',{'verified':True,'modes':len(r['modes']),'checks':['source/code identity','compressed inventory hashes','full independent regeneration','recognizer equivalence on frozen queries and independent sample','coverage reconstruction'],'solver_runs':0})
    print('Validated independent Latin form inventories')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run',action='store_true');parser.add_argument('--validate',action='store_true');a=parser.parse_args()
    if a.validate:validate()
    elif a.run:run()
    else:prepare();print('Frozen target-independent form generation')
