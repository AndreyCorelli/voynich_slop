"""Independent audit of fixed-width selection diagnostic records."""
from collections import Counter
import json
from pathlib import Path
from benchmarks.currier_selection_comparison import OUT,PARENT
from benchmarks.validate_currier_mechanism_comparison import edit
from voynich_smt.data.corpus import digest,write_json

def validate():
    p=json.loads((OUT/'prepared.json').read_text());parent=json.loads(PARENT.read_text())
    assert p['parent_sha256']==digest(parent)
    assert p['code_sha256']==digest(Path('benchmarks/currier_selection_comparison.py').read_text())
    for path,sha in parent['code_sha256'].items():assert digest(Path(path).read_text())==sha
    for path,sha in parent['source_sha256'].items():assert digest(json.loads(Path(path).read_text()))==sha
    cases=0;metrics=0;paired={}
    for path in sorted((OUT/'cases').glob('*.json')):
        r=json.loads(path.read_text());assert r['prepared_sha256']==digest(p)
        g=r['generation'];payload=g['payload'];nulls=set(g['null_glyphs']);codes=g['encoder']['codebook']
        inverse={c[0]:u for u,cs in codes.items() for c in cs}
        assert len(inverse)==2*len(codes) and nulls.isdisjoint(inverse)
        assert all(len(c)==1 for cs in codes.values() for c in cs)
        decoded=[''.join(inverse[x] for x in w) for l in payload for w in l]
        assert decoded==parent['passages'][g['source']][g['target_index']]['words']
        lengths=[len(w) for l in payload for w in l]
        key=(g['source'],g['target_index'],g['seed']);paired.setdefault(key,[]).append(lengths)
        if g['selection']=='word-deterministic':
            mapping={}
            for word,encoded in zip(decoded,[tuple(w) for l in payload for w in l]):
                if word in mapping:assert mapping[word]==encoded
                mapping[word]=encoded
        for rate in parent['null_rates']:
            arms=[g['profiles'][f'{kind}-null-{rate}'] for kind in ('independent','positional')];counts=[]
            for arm in arms:
                assert [[list(x for x in w if x not in nulls) for w in l] for l in arm]==payload
                count=Counter(x for l in arm for w in l for x in w if x in nulls)
                assert sum(count.values())==round(rate*sum(lengths));counts.append(count)
            assert counts[0]==counts[1]
        for expected in parent['boundary_means']:
            assert [[x for w in l for x in w] for l in g['profiles'][f'renewal-{expected}']]==[[x for w in l for x in w] for l in payload]
        for result in r['results']:
            lines=g['profiles'][result['profile']];words=[tuple(w) for l in lines for w in l];freq=Counter(words);m=result['metrics']
            assert m['token_lengths']=={str(k):v for k,v in Counter(map(len,words)).items()}
            assert m['type_lengths']=={str(k):v for k,v in Counter(map(len,freq)).items()}
            assert m['adjacent_pairs']==sum(len(l)-1 for l in lines)
            pairs=len(words)*(len(words)-1)/2
            assert abs(m['repeat_pair_fraction']-sum(v*(v-1)/2 for v in freq.values())/pairs)<1e-12
            unique=list(freq);nt=np=0
            for i,a in enumerate(unique):
                for b in unique[i+1:]:
                    if abs(len(a)-len(b))<=1 and edit(a,b)==1:nt+=1;np+=freq[a]*freq[b]
            assert abs(m['near_variant_token_pair_fraction']-np/pairs)<1e-12
            assert abs(m['near_variant_type_pair_fraction']-nt/(len(freq)*(len(freq)-1)/2))<1e-12
            metrics+=1
        cases+=1
    assert all(len(v)==2 and v[0]==v[1] for v in paired.values())
    assert cases==432 and metrics==3456
    write_json(OUT/'validation.json',{'validated':True,'prepared_sha256':digest(p),'payloads':cases,'metrics':metrics,'checks':'Frozen provenance; independent inverse-code decoding; length invariance across selections; deterministic repeated words; paired null identities/budgets/payload; renewal stream; token/type histograms and adjacency boundaries; exact repeat and full-Levenshtein near-pair rates for every record.'})
    print('Validated',cases,'payloads and',metrics,'metric records')

if __name__=='__main__':validate()
