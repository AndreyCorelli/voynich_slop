"""Coherent-analysis controls, boundary ablation, then gated natural transfer."""
from dataclasses import asdict
from pathlib import Path
import hashlib
import json
import time
from collections import Counter

from voynich_smt.data.corpus import write_json,digest
from voynich_smt.coherent_grammar import CoherentGrammar,CoherentLatinAdapter,validate_clause
from voynich_smt.word_mapping.morphology import WhitakerAnnotator

OUT=Path('experiments/results/grammar-restoration/iteration2')
FIXTURES=Path('benchmarks/fixtures/grammar_coherent_v1.json')
ITER1=Path('experiments/results/grammar-restoration/iteration1')


def verify(result,grammar,tokens):
    if result.status=='supported':
        assert result.covered_tokens==len(tokens) and result.boundaries[-1]==len(tokens)
        assert sum(len(c.tokens) for c in result.clauses)==len(tokens)
        assert tuple(w for c in result.clauses for w in c.tokens)==tuple(tokens)
        for clause in result.clauses:validate_clause(clause,grammar.adapter)
        assert result.score==sum(result.components.values())==-len(result.clauses)


def run():
    if OUT.exists():raise ValueError('Preserve prior results; use a new iteration output')
    start=time.monotonic();fixtures=json.loads(FIXTURES.read_text())
    analyzer=WhitakerAnnotator('data/vendor/whitakers-words')
    adapter=CoherentLatinAdapter(analyzer);grammar=CoherentGrammar(adapter)
    manifest={'version':1,'fixtures_sha256':hashlib.sha256(FIXTURES.read_bytes()).hexdigest(),
        'gate':fixtures['gate'],'model':{'max_clause':10,'timeout_ms':250,'boundary_cost':1,
        'reading_aggregation':'one consistent reading per token; satisfiability, no multiplicity reward',
        'role_aggregation':'one attachment per token; one root, acyclic connected tree',
        'intransitive_forms':sorted(adapter.INTRANSITIVE),'government':adapter.GOVERNMENT},
        'resource':analyzer.resource,'scope':fixtures['scope'],
        'code_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),Path('src/voynich_smt/coherent_grammar.py')]}}
    write_json(OUT/'manifest.json',manifest)
    rows=[]
    for split in ['development','confirmation']:
        for pair in [r for r in fixtures['pairs'] if r['split']==split]:
            records={}
            for mode in ['supplied','latent']:
                for version in ['reference','corrupted']:
                    tokens=pair[version].split()
                    result=grammar.score(tokens,supplied_boundaries=[len(tokens)] if mode=='supplied' else None)
                    verify(result,grammar,tokens);records[f'{mode}_{version}']=asdict(result)
            rows.append({**pair,'results':records})
        selected=[r for r in rows if r['split']==split]
        print(split,[(mode,sum(r['results'][f'{mode}_reference']['status']=='supported' and
            r['results'][f'{mode}_corrupted']['status']=='no_parse' for r in selected)) for mode in ['supplied','latent']],flush=True)
    controls=[]
    for control in fixtures['controls']:
        tokens=control['tokens'].split();results={}
        for mode in ['supplied','latent']:
            result=grammar.score(tokens,supplied_boundaries=[len(tokens)] if mode=='supplied' else None)
            verify(result,grammar,tokens);results[mode]=asdict(result)
        controls.append({**control,'results':results})
    streams=[]
    for example in fixtures['streams']:
        records={}
        for mode in ['supplied','latent']:
            for version in ['reference','corrupted']:
                tokens=example[version].split();result=grammar.score(tokens,
                    supplied_boundaries=example['boundaries'] if mode=='supplied' else None)
                verify(result,grammar,tokens);records[f'{mode}_{version}']=asdict(result)
        streams.append({**example,'results':records})
    summary=[]
    for split in ['development','confirmation']:
        for mode in ['supplied','latent']:
            group=[r for r in rows if r['split']==split];valid=[r for r in controls if r['split']==split]
            multi=[r for r in streams if r['split']==split]
            summary.append({'split':split,'mode':mode,'pairs':len(group),
                'references_supported':sum(r['results'][f'{mode}_reference']['status']=='supported' for r in group),
                'corruptions_no_parse':sum(r['results'][f'{mode}_corrupted']['status']=='no_parse' for r in group),
                'valid_controls':len(valid),'valid_controls_supported':sum(r['results'][mode]['status']=='supported' for r in valid),
                'multi_clause_pairs':len(multi),'multi_clause_correct':sum(r['results'][f'{mode}_reference']['status']=='supported'
                    and r['results'][f'{mode}_corrupted']['status']=='no_parse' for r in multi)})
    gate=all(r['pairs']==8 and r['references_supported']==8 and r['corruptions_no_parse']==8
        and r['valid_controls_supported']==r['valid_controls'] and r['multi_clause_correct']==r['multi_clause_pairs'] for r in summary)
    for filename,value in [('pairs.json',rows),('controls.json',controls),('streams.json',streams)]:write_json(OUT/filename,value)
    natural=[];historical=[]
    if gate:
        print('Controlled gate passed; running unchanged natural transfer diagnostics.',flush=True)
        for passage in json.loads((ITER1/'passages.json').read_text()):
            tokens=passage['tokens'];boundaries=sorted(set(passage['reference_boundaries_eval_only']+[len(tokens)]))
            records={}
            for mode in ['supplied','latent']:
                result=grammar.score(tokens,supplied_boundaries=boundaries if mode=='supplied' else None)
                verify(result,grammar,tokens);records[mode]=asdict(result)
            natural.append({'id':passage['id'],'author':passage['author'],'tokens':tokens,'results':records})
            print('natural',passage['id'],records['latent']['status'],flush=True)
        for move in json.loads((ITER1/'first-corruptions.json').read_text()):
            crops=[]
            for crop in move['crops']:
                records={}
                for version in ['before','after']:
                    tokens=crop[f'{version}_tokens'];result=grammar.score(tokens);verify(result,grammar,tokens)
                    records[version]=asdict(result)
                crops.append({'start':crop['start'],'end':crop['end'],'results':records})
            historical.append({'target':move['target'],'seed':move['seed'],'changes':move['changes'],'crops':crops})
        write_json(OUT/'natural-transfer.json',natural);write_json(OUT/'historical-transfer.json',historical)
    # Freeze exactly the dictionary analyses and lexical tables used for replay.
    used={w for r in fixtures['pairs']+fixtures['streams'] for key in ['reference','corrupted'] for w in r[key].split()}
    used|={w for r in fixtures['controls'] for w in r['tokens'].split()}
    used|={w for p in natural for w in p['tokens']}
    if gate:used|={w for r in json.loads((ITER1/'first-corruptions.json').read_text()) for c in r['crops'] for key in ['before_tokens','after_tokens'] for w in c[key]}
    write_json(OUT/'morphology-lattice.json',{w:[asdict(r) for r in adapter.analyze(w)] for w in sorted(used)})
    report={'manifest_sha256':digest(manifest),'controlled_gate_pass':gate,'summary':summary,
        'natural_passages':len(natural),'natural_statuses':{mode:dict(Counter(r['results'][mode]['status'] for r in natural)) for mode in ['supplied','latent']},
        'historical_moves':len(historical),'historical_intact_fully_supported':sum(all(c['results']['before']['status']=='supported' for c in r['crops']) for r in historical),
        'elapsed_seconds':time.monotonic()-start,'clause_cache':str(grammar.clause.cache_info()),
        'decision':'controlled subset works; expand grammar and coverage before dictionary search' if gate else 'controlled gate failed; inspect without natural transfer',
        'annotation_failures':analyzer.annotation_failures}
    write_json(OUT/'report.json',report);print(json.dumps(report,indent=2),flush=True)


if __name__=='__main__':run()
