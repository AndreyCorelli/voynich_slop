"""No-solver coverage ladder from independent source-prefix vocabularies."""
import argparse
from collections import Counter
import json
from pathlib import Path
from benchmarks import unseeded_vocabulary_calibration as frozen
from benchmarks import natural_passage_replication as natural
from voynich_smt.data.corpus import digest,write_json

OUT=Path('experiments/results/independent-vocabulary-coverage')
SIZES=(256,512,1024,2048,4096)


def inventories(records,allowed,alphabet):
    counts=Counter();first={}
    for index,r in enumerate(records[:len(records)//2]):
        w=tuple(r['tokens'])
        if r.get('excluded_reason') is not None or not w or w not in allowed or not set(w)<=alphabet:continue
        counts[w]+=1;first.setdefault(w,index)
    if not counts:raise ValueError('Empty eligible prefix')
    return {'corpus-order':list(first),'frequency':sorted(counts,key=lambda w:(-counts[w],w))},counts,first


def audit(words,members):
    missing=[i for i,w in enumerate(words) if tuple(w) not in members]
    maximum=max(map(len,members))
    lengths=[i for i,w in enumerate(words) if not 1<=len(w)<=maximum]
    return {'missing_occurrences':len(missing),'missing_types':len({tuple(words[i]) for i in missing}),
            'missing_positions':missing,'outside_public_length_positions':lengths,'admitted_one_oov':len(missing)<=1 and not lengths}


def windows(records,allowed,alphabet):
    # Fixed nonoverlapping grid, no coverage-based selection or shifted retries.
    selected=[];rejected=[]
    for start in range(len(records)//2,len(records)-23,24):
        block=records[start:start+24];words=[tuple(r['tokens']) for r in block]
        if any(r.get('excluded_reason') is not None or not w or w not in allowed or not set(w)<=alphabet for r,w in zip(block,words)):
            rejected.append(start);continue
        selected.append({'start':start,'words':words})
    return selected,rejected


def prepare():
    source=frozen.prepare();records,templates,sources=natural.load_sources()
    paths=(Path(__file__),Path(frozen.__file__),Path(natural.__file__))
    identity={'frozen_passages_sha256':digest(source),'sources':sources,'code_sha256':{str(p):digest(p.read_text()) for p in paths}}
    path=OUT/'prepared.json'
    if path.exists():
        p=json.loads(path.read_text())
        if p['identity']!=identity:raise ValueError('Frozen identity changed')
        return p
    languages={}
    for lang,rs in records.items():
        t=templates[lang]['request'];allowed=set(map(tuple,t['dictionary']['words']));alphabet=set(t['plaintext_alphabet']['symbols'])
        rankings,counts,first=inventories(rs,allowed,alphabet);blocks,rejected=windows(rs,allowed,alphabet)
        languages[lang]={'rankings':rankings,'word_provenance':[{'word':w,'prefix_count':counts[w],'first_record':first[w]} for w in rankings['corpus-order']],
            'prefix_records':len(rs)//2,'prefix_types':len(counts),'fixed_passage':source['passages'][lang],
            'grid_windows':blocks,'rejected_grid_starts':rejected}
    protocol={'identity':identity,'sizes':SIZES,'rankings':['corpus-order','frequency'],'include_full_prefix':True,'solver_runs':0,
        'selection':'Vocabulary learned only from eligible first-half source records. Corpus order and descending prefix frequency with lexical ties; no target-word reservation. Nested requested sizes 256/512/1024/2048/4096, mark unavailable sizes instead of broadening; full-prefix inventory audits coverage ceiling. Frozen new passages plus all eligible nonoverlapping 24-word blocks on midpoint-anchored second-half grid. Reject whole invalid blocks, no coverage selection or shifting.',
        'scope':'One-OOV occurrence admission requires missing count<=1 and public dictionary length coverage. Same-source early/later split, fixed corrected inventory/alphabet/normalization still assisted. Coverage only, no cipher recovery or language inference. Windows/passages may overlap and are not independent observations. Full-prefix ceiling diagnoses words never seen in vocabulary-building half.'}
    p={'identity':identity,'protocol':protocol,'languages':languages};write_json(OUT/'protocol.json',protocol);write_json(path,p);return p


def calculate(p):
    rows=[]
    for lang,data in p['languages'].items():
        for ranking,words in data['rankings'].items():
            for size in (*SIZES,'full-prefix'):
                n=len(words) if size=='full-prefix' else size
                row={'language':lang,'ranking':ranking,'requested_size':size,'available_types':len(words)}
                if n>len(words):row['status']='UNAVAILABLE';rows.append(row);continue
                members=set(map(tuple,words[:n]));passage=data['fixed_passage']
                row.update(status='AUDITED',dictionary_size=n,
                    training=audit(passage['plaintext']['words'],members),
                    heldout=audit(passage['holdout_plaintext']['words'],members))
                audits=[audit(w['words'],members) for w in data['grid_windows']];miss=sorted(a['missing_occurrences'] for a in audits)
                row['grid']={'eligible_windows':len(audits),'rejected_windows':len(data['rejected_grid_starts']),
                    'admitted_one_oov_windows':sum(a['admitted_one_oov'] for a in audits),
                    'missing_occurrence_histogram':dict(Counter(map(str,miss))),
                    'mean_missing':sum(miss)/len(miss) if miss else None,
                    'median_missing':((miss[(len(miss)-1)//2]+miss[len(miss)//2])/2) if miss else None}
                rows.append(row)
    return {'prepared_sha256':digest(p),'complete':True,'rows':rows}


def run():
    r=calculate(prepare());write_json(OUT/'report.json',r);return r


def validate():
    p=prepare();saved=json.loads((OUT/'report.json').read_text());assert digest(saved)==digest(calculate(p))
    records,templates,_=natural.load_sources()
    for lang,data in p['languages'].items():
        t=templates[lang]['request'];allowed=set(map(tuple,t['dictionary']['words']));alphabet=set(t['plaintext_alphabet']['symbols'])
        rankings,counts,first=inventories(records[lang],allowed,alphabet);blocks,rejected=windows(records[lang],allowed,alphabet)
        assert digest(rankings)==digest(data['rankings']) and digest(blocks)==digest(data['grid_windows']) and rejected==data['rejected_grid_starts']
        assert digest([{'word':w,'prefix_count':counts[w],'first_record':first[w]} for w in rankings['corpus-order']])==digest(data['word_provenance'])
    write_json(OUT/'validation.json',{'verified':True,'rows':len(saved['rows']),'checks':['source/code hashes','prefix-only ranking/provenance','fixed second-half grid','nested coverage audits','unavailable sizes','full-prefix ceiling'],'solver_runs':0})
    print('Validated independent vocabulary coverage')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run',action='store_true');parser.add_argument('--validate',action='store_true');a=parser.parse_args()
    if a.validate:validate()
    elif a.run:
        for row in run()['rows']:
            print(row['language'],row['ranking'],row['requested_size'],row['status'],row.get('training',{}).get('missing_occurrences'),row.get('grid',{}).get('admitted_one_oov_windows'))
    else:prepare();print('Frozen coverage ladder; no solver runs')
