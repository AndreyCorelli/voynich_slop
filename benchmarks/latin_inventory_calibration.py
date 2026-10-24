"""Inventory acceptance controls and public candidate-scale audit, no SMT."""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import random
from benchmarks import latin_form_inventory as inventory
from benchmarks import latin_morphology_coverage as morphology
from voynich_smt.data.corpus import digest,write_json

OUT=Path('experiments/results/latin-inventory-calibration')
SEEDS=(4701,4702,4703)


def controls(words,seed):
    rng=random.Random(seed);letters='abcdefghiklmnopqrstu xyz'.replace(' ','')
    shuffled={};uniform={};unavailable=[]
    for word in sorted(words):
        draws=0;changed=None
        for _ in range(100):
            chars=list(word);rng.shuffle(chars);candidate=''.join(chars);draws+=1
            if candidate!=word:changed=candidate;break
        if changed is None:unavailable.append(word)
        else:shuffled[word]={'word':changed,'draws':draws}
        # Independent letters, same exact length. No rejection for accidental words.
        uniform[word]=''.join(rng.choice(letters) for _ in word)
    return {'seed':seed,'typewise_anagram':shuffled,'uniform_letters':uniform,'unavailable_anagrams':unavailable}


def prepare():
    source=morphology.prepare();report=json.loads((inventory.OUT/'report.json').read_text());frozen=inventory.prepare()
    if not report['complete'] or report['prepared_sha256']!=digest(frozen):raise ValueError('Unmatched generated inventories')
    identity={'morphology_targets_sha256':digest(source),'inventory_report_sha256':digest(report),'generator_sha256':digest(Path(__file__).read_text())}
    path=OUT/'prepared.json'
    if path.exists():
        p=json.loads(path.read_text())
        if p['identity']!=identity:raise ValueError('Frozen inputs/code changed')
        return p
    words=sorted({morphology.canonical(w) for w in source['query_words']})
    # Cipher lengths are regenerated from the independent fixed synthetic keys;
    # truth is used to build fixtures, never to select inventory candidates.
    from benchmarks.natural_passage_replication import key
    from voynich_smt.models.text import Text
    passage=source['fixed_passage'];alphabet=tuple(sorted({s for s in passage['alphabet']['symbols'] if s not in 'jv'}|{'i','u'}))
    train=Text(tuple(tuple(morphology.canonical(''.join(w))) for w in passage['plaintext']['words']))
    lengths={}
    for profile in ('fixed-two','mixed-one-two-three'):
        encoder=key(alphabet,tuple('uvwxyz'),profile,4501)
        lengths[profile]=list(map(len,encoder.encode(train,(0,)*train.size).words))
    protocol={'identity':identity,'seeds':SEEDS,'max_anagram_draws':100,'solver_runs':0,
        'selection':'All distinct canonicalized frozen Latin query types. Each seed supplies one changed within-type anagram (max100 draws; unavailable preserved) and one same-length independent-uniform-letter string over the fixed canonical alphabet. No collision or inventory-membership rejection, no tuning. Scores by type and later-block token weighting. Controls are not guaranteed non-Latin and are not encryption controls.',
        'scope':'Exact generated inventory and canonical attested-union recognition only. Real-word coverage and randomized acceptance reported separately; no population false-positive estimate or p-values. Candidate scale counts every independent inventory entry whose letter length could encode each fixed synthetic ciphertext word under L1-3 and public max length. No true plaintext length or key constraints used to prune candidates. Counts are an upper bound before structural/prefix pruning, not solver timings. Canonical i/u fixture differs from prior u/v model. No SMT or manuscript inference.'}
    p={'identity':identity,'protocol':protocol,'query_types':words,'controls':[controls(words,seed) for seed in SEEDS],
       'grid_windows':source['grid_windows'],'cipher_word_lengths':lengths,'inventory_records':report['modes'],'attested_words':source['attested_words']}
    write_json(OUT/'protocol.json',protocol);write_json(path,p);return p


