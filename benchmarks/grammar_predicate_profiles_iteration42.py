"""Can other source constructions transfer case preference to unseen-in verbs?"""
from pathlib import Path
from collections import Counter,defaultdict
import numpy as np
from benchmarks.grammar_predicate_case_iteration41 import OUT as PREVIOUS,ROOT,TREEBANK,RESERVE,load,save,digest,metrics
from voynich_smt.predicate_case import probability as lexical_probability
from voynich_smt.predicate_profiles import build_profiles,vectorize,train,probability,transfer
OUT=ROOT/'iteration42'
SEEDS=tuple(range(42001,42101))


def source_data(ids):
    wanted=set(ids);reserve={r['sent_id'] for rows in load(RESERVE)['authors'].values() for r in rows};assert not wanted&reserve;data={}
    for block in TREEBANK.read_text().split('\n\n'):
        lines=block.splitlines();sid=next((l.split(' = ',1)[1] for l in lines if l.startswith('# sent_id = ')),None)
        if sid in reserve or sid not in wanted:continue
        rows=[l.split('\t') for l in lines if l and not l.startswith('#')];rows=[r for r in rows if r[0].isdigit() and r[3]!='PUNCT'];indices={r[0]:i for i,r in enumerate(rows)};tokens=[]
        for r in rows:
            feats=dict(x.split('=',1) for x in r[5].split('|') if '=' in x);norm=lambda x:x.lower().replace('v','u').replace('j','i')
            tokens.append(dict(word=norm(r[1]),lemma=None if r[2]=='_' else norm(r[2]),pos=r[3],case=feats.get('Case',''),head=indices.get(r[6]),rel=r[7].split(':')[0]))
        data[sid]=tokens
    assert set(data)==wanted
    return data


def shuffled_profiles(profiles,occurrences,seed):
    # Permute within source verb-frequency bins; keep nonempty profile coverage.
    bins=defaultdict(list)
    for lemma in sorted(profiles):bins[int(np.log2(1+occurrences[lemma]))].append(lemma)
    rng=np.random.default_rng(seed);result={}
    for lemmas in bins.values():
        for target,donor in zip(lemmas,rng.permutation(lemmas)):result[target]=profiles[donor]
    return result


def prepare():
    assert not OUT.exists()
    for p,h in load(PREVIOUS/'verification-manifest.json')['inputs'].items():assert digest(p)==h,p
    splits=load(PREVIOUS/'manifest.json')['split_ids'];source=source_data(splits['source']);profiles=build_profiles(source.values());records=load(PREVIOUS/'records-truth.json');models={mode:train(records['source'][mode],profiles['profiles']) for mode in ('oracle','nearest')}
    OUT.mkdir();save(OUT/'source-annotations.json',source);save(OUT/'source-profiles.json',profiles);save(OUT/'models.json',models)
    paths=[Path(__file__),Path('src/voynich_smt/predicate_profiles.py'),Path('src/voynich_smt/predicate_case.py'),TREEBANK,RESERVE,PREVIOUS/'verification-manifest.json',PREVIOUS/'manifest.json',PREVIOUS/'records-truth.json',PREVIOUS/'predictions.json']
    save(OUT/'manifest.json',dict(inputs={str(p):digest(p) for p in paths},split_ids=splits,k=5,strength=4,shuffle_seeds=SEEDS,
        scope='Same source767 and reused target17/41 in+Acc/Abl examples as iteration41. No expansion of source IDs, no fresh confirmation, no reserve scoring. Predicate profiles extracted from source only, never target contexts.',
        profile='Direct dependency relation/POS/case, nominal argument lemmas and non-in preposition-case frames, aggregated by source predicate lemma. Exclude any direct child subtree containing an in ADP, including indirect cases. No predicate-identity features or in case evidence.',
        transfer='Source TF-IDF cosine similarity, top5 positive-similarity labeled donor predicates excluding the query lemma. Similarity-weighted mean of donor case rates shrunk with mass4 to baseline. No profile/no neighbors -> exact baseline. Hybrid uses transfer as mass4 prior for own case counts; transfer-only never uses own counts. No target tuning.',
        controls='Existing lexical counts; preposition baseline; nearest-context matched training and oracle-trained inference;100 profile permutations within log2 source occurrence bins. Permute only nonempty profiles, preserve coverage. Reused source leave-predicate-out removes every case label of held lemma and refits baseline/counts; non-in source profiles retained as label-independent covariates.',
        evaluation='All, unseen-in lemma, unseen-in but source-profile-covered, no-profile, seen-in; full coverage counts. Accuracy/BA/logloss/Brier; fixed-model paired sentence bootstrap10000 vs lexical model. Source leave-predicate-out macro by predicate and token metrics. Oracle annotations and plaintext lexical contexts retained.'))
    save(OUT/'prediction-freeze.json',dict(inputs={str(p):digest(p) for p in OUT.glob('*.json')}))


