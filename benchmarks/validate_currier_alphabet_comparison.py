"""Independent audit of saved 25-label capacity comparison."""
from collections import Counter,defaultdict
import json
from pathlib import Path
from benchmarks.currier_alphabet_comparison import OUT,PARENT
from benchmarks.validate_currier_mechanism_comparison import edit
from voynich_smt.data.corpus import digest,write_json

def validate():
    p=json.loads((OUT/'prepared.json').read_text());parent=json.loads(PARENT.read_text())
    assert digest(parent)==p['parent_sha256']
    assert digest(Path('benchmarks/currier_alphabet_comparison.py').read_text())==p['code_sha256']
    for path,sha in parent['code_sha256'].items():assert digest(Path(path).read_text())==sha
    for path,sha in parent['source_sha256'].items():assert digest(json.loads(Path(path).read_text()))==sha
    for source,a in p['allocations'].items():
        counts=Counter(u for i,t in enumerate(parent['targets']) if t['split']=='development' for w in parent['passages'][source][i]['words'] for u in w)
        assert dict(counts)==p['development_frequencies'][source]
        alphabet=sorted(a['mono']);assert set(alphabet)=={u for w in parent['sources'][source]['segments'] for word in w if word for u in word}
        expected={u:1 for u in alphabet}
        for u in sorted(alphabet,key=lambda u:(-counts[u],u))[:25-len(alphabet)]:expected[u]+=1
        assert a['allocated']==expected and sum(expected.values())==25
    groups=defaultdict(dict);cases=0
    for path in sorted((OUT/'cases').glob('*.json')):
        r=json.loads(path.read_text());assert r['prepared_sha256']==digest(p)
        codebook=r['encoder']['codebook'];inverse={c[0]:u for u,cs in codebook.items() for c in cs}
        assert len(inverse)==sum(map(len,codebook.values()))<=25
        assert set(inverse)<=set(parent['glyphs']) and all(len(c)==1 for cs in codebook.values() for c in cs)
        kind,selection=r['arm'].split('-',1)
        assert {u:len(cs) for u,cs in codebook.items()}==p['allocations'][r['source']][kind]
        lines=r['payload'];words=[tuple(w) for l in lines for w in l];plain=[''.join(inverse[g] for g in w) for w in words]
        assert plain==parent['passages'][r['source']][r['target_index']]['words']
        if kind=='mono' or selection=='word-deterministic':
            mapping={}
            for a,b in zip(plain,words):
                if a in mapping:assert mapping[a]==b
                mapping[a]=b
            assert Counter(Counter(plain).values())==Counter(Counter(words).values())
        m=r['result']['metrics'];freq=Counter(words);unique=list(freq);n=len(words);pairs=n*(n-1)/2
        assert m['token_lengths']=={str(k):v for k,v in Counter(map(len,plain)).items()}
        assert m['type_lengths']=={str(k):v for k,v in Counter(map(len,unique)).items()}
        assert m['adjacent_pairs']==sum(len(l)-1 for l in lines)
        for pos in m['position'].values():assert sum(x[2] for x in pos['glyph_counts'])==sum(map(len,words))
        assert abs(m['repeat_pair_fraction']-sum(v*(v-1)/2 for v in freq.values())/pairs)<1e-12
        nt=np=0
        for i,a in enumerate(unique):
            for b in unique[i+1:]:
                if abs(len(a)-len(b))<=1 and edit(a,b)==1:nt+=1;np+=freq[a]*freq[b]
        assert abs(m['near_variant_token_pair_fraction']-np/pairs)<1e-12
        assert abs(m['near_variant_type_pair_fraction']-nt/(len(unique)*(len(unique)-1)/2))<1e-12
        groups[r['source'],r['target_index'],r['seed']][r['arm']]=r;cases+=1
    for (source,_,_),arms in groups.items():
        assert len(arms)==4
        assert arms['mono-independent']['payload']==arms['mono-word-deterministic']['payload']
        if source=='german-113':assert all(r['payload']==arms['mono-independent']['payload'] for r in arms.values())
        assert len({json.dumps(r['result']['metrics']['token_lengths'],sort_keys=True) for r in arms.values()})==1
    assert cases==864
    write_json(OUT/'validation.json',{'validated':True,'prepared_sha256':digest(p),'cases':cases,'checks':'Frozen provenance; independent development-only allocation; one-glyph alphabet capacity; inverse decoding; deterministic equality and frequency preservation; mono and German arm identities; all-arm token-length equality; type lengths, adjacency and position totals; full edit-distance near-variants and exact repeat rates.'})
    print('Validated',cases,'records')

if __name__=='__main__':validate()
