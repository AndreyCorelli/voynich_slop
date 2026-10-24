"""Fresh source support audit excluding every previously declared ID and target author."""
from pathlib import Path
from collections import Counter,defaultdict
import hashlib
import sys
import numpy as np
from benchmarks.grammar_occurrence_case_iteration43 import OUT as PREVIOUS,ROOT,RESERVE,load,save,digest,metrics
from benchmarks.grammar_latent_classes_iteration26 import strings
from benchmarks.scalable_latin_caesar import PROIEL,words
from benchmarks.grammar_pp_contrast_iteration40 import constructions
from voynich_smt.predicate_case import governor,probability as lexical_probability
from voynich_smt.occurrence_case import context,fit,predict
OUT=ROOT/'iteration44'
TREEBANKS=tuple(sorted(Path('data/latin-grammar-benchmark/proiel-r2.17').glob('*.conllu')))
AUTHORS=('Cicero','Palladius')


def fold(value):return int(hashlib.sha256(value.encode()).hexdigest(),16)%5


def prepare():
    assert not OUT.exists()
    for p,h in load(PREVIOUS/'verification-manifest.json')['inputs'].items():assert digest(p)==h,p
    declarations=sorted(set(ROOT.rglob('*manifest*.json'))|set(ROOT.rglob('*truth*.json')));used=set().union(*(set(strings(load(p))) for p in declarations));reserved={r['sent_id'] for rows in load(RESERVE)['authors'].values() for r in rows}
    OUT.mkdir();paths=[Path(__file__),Path('src/voynich_smt/occurrence_case.py'),Path('src/voynich_smt/predicate_case.py'),Path('src/voynich_smt/pp_contrast.py'),PREVIOUS/'verification-manifest.json',RESERVE]+list(TREEBANKS)
    save(OUT/'selection-manifest.json',dict(inputs={str(p):digest(p) for p in paths},prior_declarations={str(p):digest(p) for p in declarations},allowed_authors=AUTHORS,excluded_authors=['Jerome','Caesar'],
        selection='All cached PROIEL train/dev/test files, metadata filter before token parsing. Exclude reserve and ALL prior declared IDs (including old source/background), not just queries. Reject multiword IDs, non-singleword normalized tokens, and sentences outside3..60 retained tokens. Same simple contiguous PP extractor as iteration40.',
        fit_gate='At least100 source examples belonging to predicates with both cases, and at least10 distinct such predicates. Gate set before parsing annotations.',
        fixed_models='Unchanged iteration43 ridge1 residual context over mass4 lexical prior, bias calibration, global-offset context-only, and lemma control. Source leave-sentence-out training offsets, df>=2 vocabulary.',
        evaluation='Deterministic5fold sentence-grouped CV; deterministic5fold predicate-grouped CV (linked records only); leave-source-author-out. No prior Jerome/Caesar queries or reserve scoring; no hyperparameter selection. Case-free target-subtree-excluded oracle context remains privileged.'))
    data={};records=[];features=[];counts=Counter()
    for path in TREEBANKS:
        for block in path.read_text().split('\n\n'):
            lines=block.splitlines();sid=next((l.split(' = ',1)[1] for l in lines if l.startswith('# sent_id = ')),None);work=next((l.split(' = ',1)[1].split(',')[0] for l in lines if l.startswith('# source = ')),None);author=PROIEL.get(work)
            if sid is None or author not in AUTHORS or sid in reserved or sid in used:continue
            rows=[l.split('\t') for l in lines if l and not l.startswith('#')]
            if any('-' in r[0] for r in rows):continue
            rows=[r for r in rows if r[0].isdigit() and r[3]!='PUNCT'];norm=[words(r[1]) for r in rows]
            if not 3<=len(rows)<=60 or any(len(w)!=1 for w in norm):continue
            assert sid not in data
            index={r[0]:i for i,r in enumerate(rows)};tokens=[]
            for r,w in zip(rows,norm):
                fs=dict(f.split('=',1) for f in r[5].split('|') if '=' in f);normalize=lambda s:s.lower().replace('v','u').replace('j','i')
                tokens.append(dict(word=w[0],lemma=None if r[2]=='_' else normalize(r[2]),pos=r[3],case=fs.get('Case',''),head=index.get(r[6]),rel=r[7].split(':')[0],features=fs))
            data[sid]=dict(author=author,file=str(path),tokens=tokens);counts[author]+=1
            for number,c in enumerate(constructions(tokens)):
                if tokens[c['prep']]['word']!='in' or c['case'] not in ('Acc','Abl'):continue
                pred,hops=governor(tokens,c['head']);records.append(dict(sent_id=sid,author=author,construction=number,head=c['head'],prep=c['prep'],case=c['case'],predicate=tokens[pred]['lemma'] if pred is not None else None,oracle_index=pred,hops=hops));features.append(context(tokens,c['head'],pred))
    tables=defaultdict(Counter)
    for r in records:
        if r['predicate'] is not None:tables[r['predicate']][r['case']]+=1
    mixed={k:dict(v) for k,v in tables.items() if len(v)==2};well={k:v for k,v in mixed.items() if min(v.values())>=2};mixedn=sum(sum(v.values()) for v in mixed.values());gate=mixedn>=100 and len(mixed)>=10
    audit=dict(sentences=dict(counts),examples_by_author={a:dict(Counter(r['case'] for r in records if r['author']==a)) for a in AUTHORS},total_examples=len(records),linked=sum(r['predicate'] is not None for r in records),mixed_predicates=mixed,mixed_examples=mixedn,mixed_lemmas=len(mixed),at_least_two_each=well,fit_gate_passed=gate)
    save(OUT/'annotations-truth.json',data);save(OUT/'records-truth.json',records);save(OUT/'features.json',features);save(OUT/'audit.json',audit);save(OUT/'manifest.json',dict(inputs={str(p):digest(p) for p in paths},split_ids={a:[sid for sid,s in data.items() if s['author']==a] for a in AUTHORS},selection_manifest=digest(OUT/'selection-manifest.json')));save(OUT/'fit-freeze.json',dict(inputs={str(p):digest(p) for p in OUT.glob('*.json')}));print(audit,flush=True)


