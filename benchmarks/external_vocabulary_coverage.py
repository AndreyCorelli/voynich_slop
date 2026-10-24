"""Broader attested vocabularies from cached works excluding both test sources."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import tarfile
import xml.etree.ElementTree as ET
from benchmarks import independent_vocabulary_coverage as previous
from benchmarks.expanded_medieval_latin import WORKS,load_work
from benchmarks.historical_word_lengths import latin_segments,source,GERMAN_IDS
from benchmarks.german_regional_audit import corrected_counts,EXCLUSIONS
from voynich_smt.data.corpus import digest,write_json

OUT=Path('experiments/results/external-vocabulary-coverage')
SIZES=(1024,2048,4096,8192)


def normalize_latin(words,alphabet):
    counts=Counter();excluded=Counter()
    for word in words:
        if not word:continue
        word=word.replace('j','i')
        if not set(word)<=alphabet:excluded[word]+=1;continue
        counts[tuple(word)]+=1
    return counts,excluded


def external_sources(alphabets):
    counts={'latin':Counter(),'swabian':Counter()};metadata=[]
    # All cached expanded Latin works; no Caesar records or target inventories.
    for work in WORKS:
        segments,manifests,quality=load_work(work)
        found,excluded=normalize_latin((w for segment in segments for w in segment),alphabets['latin'])
        counts['latin'].update(found)
        metadata.append({'language':'latin','id':work['id'],'manifests':manifests,'extraction_audit':quality,
                         'normalized_counts':sorted(found.items()),'outside_alphabet_counts':sorted(excluded.items())})
    for filename,incipit in (('latin-aquinas-ente.html','Quia parvus error'),('latin-caroli.html','Secundis sedentibus')):
        segments,manifest=latin_segments(filename,incipit)
        found,excluded=normalize_latin((w for segment in segments for w in segment),alphabets['latin'])
        counts['latin'].update(found)
        metadata.append({'language':'latin','id':filename,'manifest':manifest,'normalized_counts':sorted(found.items()),'outside_alphabet_counts':sorted(excluded.items())})
    raw,manifest=source('german-corpus.tar.xz')
    with tarfile.open('data/raw/historical-lengths/german-corpus.tar.xz') as archive:
        for number in GERMAN_IDS:
            if number==123:continue
            payload=archive.extractfile(f'XML/{number}.xml').read()
            found,events=corrected_counts(ET.fromstring(payload),EXCLUSIONS.get(number,{}))
            eligible=Counter({tuple(w):n for w,n in found.items() if set(w)<=alphabets['swabian']})
            counts['swabian'].update(eligible)
            metadata.append({'language':'swabian','id':number,'archive_manifest':manifest,'xml_sha256':hashlib.sha256(payload).hexdigest(),
                             'normalization_events':events,'normalized_counts':sorted(eligible.items())})
    return counts,metadata


def ranked(counts):
    return sorted(counts,key=lambda w:(-counts[w],w))


def prepare():
    baseline=previous.prepare()
    alphabets={lang:set(data['fixed_passage']['alphabet']['symbols']) for lang,data in baseline['languages'].items()}
    counts,metadata=external_sources(alphabets)
    paths=(Path(__file__),Path('benchmarks/expanded_medieval_latin.py'),Path('benchmarks/historical_word_lengths.py'),
           Path('benchmarks/german_regional_audit.py'),Path('benchmarks/german_selection.py'),Path(previous.__file__))
    identity={'baseline_sha256':digest(baseline),'external_sources_sha256':digest(metadata),'code_sha256':{str(p):digest(p.read_text()) for p in paths}}
    path=OUT/'prepared.json'
    if path.exists():
        p=json.loads(path.read_text())
        if p['identity']!=identity:raise ValueError('Frozen sources/code changed')
        return p
    languages={}
    for lang,data in baseline['languages'].items():
        prefix=Counter({tuple(r['word']):r['prefix_count'] for r in data['word_provenance']})
        combined=prefix+counts[lang]
        languages[lang]={'fixed_passage':data['fixed_passage'],'grid_windows':data['grid_windows'],'rejected_grid_starts':data['rejected_grid_starts'],
                         'rankings':{'external-only':ranked(counts[lang]),'external-plus-prefix':ranked(combined)},
                         'external_types':len(counts[lang]),'prefix_types':len(prefix)}
    protocol={'identity':identity,'sizes':SIZES,'include_full_inventory':True,'solver_runs':0,
        'selection':'Use all four already-cached expanded medieval Latin works plus Aquinas/Caroli; no Caesar. Use cached German IDs113,133,143,153,223,233,243,253; exclude target source123 entirely. Existing extraction/corrected normalization, Latin j->i and u/v preserved, fixed target-language alphabets. Frequency-ranked external-only and external+earlier-prefix dictionaries, lexical ties. No target-word additions, morphology generation, downloads or outcome-based source selection.',
        'scope':'Attested edited-source forms, not comprehensive historical lexicons. Eight German sources pool regional spellings without claiming dialect equivalence. Latin sources differ in period/genre from Caesar. Known source-specific exclusions retained; other editorial noise may remain. Frozen target passages and prior later-source grid, coverage only. Admission max one missing occurrence plus public maximum length. Correlated grids; no solver or manuscript inference.'}
    p={'identity':identity,'protocol':protocol,'external_source_provenance':metadata,'languages':languages}
    write_json(OUT/'protocol.json',protocol);write_json(path,p);return p


def calculate(p):
    rows=[]
    for lang,data in p['languages'].items():
        for ranking,words in data['rankings'].items():
            for size in (*SIZES,'full-inventory'):
                n=len(words) if size=='full-inventory' else size
                row={'language':lang,'ranking':ranking,'requested_size':size,'available_types':len(words)}
                if n>len(words):row['status']='UNAVAILABLE';rows.append(row);continue
                members=set(map(tuple,words[:n]));passage=data['fixed_passage']
                audits=[previous.audit(w['words'],members) for w in data['grid_windows']]
                row.update(status='AUDITED',dictionary_size=n,training=previous.audit(passage['plaintext']['words'],members),
                           heldout=previous.audit(passage['holdout_plaintext']['words'],members),
                           grid={'eligible_windows':len(audits),'admitted_one_oov_windows':sum(a['admitted_one_oov'] for a in audits),
                                 'median_missing': sorted(a['missing_occurrences'] for a in audits)[len(audits)//2] if audits else None,
                                 'missing_occurrence_histogram':dict(Counter(str(a['missing_occurrences']) for a in audits))})
                rows.append(row)
    return {'prepared_sha256':digest(p),'complete':True,'rows':rows}


def run():
    r=calculate(prepare());write_json(OUT/'report.json',r);return r


def validate():
    p=prepare();r=json.loads((OUT/'report.json').read_text());assert digest(r)==digest(calculate(p))
    baseline=previous.prepare();alphabets={lang:set(data['fixed_passage']['alphabet']['symbols']) for lang,data in baseline['languages'].items()}
    counts,metadata=external_sources(alphabets);assert digest(metadata)==digest(p['external_source_provenance'])
    for lang,data in p['languages'].items():
        original=baseline['languages'][lang];prefix=Counter({tuple(r['word']):r['prefix_count'] for r in original['word_provenance']})
        assert digest(data['rankings'])==digest({'external-only':ranked(counts[lang]),'external-plus-prefix':ranked(prefix+counts[lang])})
        assert digest(data['fixed_passage'])==digest(original['fixed_passage']) and digest(data['grid_windows'])==digest(original['grid_windows'])
    assert all(m['id']!=123 for m in metadata if m['language']=='swabian')
    write_json(OUT/'validation.json',{'verified':True,'rows':len(r['rows']),'checks':['cached raw checksums','target-source exclusion','normalization provenance','frequency ranking/nesting','unchanged targets/grid','coverage reconstruction'],'solver_runs':0})
    print('Validated broader independent vocabulary coverage')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run',action='store_true');parser.add_argument('--validate',action='store_true');a=parser.parse_args()
    if a.validate:validate()
    elif a.run:
        for row in run()['rows']:print(row['language'],row['ranking'],row['requested_size'],row['status'],row.get('training',{}).get('missing_occurrences'),row.get('grid'))
    else:prepare();print('Frozen external coverage audit')