def acceptance(words,control,weights):
    summaries={}
    for family in ('typewise_anagram','uniform_letters'):
        mapping={w:r['word'] for w,r in control[family].items()} if family=='typewise_anagram' else control[family]
        hits={w for w,c in mapping.items() if c in words}
        summaries[family]={'accepted_types':len(hits),'available_types':len(mapping),
            'accepted_grid_tokens':sum(weights[w] for w in hits),'available_grid_tokens':sum(weights[w] for w in mapping),
            'accepted_pairs':[{'original':w,'control':mapping[w]} for w in sorted(hits)]}
    return summaries


def candidate_scale(histogram,cipher_lengths):
    maximum=max(histogram)
    rows=[]
    for length in cipher_lengths:
        lo=max(1,(length+2)//3);hi=min(length,maximum)
        rows.append({'ciphertext_length':length,'public_plain_length_min':lo,'public_plain_length_max':hi,
                     'candidate_words':sum(n for k,n in histogram.items() if lo<=k<=hi)})
    return {'word_rows':rows,'total_membership_candidates':sum(r['candidate_words'] for r in rows),
            'maximum_candidates_per_word':max(r['candidate_words'] for r in rows)}


def calculate(p):
    weights=Counter(morphology.canonical(''.join(w)) for block in p['grid_windows'] for w in block['words'])
    query=set(p['query_types']);attested={morphology.canonical(''.join(w)) for w in p['attested_words']};rows=[]
    for mode,record in p['inventory_records'].items():
        path=Path(record['inventory']['path']);raw=path.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=record['inventory']['sha256']:raise ValueError('Inventory hash changed')
        forms=set(gzip.decompress(raw).decode().splitlines())
        for variant,words in [('morphology-only',forms),('plus-attested',forms|attested)]:
            hist=Counter(map(len,words));rows.append({'mode':mode,'variant':variant,'inventory_size':len(words),
                'real_accepted_types':len(query&words),'real_query_types':len(query),
                'real_accepted_grid_tokens':sum(n for w,n in weights.items() if w in words),'real_grid_tokens':sum(weights.values()),
                'length_histogram':{str(k):v for k,v in sorted(hist.items())},
                'control_acceptance':[{'seed':c['seed'],'unavailable_anagrams':len(c['unavailable_anagrams']),'families':acceptance(words,c,weights)} for c in p['controls']],
                'candidate_scale':{profile:candidate_scale(hist,lengths) for profile,lengths in p['cipher_word_lengths'].items()}})
    return {'prepared_sha256':digest(p),'complete':True,'rows':rows}


def run():
    r=calculate(prepare());write_json(OUT/'report.json',r);return r


def validate():
    p=prepare();r=json.loads((OUT/'report.json').read_text());assert digest(r)==digest(calculate(p))
    assert digest(p['controls'])==digest([controls(p['query_types'],s) for s in SEEDS])
    for c in p['controls']:
        for w,item in c['typewise_anagram'].items():assert item['word']!=w and Counter(item['word'])==Counter(w)
        for w,item in c['uniform_letters'].items():assert len(w)==len(item)
    write_json(OUT/'validation.json',{'verified':True,'rows':len(r['rows']),'checks':['source/code/inventory hashes','deterministic controls','anagram/length invariants','acceptance reconstruction','public candidate counts'],'solver_runs':0})
    print('Validated inventory acceptance and scale audit')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run',action='store_true');parser.add_argument('--validate',action='store_true');a=parser.parse_args()
    if a.validate:validate()
    elif a.run:
        for row in run()['rows']:
            print(row['mode'],row['variant'],row['inventory_size'],[(c['seed'],[(family,v['accepted_types'],v['available_types']) for family,v in c['families'].items()]) for c in row['control_acceptance']],row['candidate_scale']['fixed-two']['total_membership_candidates'])
    else:prepare();print('Frozen randomized acceptance and scale audit')
