"""Predicate context for in+Acc/Abl: source-only, reused development diagnostic."""
from pathlib import Path
import numpy as np
from benchmarks.grammar_pp_contrast_iteration40 import OUT as PREVIOUS,ROOT,TREEBANK,RESERVE,load,save,digest,constructions
from voynich_smt.predicate_case import fit,probability,governor,nearest
OUT=ROOT/'iteration41'
STRENGTHS=(1.,4.,16.)
PRIMARY=4.
SEEDS=tuple(range(41001,41101))


def records(data,ids,mode):
    result=[]
    for sid in ids:
        tokens=data[sid]
        for index,c in enumerate(constructions(tokens)):
            if tokens[c['prep']]['word']!='in' or c['case'] not in ('Acc','Abl'):continue
            oracle,hops=governor(tokens,c['head']);near=nearest(tokens,c['prep']);chosen=oracle if mode=='oracle' else near
            result.append(dict(sent_id=sid,construction=index,prep=c['prep'],head=c['head'],case=c['case'],predicate=tokens[chosen]['lemma'] if chosen is not None else None,oracle_index=oracle,nearest_index=near,hops=hops,direct=hops==1))
    return result


def metrics(rows,p):
    y=np.array([r['case']=='Acc' for r in rows]);p=np.array(p);pred=p>.5
    if not len(y):return dict(n=0)
    return dict(n=len(y),accusative=int(y.sum()),accuracy=float((pred==y).mean()),balanced_accuracy=float(np.mean([(pred[y==v]==v).mean() for v in (False,True) if np.any(y==v)])),log_loss=float(-np.mean(y*np.log(p)+(1-y)*np.log1p(-p))),brier=float(np.mean((p-y)**2)))


def prepare():
    assert not OUT.exists()
    for p,h in load(PREVIOUS/'verification-manifest.json')['inputs'].items():assert digest(p)==h,p
    splits=load(PREVIOUS/'manifest.json')['split_ids'];wanted=set(sum(splits.values(),[]));reserve={r['sent_id'] for rows in load(RESERVE)['authors'].values() for r in rows};assert not wanted&reserve;data=load(PREVIOUS/'data-truth.json');lemmas={}
    for block in TREEBANK.read_text().split('\n\n'):
        lines=block.splitlines();sid=next((l.split(' = ',1)[1] for l in lines if l.startswith('# sent_id = ')),None)
        if sid in reserve or sid not in wanted:continue
        rows=[l.split('\t') for l in lines if l and not l.startswith('#')];rows=[r for r in rows if r[0].isdigit() and r[3]!='PUNCT'];assert len(rows)==len(data[sid])
        for token,row in zip(data[sid],rows):
            assert token['word']==row[1].lower().replace('v','u').replace('j','i')
            token['lemma']=None if row[2]=='_' else row[2].lower().replace('v','u').replace('j','i')
    allrecords={split:{mode:records(data,ids,mode) for mode in ('oracle','nearest')} for split,ids in splits.items()};models={}
    for mode in ('oracle','nearest'):
        for strength in STRENGTHS:models[f'{mode}/{strength}']=fit(allrecords['source'][mode],strength)
    OUT.mkdir();save(OUT/'records-truth.json',allrecords);save(OUT/'models.json',models)
    paths=[Path(__file__),Path('src/voynich_smt/predicate_case.py'),TREEBANK,RESERVE,PREVIOUS/'verification-manifest.json',PREVIOUS/'data-truth.json',PREVIOUS/'manifest.json']
    save(OUT/'manifest.json',dict(inputs={str(p):digest(p) for p in paths},split_ids=splits,primary_strength=PRIMARY,strengths=STRENGTHS,shuffle_seeds=SEEDS,
        scope='Reused iteration40 simple contiguous PP constructions, restricted to in+Acc/Abl. Source Jerome/Palladius; Caesar unseen author but reused queries. Oracle POS, head case for labels/eligibility, prep identity, predicate lemma and dependency ancestor links. No ciphertext restoration or new holdout confirmation.',
        hypothesis='Does first verbal ancestor lemma improve binary case prediction over source-only in case frequency? Compare nearest verbal token, oracle-trained model with nearest link, and100 shuffled-source predicate assignments.',
        estimator='Beta-smoothed source Acc frequency; per-predicate counts shrink to baseline with fixed mass4. Sensitivities1/16, no target selection. Missing or unseen lemma exactly baseline. No target case or head morphology enters probability().',
        evaluation='All eligible, oracle-linked, direct, source-seen/unseen oracle lemmas. Accuracy, balanced accuracy, logloss, Brier; paired sentence bootstrap fixed predictions10000. Binary decision pAcc>.5; no target threshold fitting. Record link coverage and exact nearest agreement.'))
    save(OUT/'prediction-freeze.json',dict(inputs={str(p):digest(p) for p in OUT.glob('*.json')}))


