"""Full replay and ceiling diagnostics for the supplied-anchor experiment."""
from concurrent.futures import ProcessPoolExecutor
import hashlib
import json
from pathlib import Path
from collections import Counter
from statistics import mean
from benchmarks import word_mapping_anchor_recovery as b
from voynich_smt.data.corpus import digest,write_json
from voynich_smt.structural_oracle import StructuralOracle


def run():
    old=json.loads((b.OUT/'report.json').read_text())
    saved_catalog=json.loads((b.OUT/'catalog.json').read_text())
    manifest=json.loads((b.OUT/'manifest.json').read_text())
    assert digest(manifest['protocol'])==manifest['sha256']==old['manifest_sha256']
    for path,sha in manifest['protocol']['code_sha256'].items():
        assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==sha
    model,profiles,members,mass,jobs,entries,train_sha=b.foundation()
    assert digest(saved_catalog)==digest(json.loads((b.OUT/'catalog.json').read_text()))==manifest['protocol']['catalog_sha256']
    assert digest(jobs)==manifest['protocol']['jobs_sha256'] and train_sha==manifest['protocol']['training_sha256']
    steps=manifest['protocol']['steps']
    # Repeat every proposal, score and materialized dictionary, not just final metrics.
    with ProcessPoolExecutor(max_workers=4) as pool:
        futures=[pool.submit(b.worker,job,model,profiles,members,mass,steps,b.OUT) for job in jobs]
        rows=[]
        for job,future in zip(jobs,futures):
            rows.append(future.result());print('replayed',job['target'],job['fraction'],job['seed'],flush=True)
    assert [digest(row) for row in rows]==old['run_sha256']
    assert b.evaluate(rows,entries)==old['evaluations']
    all_forms={w for group in members for w in group}
    diagnostics=[]
    for target in b.TARGETS:
        public=json.loads((b.PARENT/f'public/fit-{target}.json').read_text())
        truth=json.loads((b.PARENT/f'truth/fit-{target}.json').read_text())
        oracle=StructuralOracle(entries,truth['decoding'])
        counts=Counter(c for s in public['segments'] for c in s)
        content={c for c,w in truth['decoding'].items() if oracle.kind(w)=='content'}
        total=sum(counts[c] for c in content)
        grouped={}
        for c in content:
            grouped.setdefault(model.emissions(truth['decoding'][c]),[]).append(c)
        capacities={p:len(m) for p,m in zip(profiles,members)}
        reachable=0
        for profile,keys in grouped.items():
            selected=sorted(keys,key=lambda c:(-counts[c],c))[:capacities.get(profile,0)]
            reachable+=sum(counts[c] for c in selected)
        gold_score=model.score(truth['plaintext'])
        relevant=[row for row in rows if row['target']==target and row['fraction']==1]
        diagnostics.append({'target':target,'content_tokens':total,'strict_profile_token_ceiling_ignoring_anchor_capacity':reachable/total,
            'exact_content_candidate_coverage':sum(counts[c] for c in content if truth['decoding'][c] in all_forms)/total,
            'gold_score':gold_score,'fully_anchored_best_scores':[r['best_score'] for r in relevant],
            'fully_anchored_score_gaps':[r['best_score']-gold_score for r in relevant]})
    write_json(b.OUT/'diagnostics.json',{'rows':diagnostics,'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})
    write_json(b.OUT/'validation.json',{'deterministic_replay':True,'report_sha256':digest(old),'runs':len(rows),
        'checks':['frozen protocol and source hashes','catalog and supplied-anchor jobs','every proposed move replayed',
                  'all dictionaries and metrics reproduced','C++ forward score checked against Python','profile capacities and anchors preserved']})
    # A real search-produced 100-word comparison, distinct from constructed oracle examples.
    row=next(r for r in rows if r['target']==8000 and r['fraction']==1 and r['seed']==101)
    truth=json.loads((b.PARENT/'truth/fit-8000.json').read_text())
    public=json.loads((b.PARENT/'public/fit-8000.json').read_text())
    original=[w for s in truth['plaintext'] for w in s][:100]
    cipher=[w for s in public['segments'] for w in s][:100]
    predicted=[row['best_mapping'][c] for c in cipher]
    lines=['# First 100 words: fully anchored structural search','',
        'Correct function-word mappings supplied; content mappings hidden. This is assisted recovery, not a blind crack.',
        '', '## Original','', ' '.join(original),'','## Search output','', ' '.join(predicted),'',
        '| Position | Original | Output | Supplied anchor |','|---:|---|---|:---:|']
    lines += [f'| {i} | {a} | {p} | {"yes" if c in row["supplied_anchors"] else ""} |'
              for i,(a,p,c) in enumerate(zip(original,predicted,cipher),1)]
    (b.OUT/'first-100.md').write_text('\n'.join(lines)+'\n')
    print('Full replay verified; candidate ceilings',diagnostics,flush=True)


if __name__=='__main__':
    run()
