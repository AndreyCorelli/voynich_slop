"""Compare unchanged graphs against the preserved pairwise implementation; no SMT."""
from dataclasses import asdict
import importlib.util
import json
from pathlib import Path
import sys
from time import perf_counter

from voynich_smt.data.corpus import digest,write_json
from voynich_smt.experiments.hidden import HiddenRecoveryRequest

OUT=Path('experiments/results/prefix-pruning')
SOURCE=Path('experiments/results/training-diversity/prepared.json')
REFERENCE=OUT/'reference_dictionary.py'


def run():
    source=json.loads(SOURCE.read_text())
    identity={'source_sha256':digest(source),'code_sha256':{str(p):digest(p.read_text()) for p in (Path(__file__),REFERENCE,Path('src/voynich_smt/language/dictionary.py'))}}
    path=OUT/'report.json'
    if path.exists():
        report=json.loads(path.read_text())
        if report['identity']!=identity:raise ValueError('Fixed benchmark inputs or implementation changed')
    else:report={'identity':identity,'cases':[],'complete':False,'semantics':'Single sequential indexed/reference graph construction on each preserved 36-type request. Exact dataclass comparison including order, relations and pruning count. No Z3 fits or new language outcomes.'}
    spec=importlib.util.spec_from_file_location('prefix_pruning_reference',REFERENCE)
    old=importlib.util.module_from_spec(spec);sys.modules[spec.name]=old;spec.loader.exec_module(old)
    for case in (c for c in source['cases'] if c['distinct_training_types']==36):
        if any(c['id']==case['id'] for c in report['cases']):continue
        q=HiddenRecoveryRequest.from_dict(case['request']);maximum=q.max_word_length or max(map(len,q.dictionary.words))
        start=perf_counter();graph=q.dictionary.candidate_graph(q.ciphertext,q.bounds,q.min_word_length,maximum);fast=perf_counter()-start
        print(case['id'],f'indexed={fast:.3f}s; running preserved pairwise reference',flush=True)
        start=perf_counter();previous=old.WordDictionary(q.dictionary.words).candidate_graph(q.ciphertext,q.bounds,q.min_word_length,maximum);slow=perf_counter()-start
        if asdict(graph)!=asdict(previous):raise RuntimeError('Candidate graph changed')
        row={'id':case['id'],'request_sha256':digest(asdict(q)),'graph_sha256':digest(asdict(graph)),
            'indexed_seconds':fast,'reference_seconds':slow,'speedup':slow/fast,'exact_match':True,
            'candidate_counts':list(map(len,graph.candidates)),'relations':len(graph.relations),'pruned_candidates':graph.pruned_candidates}
        report['cases'].append(row);write_json(path,report)
        print(f'Exact match; reference={slow:.3f}s; speedup={slow/fast:.1f}x',flush=True)
    report['complete']=True;write_json(path,report);return report

if __name__=='__main__':run()