def run():
    prepare();rec=load(PREVIOUS/'records-truth.json');profiles=load(OUT/'source-profiles.json');models=load(OUT/'models.json');vectors=vectorize(profiles['profiles']);pred={};audit=[]
    for author in ('Jerome','Caesar'):
        rows=rec[author]['oracle'];near=rec[author]['nearest'];model=models['oracle'];pred[author]=dict(baseline=[model['base']]*len(rows),lexical=[lexical_probability(model,r['predicate']) for r in rows],transfer_only=[probability(model,r['predicate'],False,vectors) for r in rows],hybrid=[probability(model,r['predicate'],True,vectors) for r in rows],nearest_matched=[probability(models['nearest'],r['predicate'],True,vectors) for r in near],nearest_oracle_model=[probability(model,r['predicate'],True,vectors) for r in near])
        for row in rows:
            p,neighbors=transfer(model,row['predicate'],vectors);audit.append(dict(author=author,**row,source_profile=row['predicate'] in vectors,seen_in=row['predicate'] in model['counts'],transfer_p=p,neighbors=neighbors))
    shuffles=[]
    for seed in SEEDS:
        fake=shuffled_profiles(profiles['profiles'],profiles['occurrences'],seed);v=vectorize(fake);model=dict(models['oracle'],profiles=fake)
        shuffles.append(dict(seed=seed,predictions={a:[probability(model,r['predicate'],True,v) for r in rec[a]['oracle']] for a in ('Jerome','Caesar')}))
    lpo=[];source=rec['source']['oracle']
    for lemma in sorted({r['predicate'] for r in source if r['predicate'] is not None}):
        trainrows=[r for r in source if r['predicate']!=lemma];model=train(trainrows,profiles['profiles'])
        for r in source:
            if r['predicate']==lemma:lpo.append(dict(**r,baseline=model['base'],profile=probability(model,lemma,False,vectors)))
    save(OUT/'predictions.json',pred);save(OUT/'neighbor-audit.json',audit);save(OUT/'shuffled-predictions.json',shuffles);save(OUT/'leave-predicate-out.json',lpo);save(OUT/'evaluation-freeze.json',dict(inputs={str(p):digest(p) for p in OUT.glob('*.json')}));evaluate()


def evaluate():
    rec=load(PREVIOUS/'records-truth.json');model=load(OUT/'models.json')['oracle'];pred=load(OUT/'predictions.json');profiles=vectorize(model['profiles']);shuffles=load(OUT/'shuffled-predictions.json');result={};coverage={};intervals={};control={}
    for author in ('Jerome','Caesar'):
        rows=rec[author]['oracle'];masks=dict(all=[True]*len(rows),unseen_in=[r['predicate'] not in model['counts'] for r in rows],unseen_profiled=[r['predicate'] not in model['counts'] and r['predicate'] in profiles for r in rows],no_profile=[r['predicate'] not in profiles for r in rows],seen_in=[r['predicate'] in model['counts'] for r in rows]);coverage[author]={k:sum(v) for k,v in masks.items()}
        for subset,mask in masks.items():
            ix=np.flatnonzero(mask);selected=[rows[i] for i in ix]
            for arm,ps in pred[author].items():result[f'{author}/{subset}/{arm}']=metrics(selected,[ps[i] for i in ix])
            # All arms evaluated on cohorts defined by oracle predicate membership.
            if not len(ix):continue
            sid=sorted({r['sent_id'] for r in selected});draw=np.random.default_rng(42999).integers(0,len(sid),(10000,len(sid)));den=np.array([sum(r['sent_id']==s for r in selected) for s in sid]);y=np.array([r['case']=='Acc' for r in selected]);base=np.array(pred[author]['lexical'])[ix]
            for arm in ('transfer_only','hybrid','nearest_matched','nearest_oracle_model'):
                p=np.array(pred[author][arm])[ix];gain=((p>.5)==y).astype(float)-((base>.5)==y);ll=y*np.log(p/base)+(1-y)*np.log((1-p)/(1-base));totals=np.array([[gain[[r['sent_id']==s for r in selected]].sum(),ll[[r['sent_id']==s for r in selected]].sum()] for s in sid]);samples=totals[draw].sum(axis=1)/den[draw].sum(axis=1)[:,None];intervals[f'{author}/{subset}/{arm}']=dict(accuracy_gain95=np.quantile(samples[:,0],[.025,.975]).tolist(),logloss_reduction95=np.quantile(samples[:,1],[.025,.975]).tolist())
            control[f'{author}/{subset}']={}
            for metric in ('accuracy','log_loss'):
                values=[metrics(selected,[r['predictions'][author][i] for i in ix])[metric] for r in shuffles];control[f'{author}/{subset}'][metric]=dict(mean=float(np.mean(values)),range95=np.quantile(values,[.025,.975]).tolist())
    lpo=load(OUT/'leave-predicate-out.json');lporesult={}
    for arm in ('baseline','profile'):
        grouped=defaultdict(list)
        for r in lpo:grouped[r['predicate']].append(r)
        lporesult[arm]=dict(token_metrics=metrics(lpo,[r[arm] for r in lpo]),predicates=len(grouped),macro_accuracy=float(np.mean([metrics(v,[r[arm] for r in v])['accuracy'] for v in grouped.values()])),macro_logloss=float(np.mean([metrics(v,[r[arm] for r in v])['log_loss'] for v in grouped.values()])))
    save(OUT/'evaluation.json',dict(metrics=result,coverage=coverage,paired_intervals=intervals,shuffled=control,leave_predicate_out=lporesult));print('Coverage',coverage,'LPO',lporesult)
    for k,v in result.items():
        if '/all/' in k or ('/unseen_profiled/' in k and (k.endswith('lexical') or k.endswith('hybrid'))):print(k,v)
if __name__=='__main__':run()
