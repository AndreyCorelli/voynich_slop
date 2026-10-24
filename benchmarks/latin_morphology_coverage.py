"""Pinned independent morphology recognition audit, no cipher solving."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
from benchmarks import external_vocabulary_coverage as external
from voynich_smt.data.corpus import digest,write_json

OUT=Path('experiments/results/latin-morphology-coverage')
VENDOR=Path('data/vendor/whitakers-words')
ARCHIVE=Path('data/raw/latin-morphology/whitakers-words-92eb56f.tar.gz')
COMMIT='92eb56f188ec9dadecca01ca34d3c9fd13d746da'
MODES={'upstream-default':{},'through-medieval-rare':{'age':'F','frequency':'F'}}


def canonical(word):
    return word.replace('j','i').replace('v','u')


def parser(mode):
    sys.path.insert(0,str(VENDOR.resolve())) if str(VENDOR.resolve()) not in sys.path else None
    from whitakers_words.parser import Parser
    return Parser(**MODES[mode])


def evidence(engine,word):
    parsed=engine.parse(word);analyses=[]
    for form in parsed.forms:
        for analysis in form.analyses.values():
            analyses.append({'lexeme_id':analysis.lexeme.id,'roots':list(analysis.lexeme.roots),
                'part_of_speech':analysis.lexeme.wordType.name,'properties':list(analysis.lexeme.props),
                'enclitic':analysis.enclitic.text if analysis.enclitic else None,
                'inflections':[{'stem':i.stem,'ending':i.affix,'part_of_speech':i.wordType.name,
                                'features':{k:v.name for k,v in i.features.items()}} for i in analysis.inflections]})
    for analysis in analyses:
        analysis['inflections'].sort(key=lambda x:json.dumps(x,sort_keys=True))
    analyses.sort(key=lambda x:json.dumps(x,sort_keys=True))
    return {'query':word,'canonical_query':parsed.text,'recognized':bool(analyses),'analyses':analyses}


def prepare():
    baseline=external.prepare();latin=baseline['languages']['latin']
    paths=[p for p in (VENDOR/'whitakers_words').rglob('*') if p.is_file() and '__pycache__' not in str(p) and p.suffix!='.db']
    paths.extend([VENDOR/'LICENSE',Path(__file__)])
    identity={'external_audit_sha256':digest(baseline),'upstream_commit':COMMIT,'archive_sha256':hashlib.sha256(ARCHIVE.read_bytes()).hexdigest(),
              'code_data_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}}
    path=OUT/'prepared.json'
    if path.exists():
        p=json.loads(path.read_text())
        if p['identity']!=identity:raise ValueError('Frozen morphology/data/targets changed')
        return p
    passage=latin['fixed_passage'];words=sorted({''.join(w) for w in passage['plaintext']['words']+passage['holdout_plaintext']['words']}|{''.join(w) for block in latin['grid_windows'] for w in block['words']})
    protocol={'identity':identity,'modes':MODES,'solver_runs':0,
        'resource':'https://github.com/blagae/whitakers_words/tree/'+COMMIT,
        'selection':'Pinned independent Whitaker Python code/data, no target additions or morphology rule edits. Two fixed settings: upstream defaults; age F/frequency F sensitivity for inflections through medieval age and rare frequency. Lexeme age is not fully filtered by this API. Existing Latin targets and grid unchanged. Query all target types, no tuning after recognition.',
        'scope':'Morphological recognition, not enumerated finite dictionary or proof of historical attestation. Parser merges j/i and v/u, accepts its built-in enclitic rules. Compare exact attested external+prefix vocabulary, orthography-only canonical lookup, morphology alone, and combined recognition. Queries do not train resource. Counts<=1 assess membership coverage only; future solver length bounds/finite enumeration not yet established. Known upstream API issues remain; no manuscript inference.'}
    p={'identity':identity,'protocol':protocol,'query_words':words,'fixed_passage':passage,'grid_windows':latin['grid_windows'],
       'attested_words':latin['rankings']['external-plus-prefix']}
    write_json(OUT/'protocol.json',protocol);write_json(path,p);return p


def missing(words,accepted):
    return {'missing_occurrences':sum(''.join(w) not in accepted for w in words),
            'missing_words':[''.join(w) for w in words if ''.join(w) not in accepted]}


def calculate(p,recognitions):
    attested={''.join(w) for w in p['attested_words']};canon={canonical(w) for w in attested}
    orth={w for w in p['query_words'] if canonical(w) in canon}
    memberships={'attested-exact':attested,'attested-orthography-only':orth}
    for mode,records in recognitions.items():
        recognized={w for w,r in records.items() if r['recognized']}
        memberships[mode+'-morphology-only']=recognized
        memberships[mode+'-combined']=attested|recognized
    rows=[]
    for name,accepted in memberships.items():
        audit=missing(p['fixed_passage']['plaintext']['words'],accepted);held=missing(p['fixed_passage']['holdout_plaintext']['words'],accepted)
        blocks=[missing(b['words'],accepted)['missing_occurrences'] for b in p['grid_windows']]
        rows.append({'inventory':name,'training':audit,'heldout':held,'grid':{'windows':len(blocks),
                     'at_most_one_missing':sum(n<=1 for n in blocks),'median_missing':sorted(blocks)[len(blocks)//2]}})
    return {'prepared_sha256':digest(p),'recognition_sha256':digest(recognitions),'complete':True,'rows':rows}


def run():
    p=prepare();path=OUT/'recognitions.json'
    cache=json.loads(path.read_text()) if path.exists() else {'prepared_sha256':digest(p),'modes':{}}
    if cache['prepared_sha256']!=digest(p):raise ValueError('Recognition checkpoint changed')
    for mode in MODES:
        if mode in cache['modes']:continue
        engine=parser(mode);cache['modes'][mode]={w:evidence(engine,w) for w in p['query_words']}
        write_json(path,cache);print(mode,'recognized',sum(r['recognized'] for r in cache['modes'][mode].values()),'of',len(p['query_words']),flush=True)
    report=calculate(p,cache['modes']);write_json(OUT/'report.json',report);return report


def validate():
    p=prepare();cache=json.loads((OUT/'recognitions.json').read_text());report=json.loads((OUT/'report.json').read_text())
    assert cache['prepared_sha256']==digest(p) and set(cache['modes'])==set(MODES)
    for mode in MODES:
        engine=parser(mode)
        assert set(cache['modes'][mode])==set(p['query_words'])
        assert digest(cache['modes'][mode])==digest({w:evidence(engine,w) for w in p['query_words']})
    assert digest(report)==digest(calculate(p,cache['modes']))
    write_json(OUT/'validation.json',{'verified':True,'rows':len(report['rows']),'checks':['pinned raw/code/data identity','unchanged targets','full recognition regeneration','orthography-only comparison','membership coverage reconstruction'],'solver_runs':0})
    print('Validated pinned Latin morphology audit')

if __name__=='__main__':
    parser_cli=argparse.ArgumentParser(description=__doc__);parser_cli.add_argument('--run',action='store_true');parser_cli.add_argument('--validate',action='store_true');a=parser_cli.parse_args()
    if a.validate:validate()
    elif a.run:
        for row in run()['rows']:print(row)
    else:prepare();print('Frozen Latin morphology coverage protocol')
