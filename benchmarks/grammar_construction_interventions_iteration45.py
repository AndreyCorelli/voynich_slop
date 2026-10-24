"""Oracle PP lattice intervention matrix on reused source, no objective ranking."""
from pathlib import Path
from collections import defaultdict,Counter
import math
import numpy as np
from benchmarks.grammar_source_support_iteration44 import OUT as PREVIOUS,ROOT,RESERVE,load,save,digest
from benchmarks.grammar_pp_contrast_iteration40 import constructions
from voynich_smt.construction_interventions import morphology,domains,lattice,FIELDS,value,interventions,summarize
OUT=ROOT/'iteration45'


def run():
    assert not OUT.exists()
    for p,h in load(PREVIOUS/'verification-manifest.json')['inputs'].items():assert digest(p)==h,p
    data=load(PREVIOUS/'annotations-truth.json');rows=load(PREVIOUS/'records-truth.json');reserved={r['sent_id'] for group in load(RESERVE)['authors'].values() for r in group};assert not set(data)&reserved;lexicon=morphology(s['tokens'] for s in data.values());examples=[];wide=[]
    OUT.mkdir();paths=[Path(__file__),Path('src/voynich_smt/construction_interventions.py'),Path('src/voynich_smt/pp_contrast.py'),PREVIOUS/'verification-manifest.json',PREVIOUS/'annotations-truth.json',PREVIOUS/'records-truth.json',RESERVE]
    save(OUT/'manifest.json',dict(inputs={str(p):digest(p) for p in paths},scope='Reuse879 source in constructions from iteration44, Cicero/Palladius. No old target-query or reserved scoring. Oracle POS, anchor, morphology dictionary built from all4070 source sentences (including analyzed sentences), correct candidate domains and supplied boundaries. Upper-bound constraint diagnostic, not deployable decoding.',
        fields=dict(boundary='PP left/right endpoints',head='nominal head attached to in',case='head Acc/Abl',predicate='first verbal ancestor token, or None for no verbal ancestor'),
        candidate_generation='Nominal heads within8 tokens; all anchor-containing intervals length2..8; all verbal tokens plus None. Add missing reference head/boundary/predicate values to their DOMAIN, never a flagged correct candidate. Cartesian combinations with head inside and predicate outside span. Primary has no score/pruning by probability.',
        compatibility='Span includes only nominal/adjectival/DET/NUM tokens besides anchor. Existential word-type morphology witness: head case, ADJ/DET case-number-gender agreement; other nominals may share head case or be Gen. Missing features wildcard. No gold dependency edges used for filtering.',
        morphology_arms='oracle_word_type readings: all observed Case/Number/Gender tuples per normalized word/POS; hidden_case masks Case only and retains same Number/Gender dictionary. Dictionary is privileged, includes evaluation occurrences. No claimed morphology induction.',
        limitations='Four-field PP schema, not complete parse. Predicate constrained ONLY outside span, with no semantic/valency/governor evidence; fact usefulness is conditional on this rule set. Boundary/head constraints couple geometry; hidden case is symmetric by construction. Revealed fact domain sizes differ. All-four revelation is tautological.',
        intervention='All16 subsets; report remaining sets, reference survival/unique/false unique, and correct uniquely fixed UNREVEALED fields. Separate baseline-ambiguous cohort; incremental propagation excludes field revealed and fields already resolved. Empty sets are failures, not recovery.',
        sensitivity='Predeclared wider16-token domains for all same examples; unchanged compatibility, morphology and oracle inclusion. One wrong fact per available field per example/arm, uniform from raw geometry-domain alternative values, seed45001. Nonempty wrong-fact results quantify consistency insufficiency, not validated alternative parses.'))
    for row in rows:
        tokens=data[row['sent_id']]['tokens'];c=constructions(tokens)[row['construction']];reference=[c['left'],c['right'],c['head'],c['case'],row['oracle_index']];ref=dict(c,predicate=row['oracle_index']);domain=domains(tokens,c['prep'],ref);large=domains(tokens,c['prep'],ref,16,16)
        example=dict(sent_id=row['sent_id'],author=row['author'],construction=row['construction'],prep=c['prep'],reference=reference,domains=domain,arms={})
        for arm,mask in (('oracle_word_type',False),('hidden_case',True)):
            candidates,stages=lattice(tokens,c['prep'],domain,lexicon,mask);example['arms'][arm]=dict(candidates=candidates,stages=stages)
            wc,ws=lattice(tokens,c['prep'],large,lexicon,mask);wide.append(dict(sent_id=row['sent_id'],construction=row['construction'],author=row['author'],arm=arm,domains=large,stages=ws,summaries={'none' if not fields else '+'.join(fields):summarize(wc,reference,fields) for fields in interventions()}))
        examples.append(example)
    save(OUT/'morphology-oracle.json',lexicon);save(OUT/'lattices.json',examples);save(OUT/'wide-lattices.json',wide);save(OUT/'evaluation-freeze.json',dict(inputs={str(p):digest(p) for p in OUT.glob('*.json')}));evaluate()


