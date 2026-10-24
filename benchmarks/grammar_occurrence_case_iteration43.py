"""Frozen occurrence-context diagnostic with case-free feature extraction."""
from pathlib import Path
from collections import defaultdict,Counter
import hashlib
import numpy as np
from benchmarks.grammar_predicate_profiles_iteration42 import OUT as PREVIOUS,ROOT,TREEBANK,RESERVE,load,save,digest,metrics
from voynich_smt.occurrence_case import context,fit,predict
from voynich_smt.predicate_case import probability as lexical_probability
OUT=ROOT/'iteration43'
RECORDS=ROOT/'iteration41/records-truth.json'
SEEDS=tuple(range(43001,43101))


def annotations(ids):
    wanted=set(ids);reserve={r['sent_id'] for rows in load(RESERVE)['authors'].values() for r in rows};assert not wanted&reserve;data={}
    for block in TREEBANK.read_text().split('\n\n'):
        lines=block.splitlines();sid=next((l.split(' = ',1)[1] for l in lines if l.startswith('# sent_id = ')),None)
        if sid in reserve or sid not in wanted:continue
        rows=[l.split('\t') for l in lines if l and not l.startswith('#')];rows=[r for r in rows if r[0].isdigit() and r[3]!='PUNCT'];index={r[0]:i for i,r in enumerate(rows)};tokens=[]
        for r in rows:
            norm=lambda s:s.lower().replace('v','u').replace('j','i');features=dict(f.split('=',1) for f in r[5].split('|') if '=' in f)
            tokens.append(dict(word=norm(r[1]),lemma=None if r[2]=='_' else norm(r[2]),pos=r[3],head=index.get(r[6]),rel=r[7].split(':')[0],features=features))
        data[sid]=tokens
    assert set(data)==wanted
    return data


def get_features(rows,data,mode):
    return [context(data[r['sent_id']],r['head'],r['oracle_index'] if mode=='oracle' else r['nearest_index']) for r in rows]


def shuffle(features,rows,seed):
    # Permute contexts within lemma, preserving all lexical-label associations.
    groups=defaultdict(list)
    for i,r in enumerate(rows):groups[r['predicate']].append(i)
    rng=np.random.default_rng(seed);result=features[:]
    for ix in groups.values():
        for target,donor in zip(ix,rng.permutation(ix)):result[target]=features[int(donor)]
    return result


def run():
    assert not OUT.exists()
    for p,h in load(PREVIOUS/'verification-manifest.json')['inputs'].items():assert digest(p)==h,p
    splits=load(PREVIOUS/'manifest.json')['split_ids'];data=annotations(sum(splits.values(),[]));records=load(RECORDS);features={s:{mode:get_features(rows,data,mode) for mode,rows in modes.items()} for s,modes in records.items()};models={}
    for mode in ('oracle','nearest'):
        for arm in ('calibration','context','context_only'):models[f'{mode}/{arm}']=fit(records['source'][mode],features['source'][mode],arm)
    mixed=defaultdict(Counter)
    for r in records['source']['oracle']:mixed[r['predicate']][r['case']]+=1
    mixed={k:dict(v) for k,v in mixed.items() if k is not None and len(v)>1}
    OUT.mkdir();save(OUT/'annotations-truth.json',data);save(OUT/'features.json',features);save(OUT/'models.json',models)
    paths=[Path(__file__),Path('src/voynich_smt/occurrence_case.py'),Path('src/voynich_smt/predicate_case.py'),TREEBANK,RESERVE,RECORDS,PREVIOUS/'verification-manifest.json',PREVIOUS/'manifest.json']
    save(OUT/'manifest.json',dict(inputs={str(p):digest(p) for p in paths},split_ids=splits,ridge=1.,minimum_feature_df=2,shuffle_seeds=SEEDS,mixed_source_predicates=mixed,
        scope='Same source171/target17+41 eligible in examples, reused development only. No source expansion/fresh/reserve scoring. Oracle POS/lemmas/morphology and reference topology for predicate link and target subtree exclusion.',
        features='Occurrence-level verbal VerbForm/Mood/Tense/Voice/Person; other child relation/POS/lemma and their prepositions; parent POS/lemma. Entire target nominal subtree excluded. No target lexical/morphological features, case features anywhere, Number/Gender, target dependency relation, or predicate identity feature.',
        fitting='Ridge1 logistic residual over mass4 lemma prior; source priors leave entire sentence out. Calibration-only bias control and context-only global-offset control. Feature df>=2 source only. No target tuning.',
        controls='Existing lemma model; bias calibration; global-offset context-only; nearest matched training and oracle-trained nearest inference;100 source-context shuffles within predicate preserving lexical case distributions; source deterministic5fold by sentence ID, rebuild vocabulary and priors each fold.',
        evaluation='All, seen, unseen, source-mixed lemma cohorts; accuracy/BA/logloss/Brier; paired10000 sentence bootstrap vs lemma and calibration. Also source5fold metrics and per-predicate outcomes. Small mixed-lemma source support is an explicit limit.'))
    save(OUT/'prediction-freeze.json',dict(inputs={str(p):digest(p) for p in OUT.glob('*.json')}));pred={};shuffled=[];cv=[]
    for author in ('Jerome','Caesar'):
        rows=records[author]['oracle'];near=records[author]['nearest'];model=models['oracle/context'];pred[author]={'lexical':[lexical_probability(model['lexical'],r['predicate']) for r in rows]}
        for arm in ('calibration','context','context_only'):pred[author][arm]=predict(models[f'oracle/{arm}'],features[author]['oracle'],[r['predicate'] for r in rows])
        pred[author]['nearest_matched']=predict(models['nearest/context'],features[author]['nearest'],[r['predicate'] for r in near]);pred[author]['nearest_oracle_model']=predict(model,features[author]['nearest'],[r['predicate'] for r in near])
    source=records['source']['oracle'];sf=features['source']['oracle']
    for seed in SEEDS:
        model=fit(source,shuffle(sf,source,seed),'context');shuffled.append(dict(seed=seed,predictions={a:predict(model,features[a]['oracle'],[r['predicate'] for r in records[a]['oracle']]) for a in ('Jerome','Caesar')}))
    fold=lambda sid:int(hashlib.sha256(sid.encode()).hexdigest(),16)%5
    for f in range(5):
        trainix=[i for i,r in enumerate(source) if fold(r['sent_id'])!=f];testix=[i for i,r in enumerate(source) if fold(r['sent_id'])==f];trainrows=[source[i] for i in trainix];testrows=[source[i] for i in testix];fs=[sf[i] for i in trainix];ft=[sf[i] for i in testix];ps={}
        for arm in ('calibration','context','context_only'):
            m=fit(trainrows,fs,arm);ps[arm]=predict(m,ft,[r['predicate'] for r in testrows])
        ps['lexical']=[lexical_probability(m['lexical'],r['predicate']) for r in testrows]
        for j,r in enumerate(testrows):cv.append(dict(**r,fold=f,predictions={k:v[j] for k,v in ps.items()}))
    save(OUT/'predictions.json',pred);save(OUT/'shuffled-predictions.json',shuffled);save(OUT/'source-cv.json',cv);save(OUT/'evaluation-freeze.json',dict(inputs={str(p):digest(p) for p in OUT.glob('*.json')}));evaluate()


