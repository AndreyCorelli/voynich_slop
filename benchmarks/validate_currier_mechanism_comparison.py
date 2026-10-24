"""Independent conservation, provenance and one-edit checks of saved records."""
from collections import Counter
import json
from pathlib import Path
from voynich_smt.data.corpus import digest, write_json

OUT=Path('experiments/results/currier-mechanism-comparison')

def edit(a,b):
    row=list(range(len(b)+1))
    for i,x in enumerate(a,1):
        nxt=[i]
        for j,y in enumerate(b,1):nxt.append(min(nxt[-1]+1,row[j]+1,row[j-1]+(x!=y)))
        row=nxt
    return row[-1]

def validate():
    p=json.loads((OUT/'prepared.json').read_text());report=json.loads((OUT/'report.json').read_text())
    for path,sha in p['code_sha256'].items():assert digest(Path(path).read_text())==sha
    for path,sha in p['source_sha256'].items():assert digest(json.loads(Path(path).read_text()))==sha
    folios=[t['folio'] for t in p['targets']];assert len(folios)==len(set(folios))==24
    for source,passages in p['passages'].items():
        intervals=sorted((x['start'],x['end']) for x in passages)
        assert all(a[1]<=b[0] for a,b in zip(intervals,intervals[1:]))
    cases=0;metrics=0
    for path in sorted((OUT/'cases').glob('*.json')):
        r=json.loads(path.read_text());assert r['prepared_sha256']==digest(p)
        g=r['generation'];payload=g['payload'];nulls=set(g['null_glyphs'])
        assert not any(x in nulls for line in payload for word in line for x in word)
        for rate in p['null_rates']:
            arms=[g['profiles'][f'{kind}-null-{rate}'] for kind in ('independent','positional')]
            counts=[]
            for arm in arms:
                assert [[list(x for x in w if x not in nulls) for w in line] for line in arm]==payload
                c=Counter(x for line in arm for w in line for x in w if x in nulls)
                assert sum(c.values())==round(rate*sum(len(w) for line in payload for w in line))
                counts.append(c)
            assert counts[0]==counts[1]
        for expected in p['boundary_means']:
            arm=g['profiles'][f'renewal-{expected}']
            assert [[x for w in line for x in w] for line in arm]==[[x for w in line for x in w] for line in payload]
        for result in r['results']:
            lines=g['profiles'][result['profile']];words=[tuple(w) for line in lines for w in line];freq=Counter(words);m=result['metrics']
            assert m['word_count']==len(words) and m['glyph_count']==sum(map(len,words))
            assert m['token_lengths']=={str(k):v for k,v in Counter(map(len,words)).items()}
            assert m['type_lengths']=={str(k):v for k,v in Counter(map(len,freq)).items()}
            assert m['adjacent_pairs']==sum(len(line)-1 for line in lines)
            for pos in m['position'].values():assert sum(x[2] for x in pos['glyph_counts'])==m['glyph_count']
            # Check every saved near-variant statistic using full Levenshtein DP,
            # independently of the benchmark's optimized one-edit predicate.
            unique=list(freq);nt=0;np=0
            for i,a in enumerate(unique):
                for b in unique[i+1:]:
                    if abs(len(a)-len(b))<=1 and edit(a,b)==1:nt+=1;np+=freq[a]*freq[b]
            assert abs(m['near_variant_token_pair_fraction']-np/(len(words)*(len(words)-1)/2))<1e-12
            assert abs(m['near_variant_type_pair_fraction']-nt/(len(freq)*(len(freq)-1)/2))<1e-12
            metrics+=1
        cases+=1
    assert cases==report['paired_payloads']==216 and metrics==report['generated_metric_cases']==1728
    write_json(OUT/'validation.json',{'prepared_sha256':digest(p),'paired_payloads':cases,'metric_cases':metrics,'validated':True,'checks':'Frozen source/code hashes; disjoint folios/passages; exact paired null budgets/identities and payload stripping; renewal stream conservation; length histograms, adjacency boundaries, glyph-position count conservation; independent full edit-distance near-variant calculation on all records.'})
    print(f'Validated {cases} paired payloads and {metrics} metric records')

if __name__=='__main__':validate()
