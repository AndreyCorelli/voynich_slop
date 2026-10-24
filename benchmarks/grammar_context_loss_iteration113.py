"""Source-only literal suffix evidence deletion, frozen repair policies."""
from benchmarks.grammar_jerome_context_iteration112 import *
from voynich_smt.context_evidence_loss import remove_suffix_type
from voynich_smt.combined_repair_gate import select as gate
OUT=ROOT/'iteration113'


def run():
    assert not OUT.exists();OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),Path('src/voynich_smt/context_evidence_loss.py'),ROOT/'iteration98/blocks.json',ROOT/'iteration44/annotations-truth.json',ROOT/'iteration102/full/weights.npz',ROOT/'iteration102/calibration-cases.json',ROOT/'iteration110/cases.json',ROOT/'iteration109/policies.json',ROOT/'iteration111/policies.json',ROOT/'iteration93/types.json',ROOT/'iteration93/models.json',ROOT/'iteration85/anchor-budgets.json',ROOT/'iteration98/calibration-bank.json']
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='SOURCE-ONLY diagnostic, no author/PP/new labels/reserve/sealed test. Source98 full829 fixed ordered sentences; first100 protected word-for-word. For EACH16 catalogue types, remove ALL occurrences ONLY in suffix729 before global perturbation; preserve sentence slots even empty. Token deletion changes neighbor adjacency, counts, count eligibility and profiles: synthetic evidence-loss test, not natural text or isolated count effect. Same829 nominal volume route; report retainedtokens/empty slots, do not treat sentence slots as independent evidence. Fixed102full shared256bootstrapweights, same93model/195suppliedanchors/16catalogue/5occ3sent support, frozen109 and111 FULL rules; no recalibration. ALL64errors+3controls for each16removals, complete102baseline and matched110catalogue-onlyomissions, no truth-driven deletion choice. Attach original full-reference pair AFTER scoring even if an endpoint entirely absent, support from actual remaining pairs. Report allerrors/supported/unsupported/literallyabsenttrueendpoint and controls, wrongactions, changedactions vs matched catalogue omission. No new repair integration/default claim.'))
    ids=load(ROOT/'iteration98/blocks.json')['scored']['full'];data=load(ROOT/'iteration44/annotations-truth.json');anchors=load(ROOT/'iteration85/anchor-budgets.json')['195'];base=ag.public_sentences([dict(sent_id=i,**data[i]) for i in ids],anchors,'cal98-full');assert len(base)==829
    words=load(ROOT/'iteration93/types.json')['candidates'];lookup={t['anchor']:t['id'] for s in base for t in s['tokens'] if t['anchor'] in words};policies={a:load(ROOT/('iteration'+a)/'policies.json')['full'] for a in ['109','111']};bank=load(ROOT/'iteration98/calibration-bank.json');model=load(ROOT/'iteration93/models.json')['context'];weights=np.load(ROOT/'iteration102/full/weights.npz')['weights'];baseline={c['case']:c for c in load(ROOT/'iteration102/calibration-cases.json') if c['block']=='full'}
    views={w:remove_suffix_type(base,lookup[w]) for w in words};meta={}
    for w,p in views.items():
        assert p[:100]==base[:100];n=sum(t['id']==lookup[w] for s in p for t in s['tokens']);ns=sum(any(t['id']==lookup[w] for t in s['tokens']) for s in p)
        meta[w]=dict(remaining_occurrences=n,remaining_sentences=ns,deleted_tokens=sum(len(s['tokens'])-len(t['tokens']) for s,t in zip(base,p)),retained_tokens=sum(len(s['tokens']) for s in p),empty_sentence_slots=sum(not s['tokens'] for s in p))
        save(OUT/('public-'+w+'.json'),p)
    save(OUT/'preflight.json',meta);save(OUT/'policies.json',policies);save(OUT/'context-freeze.json',dict(inputs={str(p):digest(p) for p in [OUT/'preflight.json',OUT/'policies.json']+list(OUT.glob('public-*.json'))}))
    cases=[]
    for w,public in views.items():
        folder=OUT/w;folder.mkdir()
        for case,replacements in bank.items():
            row=compute(public,case,replacements,anchors,words,model,weights,folder)
            ref=dict(row['reference'],pair=baseline[case]['reference']['pair']);row.update(reference=ref,removed_word=w,regime='literal_loss',actions={a:gate(row['features'],p) for a,p in policies.items()},true_endpoint_absent=bool(ref['error'] and lookup[w] in ref['pair'] and meta[w]['remaining_occurrences']==0));cases.append(row)
        print('FINISHED',w,flush=True)
    save(OUT/'cases.json',cases);save(OUT/'predictions-freeze.json',dict(inputs={str(p):digest(p) for p in [OUT/'cases.json',OUT/'policies.json']+list(OUT.glob('*/*.json'))+list(OUT.glob('*/*.npz'))}))
    print('DONE',len(cases),flush=True)
if __name__=='__main__':run()