def evaluate():
    records=load(RECORDS);models=load(OUT/'models.json');pred=load(OUT/'predictions.json');manifest=load(OUT/'manifest.json');shuffles=load(OUT/'shuffled-predictions.json');result={};intervals={};controls={};counts={}
    for author in ('Jerome','Caesar'):
        rows=records[author]['oracle'];known=models['oracle/context']['lexical']['counts'];masks=dict(all=[True]*len(rows),seen=[r['predicate'] in known for r in rows],unseen=[r['predicate'] not in known for r in rows],mixed=[r['predicate'] in manifest['mixed_source_predicates'] for r in rows]);counts[author]={k:sum(v) for k,v in masks.items()}
        for subset,mask in masks.items():
            ix=np.flatnonzero(mask);selected=[rows[i] for i in ix]
            for arm,p in pred[author].items():result[f'{author}/{subset}/{arm}']=metrics(selected,[p[i] for i in ix])
            if not len(ix):continue
            for arm in ('context','calibration','context_only','nearest_matched','nearest_oracle_model'):
                for reference in ('lexical','calibration'):
                    sid=sorted({r['sent_id'] for r in selected});draw=np.random.default_rng(43999).integers(0,len(sid),(10000,len(sid)));den=np.array([sum(r['sent_id']==s for r in selected) for s in sid]);p=np.array(pred[author][arm])[ix];base=np.array(pred[author][reference])[ix];y=np.array([r['case']=='Acc' for r in selected]);gain=((p>.5)==y).astype(float)-((base>.5)==y);ll=y*np.log(p/base)+(1-y)*np.log((1-p)/(1-base));totals=np.array([[gain[[r['sent_id']==s for r in selected]].sum(),ll[[r['sent_id']==s for r in selected]].sum()] for s in sid]);sample=totals[draw].sum(axis=1)/den[draw].sum(axis=1)[:,None];intervals[f'{author}/{subset}/{arm}-vs-{reference}']=dict(accuracy_gain95=np.quantile(sample[:,0],[.025,.975]).tolist(),logloss_reduction95=np.quantile(sample[:,1],[.025,.975]).tolist())
            controls[f'{author}/{subset}']={}
            for metric in ('accuracy','log_loss'):
                values=[metrics(selected,[r['predictions'][author][i] for i in ix])[metric] for r in shuffles];controls[f'{author}/{subset}'][metric]=dict(mean=float(np.mean(values)),range95=np.quantile(values,[.025,.975]).tolist())
    cv=load(OUT/'source-cv.json');source_metrics={arm:metrics(cv,[r['predictions'][arm] for r in cv]) for arm in ('lexical','calibration','context','context_only')};mixedcv=[r for r in cv if r['predicate'] in manifest['mixed_source_predicates']];mixed_metrics={arm:metrics(mixedcv,[r['predictions'][arm] for r in mixedcv]) for arm in source_metrics}
    save(OUT/'evaluation.json',dict(metrics=result,coverage=counts,paired_intervals=intervals,shuffled=controls,source_cv=source_metrics,source_mixed_cv=mixed_metrics));print('Mixed source',manifest['mixed_source_predicates'],'Coverage',counts,'SourceCV',source_metrics,'MixedCV',mixed_metrics)
    for k,v in result.items():
        if '/all/' in k:print(k,v)
if __name__=='__main__':run()
