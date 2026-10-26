"""Independent joint survival/equivalence and scalar profile/control replay."""
from pathlib import Path
from itertools import combinations
import json,random,hashlib,math
from benchmarks.grammar_pos_cores_iteration236_review import measure
P=Path('experiments/results/grammar-restoration');O=P/'iteration238'
def read(p):return json.loads(p.read_text())
def near(a,b):
    if a is None:assert b is None
    else:assert math.isclose(a,b,abs_tol=1e-10,rel_tol=1e-10)
def run():
    old=read(P/'iteration236/cores.json');parts=read(P/'iteration237/partitions.json');base=read(P/'iteration234-retry/clusters.json');cores=read(O/'cores.json');excluded=read(O/'exclusions.json');ff=read(P/'iteration231/features.json');truth=read(P/'iteration231/truth.json');strata=read(P/'iteration234-retry/strata.json');coverage=read(P/'iteration231/summary.json');dd=read(O/'details.json');ss=read(O/'summary.json');previous=read(P/'iteration236/summary.json');checks=groups=0
    for a,cc in cores.items():
        maps=[dict(zip(p['words'],p['labels'])) if p['clusterable'] else {} for p in parts[a]];words=base[a]['words'];orig={w:i for i,c in enumerate(old[a]) for w in c['words']};new={w:i for i,c in enumerate(cc) for w in c['words']};surviving={w for w in words if all(w in m for m in maps)};assert set(new)==surviving;reasons={r['word']:r for r in excluded[a]};assert set(reasons)==set(words)-surviving
        for w,r in reasons.items():assert r['index']==words.index(w) and r['missing_seeds']==[p['seed'] for p,m in zip(parts[a],maps) if w not in m]
        for u,v in combinations(words,2):
            same=u in new and v in new and new[u]==new[v];expected=u in surviving and v in surviving and orig[u]==orig[v] and all(m[u]==m[v] for m in maps);assert same==expected;checks+=1
        for c in cc:assert c['words']==[words[i] for i in c['indices']] and c['size']==len(c['indices']) and c['pairs']==[list(p) for p in combinations(c['indices'],2)]
        lookup={r['word']:i for i,r in enumerate(ff[a])};y=[truth[a]['profiles'][lookup[w]] for w in words];freq=[truth[a]['frequencies'][lookup[w]] for w in words];non=[c for c in cc if c['size']>1];actual=measure(y,non)
        for k,v in actual.items():near(v,dd[a]['actual'][k]);near(v,ss[a]['actual'][k])
        assert len(non)==len(dd[a]['individual_cores'])
        for c,r in zip(non,dd[a]['individual_cores']):
            assert r['words']==c['words'] and r['indices']==c['indices'] and r['size']==c['size']
            for k,v in measure(y,[c]).items():near(v,r['metrics'][k])
        for j,seed in enumerate(range(23300,23499)):
            rng=random.Random(seed);perm=list(range(len(words)))
            for bucket in strata[a]:
                ix=bucket['indices'];source=ix.copy();rng.shuffle(source)
                for i,v in zip(ix,source):perm[i]=v
            result=measure([y[i] for i in perm],non)
            for k,v in result.items():near(v,dd[a]['null'][j][k])
            groups+=1
        selected=[i for c in non for i in c['indices']];s=ss[a];assert s['original']==previous[a] and s['surviving_all_runs']==len(surviving) and s['excluded_nodes']==len(reasons) and s['all_joint_cores']==len(cc);assert s['nonsingleton_cores']==len(non) and s['singletons']==sum(c['size']==1 for c in cc) and s['sizes']==[c['size'] for c in non] and s['pairs']==sum(len(c['pairs']) for c in non) and s['covered_nodes']==len(selected) and s['graph_nodes']==len(words);tokens=sum(freq[i] for i in selected);assert s['covered_tokens']==tokens;near(s['graph_node_coverage'],len(selected)/len(words));near(s['text_token_coverage'],tokens/coverage[a]['coverage']['text_tokens']);near(s['text_type_coverage'],len(selected)/coverage[a]['coverage']['text_word_types'])
        for k,v in actual.items():
            if v is None:assert s['null'][k] is None
            else:
                nn=[r[k] for r in dd[a]['null']];near(sum(nn)/199,s['null'][k]['mean']);near(max(nn),s['null'][k]['maximum']);near((1+sum(z>=v-1e-12 for z in nn))/200,s['null'][k]['upper_tail'])
    hashes=0
    for manifest in [read(O/'design-freeze.json'),read(P/'iteration237/verification-manifest.json')]:
        for p,h in manifest.items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h;hashes+=1
    for p,h in read(O/'core-freeze.json').items():assert hashlib.sha256((O/p).read_bytes()).hexdigest()==h;hashes+=1
    result=dict(status='passed',joint_equivalence_pair_checks=checks,profile_null_groups=groups,hashes=hashes);(O/'independent-review.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
if __name__=='__main__':run()
