"""Frozen standalone, punctuation-free Latin grammar diagnostic; no dictionary search."""
from collections import Counter
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import random
import time
from statistics import mean

from benchmarks.scalable_latin_caesar import sentences,TREEBANKS
from benchmarks.word_mapping_first_corruption import PARENT,ORACLE
from voynich_smt.data.corpus import write_json,digest
from voynich_smt.grammar_diagnostic import LatinAdapter,BoundaryModel,GrammarScorer
from voynich_smt.word_mapping.morphology import WhitakerAnnotator

OUT=Path('experiments/results/grammar-restoration/iteration1')
SEED=20261020
GATE={'first_corruptions':8,'dev_incompatible_rate':.70,'heldout_incompatible_rate':.65,
      'heldout_cluster_lower_bound':.50}


def signatures(readings):
    return set(readings)


def interval(rows,rng):
    groups={}
    for r in rows:groups.setdefault(r['passage'],[]).append(r['delta']< -1e-9)
    if not groups:return [None,None]
    keys=sorted(groups);draws=[]
    for _ in range(1000):
        sample=[v for key in rng.choices(keys,k=len(keys)) for v in groups[key]]
        draws.append(mean(sample))
    draws.sort();return [draws[24],draws[974]]


def run():
    if OUT.exists():raise ValueError('Preserve existing output; choose a new iteration directory')
    start=time.monotonic();rng=random.Random(SEED)
    source_path=TREEBANKS/'proiel-r2.17/la_proiel-ud-train.conllu'
    perseus=TREEBANKS/'perseus-r2.17/la_perseus-ud-train.conllu'
    groups={};counts=Counter();lengths=[]
    for corpus,path in [('proiel',source_path),('perseus',perseus)]:
        for work,author,tokens in sentences(path,corpus):
            words=[w for w,_ in tokens]
            if corpus=='proiel' and author in {'Jerome','Palladius'}:
                counts.update(words);lengths.append(len(words))
            if (corpus=='proiel' and author=='Cicero') or (corpus=='perseus' and author in {'Sallust','Suetonius'}):
                groups.setdefault(author,[]).append((work,words))
    annotator=WhitakerAnnotator('data/vendor/whitakers-words')
    adapter=LatinAdapter(annotator)
    boundary=BoundaryModel(mean(lengths))
    scorer=GrammarScorer(adapter,boundary)
    pool=[w for w,_ in counts.most_common(2000) if adapter.analyze(w)]
    manifest={'seed':SEED,'gate':GATE,'authors':{'development':['Cicero'],'confirmation':['Sallust','Suetonius']},
        'source_boundary_training_authors':['Jerome','Palladius'],'source_tokens':sum(counts.values()),
        'source_sentences':len(lengths),'mean_boundary_length':boundary.mean_length,
        'max_segment':24,'min_segment':4,'radius':8,'passages_per_author':6,'tokens_per_passage':64,
        'candidate_pool':'first 2000 source forms by frequency with dictionary analyses; fixed before target scoring',
        'normalization':'lowercase, strip diacritics, j->i, v->u; remove punctuation',
        'morphology_resource':annotator.resource,'source_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [source_path,perseus]},
        'code_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),Path('src/voynich_smt/grammar_diagnostic.py')]},
        'scope':'standalone local morphology relaxation; no search, no target annotations/segmentation passed to scorer; prior-explored corpus excerpts'}
    write_json(OUT/'manifest.json',manifest)
    write_json(OUT/'source-candidate-pool.json',pool)
    rows=[];passages=[]
    for author in ['Cicero','Sallust','Suetonius']:
        flat=[];gold_boundaries=[];works=[]
        for work,words in groups[author]:
            flat.extend(words);gold_boundaries.append(len(flat));works.append(work)
        for pi in range(6):
            offset=64*pi;tokens=tuple(flat[offset:offset+64]);assert len(tokens)==64
            reference=scorer.score(tokens);unsegmented=scorer.score(tokens,latent=False)
            bounds=[b-offset for b in gold_boundaries if offset<b<offset+64]
            inferred=set(reference.boundaries[:-1]);gold=set(bounds)
            pid=f'{author}/{pi}'
            passages.append({'id':pid,'author':author,'tokens':tokens,'reference':asdict(reference),
                'unsegmented_reference':asdict(unsegmented),'reference_boundaries_eval_only':bounds,
                'boundary_tp':len(gold&inferred),'boundary_predicted':len(inferred),'boundary_gold':len(gold),
                'source_work_ids':sorted(set(works))})
            eligible=[w for w in dict.fromkeys(tokens) if adapter.analyze(w)]
            for kind in ['incompatible','same_pos_disjoint','compatible','random']:
                for rep in range(2):
                    mapping={};requested=1+rep
                    shuffled=list(eligible);rng.shuffle(shuffled)
                    for old in shuffled:
                        oldr=adapter.analyze(old);oldpos={r.pos for r in oldr}
                        options=[]
                        for new in pool:
                            if new in tokens or new in mapping.values():continue
                            newr=adapter.analyze(new);newpos={r.pos for r in newr}
                            if kind=='incompatible' and oldpos&newpos:continue
                            if kind=='same_pos_disjoint' and (not oldpos&newpos or signatures(oldr)&signatures(newr)):continue
                            if kind=='compatible' and not signatures(oldr)&signatures(newr):continue
                            options.append(new)
                        if options:
                            mapping[old]=rng.choice(options)
                        if len(mapping)==requested:break
                    if len(mapping)!=requested:continue
                    changed=tuple(mapping.get(w,w) for w in tokens)
                    scored=scorer.score(changed);fixed=scorer.score(changed,latent=False)
                    rows.append({'author':author,'passage':pid,'stratum':kind,'mapping':mapping,
                        'changed_types':len(mapping),'changed_tokens':sum(w in mapping for w in tokens),
                        'changes':[{'old':a,'new':b,'old_source_count':counts[a],'new_source_count':counts[b],
                            'old_passage_count':tokens.count(a),'old_analyses':len(adapter.analyze(a)),
                            'new_analyses':len(adapter.analyze(b)),
                            'old_pos':sorted({x.pos for x in adapter.analyze(a)}),
                            'new_pos':sorted({x.pos for x in adapter.analyze(b)})} for a,b in mapping.items()],
                        'delta':scored.total-reference.total,'unsegmented_delta':fixed.total-unsegmented.total,
                        'component_delta':{k:scored.components[k]-reference.components[k] for k in scored.components},
                        'reference':asdict(reference),'corrupted':asdict(scored)})
            print(author,pi,'known',reference.known_tokens,'/',reference.tokens,flush=True)
    audited=[]
    forms=json.loads((PARENT/'candidates-oracle.json').read_text())['forms']
    for target in [500,2000,8000,16000,32000]:
        truth=json.loads((PARENT/f'truth/fit-{target}.json').read_text())
        public=json.loads((PARENT/f'public/fit-{target}.json').read_text())
        cipher=[w for s in public['segments'] for w in s];plain=[w for s in truth['plaintext'] for w in s]
        for seed in [101,202]:
            saved=json.loads((ORACLE/f'runs/{target}/greedy/seed-{seed}/report.json').read_text())
            changes=saved['first_departure']['changes'];positions=[i for i,w in enumerate(cipher) if w in changes]
            crops=[]
            for pos in positions:
                lo=max(0,min(pos-32,len(plain)-64));hi=min(len(plain),lo+64)
                if (lo,hi) in [(x['start'],x['end']) for x in crops]:continue
                before=plain[lo:hi];after=[forms[changes[c]] if c in changes else w for c,w in zip(cipher[lo:hi],before)]
                old,new=scorer.score(before),scorer.score(after)
                crops.append({'start':lo,'end':hi,'before_tokens':before,'after_tokens':after,
                    'reference':asdict(old),'corrupted':asdict(new),'delta':new.total-old.total})
            audited.append({'target':target,'seed':seed,'changes':[{'old':truth['decoding'][c],'new':forms[f]} for c,f in changes.items()],
                'delta':sum(x['delta'] for x in crops),'crops':crops})
    summary=[]
    for author in ['Cicero','Sallust','Suetonius']:
        for kind in ['incompatible','same_pos_disjoint','compatible','random']:
            selected=[r for r in rows if r['author']==author and r['stratum']==kind]
            summary.append({'author':author,'stratum':kind,'n':len(selected),
                'intact_preferred':sum(r['delta']< -1e-9 for r in selected),
                'ties':sum(abs(r['delta'])<=1e-9 for r in selected),
                'corruption_preferred':sum(r['delta']>1e-9 for r in selected),
                'rate':mean(r['delta']< -1e-9 for r in selected),
                'passage_cluster_95_interval':interval(selected,rng),
                'mean_delta':mean(r['delta'] for r in selected)})
    audit_hits=sum(r['delta']< -1e-9 for r in audited)
    decisive={r['author']:r for r in summary if r['stratum']=='incompatible'}
    development_pass=audit_hits>=GATE['first_corruptions'] and decisive['Cicero']['rate']>=GATE['dev_incompatible_rate']
    confirmation_pass=all(decisive[a]['rate']>=GATE['heldout_incompatible_rate'] and
        decisive[a]['passage_cluster_95_interval'][0]>GATE['heldout_cluster_lower_bound'] for a in ['Sallust','Suetonius'])
    # Save all readings used, enabling replay without reference annotations or mutable dictionary access.
    used=set(pool)|{w for p in passages for w in p['tokens']}|{w for a in audited for c in a['crops'] for key in ['before_tokens','after_tokens'] for w in c[key]}
    write_json(OUT/'morphology-lattice.json',{w:[asdict(a) for a in adapter.analyze(w)] for w in sorted(used)})
    write_json(OUT/'passages.json',passages);write_json(OUT/'mutations.json',rows);write_json(OUT/'first-corruptions.json',audited)
    report={'manifest_sha256':digest(manifest),'summary':summary,'first_corruptions_preferred':audit_hits,
        'development_pass':development_pass,'confirmation_pass':confirmation_pass,
        'gate_pass':development_pass and confirmation_pass,'decision':'revise before dictionary search' if not (development_pass and confirmation_pass) else 'standalone gate passed; plan stability tests separately',
        'elapsed_seconds':time.monotonic()-start,'morphology_annotation_failures':annotator.annotation_failures,
        'known_token_rate':sum(p['reference']['known_tokens'] for p in passages)/(18*64),
        'boundary_counts':{k:sum(p[k] for p in passages) for k in ['boundary_tp','boundary_predicted','boundary_gold']}}
    write_json(OUT/'report.json',report)
    print(json.dumps(report,indent=2),flush=True)


if __name__=='__main__':run()