def run():
    prepare();rec=load(OUT/'records-truth.json');models=load(OUT/'models.json');predictions={};shuffled=[]
    for author in ('Jerome','Caesar'):
        rows=rec[author]['oracle'];near=rec[author]['nearest'];arms={'baseline':[models['oracle/4.0']['base']]*len(rows)}
        for strength in STRENGTHS:
            arms[f'oracle/{strength}']=[probability(models[f'oracle/{strength}'],r['predicate']) for r in rows]
        arms['nearest_matched']=[probability(models['nearest/4.0'],r['predicate']) for r in near]
        arms['nearest_oracle_model']=[probability(models['oracle/4.0'],r['predicate']) for r in near];predictions[author]=arms
    source=rec['source']['oracle']
    for seed in SEEDS:
        order=np.random.default_rng(seed).permutation(len(source));fake=[dict(r,predicate=source[int(j)]['predicate']) for r,j in zip(source,order)];model=fit(fake,PRIMARY)
        shuffled.append(dict(seed=seed,predictions={author:[probability(model,r['predicate']) for r in rec[author]['oracle']] for author in ('Jerome','Caesar')}))
    save(OUT/'predictions.json',predictions);save(OUT/'shuffled-predictions.json',shuffled);save(OUT/'evaluation-freeze.json',dict(inputs={str(p):digest(p) for p in OUT.glob('*.json')}));evaluate()


def evaluate():
    rec=load(OUT/'records-truth.json');models=load(OUT/'models.json');pred=load(OUT/'predictions.json');shuffled=load(OUT/'shuffled-predictions.json');result={};intervals={};controls={};coverage={}
    for author in ('Jerome','Caesar'):
        rows=rec[author]['oracle'];model=models['oracle/4.0'];masks=dict(all=[True]*len(rows),linked=[r['oracle_index'] is not None for r in rows],direct=[r['direct'] for r in rows],seen=[r['predicate'] in model['counts'] for r in rows],unseen=[r['predicate'] not in model['counts'] for r in rows])
        coverage[author]=dict(total=len(rows),linked=sum(masks['linked']),direct=sum(masks['direct']),seen=sum(masks['seen']),unseen=sum(masks['unseen']),nearest_correct=sum(r['oracle_index'] is not None and r['oracle_index']==r['nearest_index'] for r in rows))
        for subset,mask in masks.items():
            indices=np.flatnonzero(mask);subsetrows=[rows[i] for i in indices]
            for arm,probs in pred[author].items():result[f'{author}/{subset}/{arm}']=metrics(subsetrows,[probs[i] for i in indices])
        y=np.array([r['case']=='Acc' for r in rows]);baseline=np.array(pred[author]['baseline']);sid=sorted({r['sent_id'] for r in rows});rng=np.random.default_rng(41999);draw=rng.integers(0,len(sid),(10000,len(sid)));den=np.array([sum(r['sent_id']==s for r in rows) for s in sid])
        for arm,probs in pred[author].items():
            p=np.array(probs);gain=((p>.5)==y).astype(float)-((baseline>.5)==y);llgain=y*np.log(p/baseline)+(1-y)*np.log((1-p)/(1-baseline));totals=np.array([[gain[[r['sent_id']==s for r in rows]].sum(),llgain[[r['sent_id']==s for r in rows]].sum()] for s in sid]);sample=totals[draw].sum(axis=1)/den[draw].sum(axis=1)[:,None];intervals[f'{author}/{arm}']=dict(accuracy_gain=np.quantile(sample[:,0],[.025,.975]).tolist(),logloss_reduction=np.quantile(sample[:,1],[.025,.975]).tolist())
        controls[author]={}
        for metric in ('accuracy','balanced_accuracy','log_loss','brier'):
            values=[metrics(rows,s['predictions'][author])[metric] for s in shuffled];observed=result[f'{author}/all/oracle/4.0'][metric];better=sum(v<=observed if metric in ('accuracy','balanced_accuracy') else v>=observed for v in values)
            controls[author][metric]=dict(mean=float(np.mean(values)),range95=np.quantile(values,[.025,.975]).tolist(),observed_percentile=better/len(values),note='Descriptive percentile among100 source-label-context permutations; not independent hypothesis tests.')
    save(OUT/'evaluation.json',dict(metrics=result,coverage=coverage,paired_intervals=intervals,shuffled=controls));print('Coverage',coverage)
    for key,value in result.items():
        if '/all/' in key:print(key,value)
    print('Controls',controls)
if __name__=='__main__':run()