def run():
    assert not (OUT/'predictions.json').exists()
    for p,h in load(OUT/'fit-freeze.json')['inputs'].items():assert digest(p)==h,p
    assert load(OUT/'audit.json')['fit_gate_passed'],'Insufficient support; retain audit only.'
    rows=load(OUT/'records-truth.json');features=load(OUT/'features.json');predictions=[];models=[]
    for scheme in ('sentence','predicate','author'):
        eligible=[i for i,r in enumerate(rows) if scheme!='predicate' or r['predicate'] is not None];groups=AUTHORS if scheme=='author' else range(5)
        key=lambda r:r['author'] if scheme=='author' else fold(r['sent_id'] if scheme=='sentence' else r['predicate'])
        for group in groups:
            trainix=[i for i in eligible if key(rows[i])!=group];testix=[i for i in eligible if key(rows[i])==group];trainrows=[rows[i] for i in trainix];testrows=[rows[i] for i in testix];fs=[features[i] for i in trainix];ft=[features[i] for i in testix];ps={};trained={}
            for arm in ('calibration','context','context_only'):
                model=fit(trainrows,fs,arm);trained[arm]=model;ps[arm]=predict(model,ft,[r['predicate'] for r in testrows])
            ps['lexical']=[lexical_probability(model['lexical'],r['predicate']) for r in testrows];models.append(dict(scheme=scheme,group=group,train_ids=sorted({r['sent_id'] for r in trainrows}),test_ids=sorted({r['sent_id'] for r in testrows}),train_predicates=sorted({r['predicate'] for r in trainrows if r['predicate'] is not None}),models=trained))
            for j,row in enumerate(testrows):predictions.append(dict(**row,scheme=scheme,group=group,predictions={a:p[j] for a,p in ps.items()}))
            print('Fitted',scheme,group,len(trainrows),len(testrows),flush=True)
    save(OUT/'models.json',models);save(OUT/'predictions.json',predictions);save(OUT/'evaluation-freeze.json',dict(inputs={str(p):digest(p) for p in OUT.glob('*.json')}));evaluate()


def evaluate():
    rows=load(OUT/'predictions.json');audit=load(OUT/'audit.json');result={};intervals={}
    for scheme in ('sentence','predicate','author'):
        selected=[r for r in rows if r['scheme']==scheme]
        for author in ('pooled',)+AUTHORS:
            group=[r for r in selected if author=='pooled' or r['author']==author]
            for subset in ('all','mixed'):
                chosen=[r for r in group if subset=='all' or r['predicate'] in audit['mixed_predicates']]
                if not chosen:continue
                for arm in ('lexical','calibration','context','context_only'):result[f'{scheme}/{author}/{subset}/{arm}']=metrics(chosen,[r['predictions'][arm] for r in chosen])
                # Cluster by held predicate for predicate CV, sentence otherwise.
                cluster=lambda r:r['predicate'] if scheme=='predicate' else r['sent_id'];keys=sorted({cluster(r) for r in chosen});den=np.array([sum(cluster(r)==k for r in chosen) for k in keys]);y=np.array([r['case']=='Acc' for r in chosen]);base=np.array([r['predictions']['lexical'] for r in chosen]);p=np.array([r['predictions']['context'] for r in chosen]);gain=((p>.5)==y).astype(float)-((base>.5)==y);ll=y*np.log(p/base)+(1-y)*np.log((1-p)/(1-base));sums=np.array([[gain[[cluster(r)==k for r in chosen]].sum(),ll[[cluster(r)==k for r in chosen]].sum()] for k in keys]);draw=np.random.default_rng(44999).integers(0,len(keys),(10000,len(keys)));samples=sums[draw].sum(axis=1)/den[draw].sum(axis=1)[:,None];intervals[f'{scheme}/{author}/{subset}']=dict(accuracy_gain95=np.quantile(samples[:,0],[.025,.975]).tolist(),logloss_reduction95=np.quantile(samples[:,1],[.025,.975]).tolist(),cluster='predicate' if scheme=='predicate' else 'sentence')
    save(OUT/'evaluation.json',dict(metrics=result,paired_intervals=intervals,note='Source internal checks only, fixed settings; intervals condition on fitted folds. Mixed cohort defined by full audited source labels; training folds may lack one case. No target-query scoring.'))
    for k,v in result.items():
        if '/pooled/' in k:print(k,v)

if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='prepare':prepare()
    else:run()