def evaluate():
    examples=load(OUT/'lattices.json');records=[];probes=[];rng=np.random.default_rng(45001)
    for e in examples:
        ref=e['reference']
        for arm,a in e['arms'].items():
            candidates=a['candidates'];baseline=summarize(candidates,ref)
            for fields in interventions():records.append(dict(sent_id=e['sent_id'],author=e['author'],construction=e['construction'],arm=arm,intervention='none' if not fields else '+'.join(fields),baseline=baseline,summary=summarize(candidates,ref,fields)))
            raw=dict(boundary=[tuple(x) for x in e['domains']['boundaries']],head=e['domains']['heads'],case=['Acc','Abl'],predicate=e['domains']['predicates'])
            for field,values in raw.items():
                alternatives=[v for v in values if v!=value(ref,field)]
                if not alternatives:continue
                wrong=alternatives[int(rng.integers(len(alternatives)))];survivors=[c for c in candidates if value(c,field)==wrong];probes.append(dict(sent_id=e['sent_id'],construction=e['construction'],author=e['author'],arm=arm,field=field,wrong_value=wrong,baseline_reference_retained=baseline['reference_retained'],remaining=len(survivors),unique_wrong=len(survivors)==1))
    save(OUT/'interventions.json',records);save(OUT/'wrong-fact-probes.json',probes);results={}
    for arm in ('oracle_word_type','hidden_case'):
        for author in ('pooled','Cicero','Palladius'):
            for cohort in ('all','reference_survives','baseline_ambiguous'):
                for fields in interventions():
                    key='none' if not fields else '+'.join(fields);selected=[r for r in records if r['arm']==arm and (author=='pooled' or r['author']==author) and r['intervention']==key and (cohort=='all' or (r['baseline']['reference_retained'] and (cohort!='baseline_ambiguous' or r['baseline']['remaining']>1)))]
                    if not selected:continue
                    n=len(selected);newly={f:sum(r['summary']['unrevealed_resolved'].get(f,False) and not r['baseline']['unrevealed_resolved'][f] for r in selected) for f in FIELDS if f not in fields}
                    results[f'{arm}/{author}/{cohort}/{key}']=dict(n=n,nonempty=sum(r['summary']['remaining']>0 for r in selected),reference_retained=sum(r['summary']['reference_retained'] for r in selected),uniquely_correct=sum(r['summary']['uniquely_correct'] for r in selected),false_unique=sum(r['summary']['false_unique'] for r in selected),median_candidates=float(np.median([r['summary']['remaining'] for r in selected])),mean_candidates=float(np.mean([r['summary']['remaining'] for r in selected])),unrevealed_newly_resolved=newly)
    wrong={}
    for arm in ('oracle_word_type','hidden_case'):
        for field in FIELDS:
            selected=[r for r in probes if r['arm']==arm and r['field']==field and r['baseline_reference_retained']];wrong[f'{arm}/{field}']=dict(n=len(selected),nonempty=sum(r['remaining']>0 for r in selected),unique_wrong=sum(r['unique_wrong'] for r in selected))
    stages={}
    for arm in ('oracle_word_type','hidden_case'):
        selected=[e['arms'][arm]['stages'] for e in examples];stages[arm]={k:sum(r[k] for r in selected) for k in selected[0]}
    audit=dict(examples=len(examples),oracle_domain_additions={k:sum(e['domains']['oracle_additions'][k] for e in examples) for k in ('head','boundary','predicate')},stages=stages)
    save(OUT/'evaluation.json',dict(matrix=results,wrong_facts=wrong,audit=audit));print(audit)
    for k,v in results.items():
        if '/pooled/baseline_ambiguous/' in k and (k.endswith('/none') or k.split('/')[-1] in FIELDS):print(k,v)
    print('Wrong',wrong)
if __name__=='__main__':run()
