"""Oracle diagnostic: restore one corrupted entry and measure structural repair."""
from collections import defaultdict
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
from statistics import mean

from benchmarks.grammar_structure_iteration3 import OUT,metrics,aggregate
from benchmarks.grammar_structure_iteration3_validate import FrozenAdapter
from voynich_smt.data.corpus import write_json
from voynich_smt.predicate_structure import StructureModel,Logistic


def run():
    load=lambda n:json.loads((OUT/n).read_text())
    saved=load('model.json');model=StructureModel(FrozenAdapter(load('morphology-lattice.json')),
        Logistic(**saved['finite']),Logistic(**saved['parent']),saved['threshold'])
    public={r['id']:r for r in load('public.json')};truth={r['id']:r for r in load('evaluation-only-truth.json')}
    rows=[]
    for r in load('corruption.json'):
        if r['rate'] not in [.25,.50]:continue
        original=public[r['id']]['tokens'];gold=truth[r['id']];mapping=r['mapping']
        # Prefer the first corrupted dictionary entry covering a reference finite
        # predicate. This selection is explicitly oracle evaluation, never search.
        words=sorted({original[i] for i in gold['finite']} & set(mapping))
        if not words:words=sorted(mapping)
        if not words:continue
        repaired_word=words[0];remaining={w:v for w,v in mapping.items() if w!=repaired_word}
        tokens=[remaining.get(w,w) for w in original]
        prediction=model.infer(tokens);after=metrics(prediction,gold);before=r['metrics']
        rows.append({'id':r['id'],'author':r['author'],'seed':r['seed'],'rate':r['rate'],
            'oracle_restored_entry':repaired_word,'removed_false_entry':mapping[repaired_word],
            'token_positions_restored':[i for i,w in enumerate(original) if w==repaired_word],
            'mapping_after':remaining,'prediction':prediction,'before':before,'after':after,
            'finite_f1_delta':after['predicates']['f1']-before['predicates']['f1'],
            'correct_anchor_delta':after['token_anchor_correct']-before['token_anchor_correct']})
    summary=[]
    for author in ['Cicero','Sallust','Suetonius']:
        chosen=[r for r in rows if r['author']==author]
        summary.append({'author':author,'runs':len(chosen),'finite_f1_increased':sum(r['finite_f1_delta']>1e-9 for r in chosen),
            'finite_f1_equal':sum(abs(r['finite_f1_delta'])<=1e-9 for r in chosen),'finite_f1_decreased':sum(r['finite_f1_delta']< -1e-9 for r in chosen),
            'mean_finite_f1_delta':mean(r['finite_f1_delta'] for r in chosen),
            'mean_correct_anchor_delta':mean(r['correct_anchor_delta'] for r in chosen)})
    write_json(OUT/'oracle-repairs.json',{'scope':'Oracle single-entry repairs of synthetic damage, selected using original finite labels; not an optimizer or lexical recovery result',
        'rows':rows,'summary':summary,'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})
    print(json.dumps(summary,indent=2))


if __name__=='__main__':run()
