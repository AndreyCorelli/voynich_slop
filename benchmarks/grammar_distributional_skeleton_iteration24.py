"""Distributional classes and conservative cipher relation skeletons."""
from collections import Counter,defaultdict
from dataclasses import asdict
from pathlib import Path
import hashlib
import time
import numpy as np
from benchmarks.grammar_cipher_relations_iteration23 import OUT as PREVIOUS,TREEBANK,ROOT,load,save,strings,LABEL_MAP
from benchmarks.grammar_relative_constituents_iteration15 import RESERVE
from benchmarks.scalable_latin_caesar import words,PROIEL
from voynich_smt.cipher_relations import views,candidates,matrix,fit,probabilities,LABELS
from voynich_smt.distributional_grammar import observations,fit_prototypes,attach_profiles,pair_features,consensus,skeleton,wilson_lower
from voynich_smt.relative_constituents import ConstituentAdapter
from voynich_smt.word_mapping.morphology import WhitakerAnnotator

OUT=ROOT/'iteration24'
ARMS=('baseline','profiles','shuffled_profiles','dictionary')
SEEDS=(24011,24012,24013)
THRESHOLDS=(.1,.2,.3,.4,.5,.6,.7,.8,.9,.95)
MARGINS=(0.,.05,.1,.2)
TARGETS=(.5,.7,.85)
KEYS={'train':404,'tune':505,'test_jerome':606,'test_caesar':606}


def prepare():
    if OUT.exists():raise ValueError('Preserve artifacts')
    files=sorted(set(ROOT.rglob('*manifest*.json'))|set(ROOT.rglob('*truth*.json')))
    prior=set().union(*(set(strings(load(p))) for p in files));reserved={r['sent_id'] for group in load(RESERVE)['authors'].values() for r in group}
    old=load(PREVIOUS/'datasets.json');train_ids={s['sent_id'] for s in old['train']};train=[];fresh={'Jerome':[],'Caesar':[]}
    for block in TREEBANK.read_text().split('\n\n'):
        lines=block.splitlines();sid=next((l.split(' = ',1)[1] for l in lines if l.startswith('# sent_id = ')),None)
        source=next((l.split(' = ',1)[1].split(',')[0] for l in lines if l.startswith('# source = ')),None);author=PROIEL.get(source)
        if sid in reserved:continue
        fresh_ok=author in fresh and sid not in prior and len(fresh[author])<(740 if author=='Jerome' else 500)
        if sid not in train_ids and not fresh_ok:continue
        rows=[l.split('\t') for l in lines if l and not l.startswith('#')]
        if any('-' in r[0] for r in rows):continue
        raw={r[0]:r for r in rows if r[0].isdigit()};kept=[r for r in raw.values() if r[3]!='PUNCT'];norm=[words(r[1]) for r in kept]
        if not 3<=len(kept)<=60 or any(len(w)!=1 for w in norm):continue
        record=dict(sent_id=sid,author=author,tokens=[w[0] for w in norm])
        background=fresh_ok and len(fresh[author])>=(140 if author=='Jerome' else 100)
        if not background:
            positions={r[0]:i for i,r in enumerate(kept)};edges=[];properties={'upos':[],'case':[],'number':[]}
            for i,r in enumerate(kept):
                h=r[6];seen=set()
                while h!='0' and h not in positions:
                    assert h not in seen;seen.add(h);h=raw[h][6]
                label=LABEL_MAP.get(r[7].split(':')[0])
                if h in positions and label is not None:edges.append([i,positions[h],label])
                f=dict(x.split('=',1) for x in r[5].split('|') if '=' in x)
                properties['upos'].append(r[3]);properties['case'].append(f.get('Case'));properties['number'].append(f.get('Number'))
            record.update(edges=edges,properties=properties)
        if sid in train_ids:train.append(record)
        else:fresh[author].append(record)
    assert len(train)==767 and len(fresh['Jerome'])==740 and len(fresh['Caesar'])==500
    data=dict(train=train,tune=fresh['Jerome'][:40],test_jerome=fresh['Jerome'][40:140],test_caesar=fresh['Caesar'][:100],
        background_tune=fresh['Jerome'][140:340],background_jerome=fresh['Jerome'][340:],background_caesar=fresh['Caesar'][100:])
    assert all('edges' not in s and 'properties' not in s for split,ss in data.items() if split.startswith('background') for s in ss)
    a=ConstituentAdapter(WhitakerAnnotator('data/vendor/whitakers-words',mode='upstream-default'))
    # Only the explicit dictionary ceiling needs a lattice; background labels
    # and dictionary readings never enter anonymous profiles.
    vocabulary=sorted({w for split,ss in data.items() if not split.startswith('background') for s in ss for w in s['tokens']})
    lattice={w:[asdict(r) for r in a.analyze(w)] for w in vocabulary}
    OUT.mkdir();save(OUT/'datasets.json',data);save(OUT/'morphology-lattice.json',lattice)
    paths=[Path(__file__),Path('src/voynich_smt/distributional_grammar.py'),Path('src/voynich_smt/cipher_relations.py'),TREEBANK,RESERVE,PREVIOUS/'datasets.json']
    save(OUT/'manifest.json',dict(inputs={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        prior_declarations={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},split_ids={split:[s['sent_id'] for s in ss] for split,ss in data.items()},
        arms=ARMS,keys=KEYS,bootstrap_seeds=SEEDS,thresholds=THRESHOLDS,margins=MARGINS,precision_targets=TARGETS,
        profile='Neighbor rank histograms at offsets -2,-1,+1,+2; train-only 8 word/8 ending centroids; leave-predicted-sentence-out observations; counts/ranks transductive.',
        context_control='Independently shuffle within each sentence with fixed positional RNG seed; counts and ending identities preserved; prototypes refit without labels.',
        skeleton='Unanimous head+label across three sentence-bootstrap classifiers; no numeric ties; threshold/margin and acyclic greedy subset; no forced completion.',
        calibration='Max recall with tuning Wilson 95% lower precision bound >= target and >=20 predictions; otherwise abstain entirely. Selected bounds are diagnostics, not test guarantees.',
        auxiliary='Training-majority mapping from cluster pairs to source coarse POS/Case/Number; labels read only by readout fitter and evaluator.',
        freshness='New tune/test/background IDs disjoint from prior grammar manifest/truth declarations and reservation; prior training reused. Sentence boundaries supplied.',
        lexicon_resource=a.analyzer.resource))
    print('Prepared',{k:(len(ss),sum(len(s['tokens']) for s in ss)) for k,ss in data.items()},flush=True)


def phase_views(data,split,lattice,key=None):
    background={'train':None,'tune':'background_tune','test_jerome':'background_jerome','test_caesar':'background_caesar'}[split]
    bg=data[background] if background else [];combined=bg+data[split]
    return views(combined,KEYS[split] if key is None else key,lattice),len(bg)


def relation_matrix(sentences,vv,arm):
    rows=[];targets=[];slices=[];pairs_all=[];offset=0
    for s,v in zip(sentences,vv):
        pairs=candidates(len(v['tokens']));gold={(c,p):label for c,p,label in s.get('edges',[])}
        rows.extend(pair_features(v,c,p,arm) for c,p in pairs);targets.extend(gold.get((c,p),0) for c,p in pairs)
        slices.append([offset,offset+len(pairs)]);pairs_all.append(pairs);offset+=len(pairs)
    return matrix(rows),targets,slices,pairs_all


def edge_metrics(rows,sentences):
    tp=predicted=gold=0
    for row,s in zip(rows,sentences):
        p={tuple(e[:3]) for e in row};g=set(map(tuple,s['edges']));tp+=len(p&g);predicted+=len(p);gold+=len(g)
    return dict(tp=tp,predicted=predicted,gold=gold,precision=tp/predicted if predicted else None,recall=tp/max(1,gold),
        f1=2*tp/max(1,predicted+gold),wilson_lower=wilson_lower(tp,predicted))


def calibrate(consensus_rows,sentences):
    grid=[]
    for threshold in THRESHOLDS:
        for margin in MARGINS:
            metrics=edge_metrics([skeleton(r,threshold,margin) for r in consensus_rows],sentences)
            grid.append(dict(threshold=threshold,margin=margin,**metrics))
    f1=max(grid,key=lambda r:(r['f1'],r['threshold'],r['margin']));operating={'f1':dict(enabled=True,threshold=f1['threshold'],margin=f1['margin'])}
    for target in TARGETS:
        eligible=[r for r in grid if r['predicted']>=20 and r['wilson_lower']>=target]
        best=max(eligible,key=lambda r:(r['recall'],r['precision'],r['threshold'],r['margin'])) if eligible else None
        operating['precision_'+str(target)]=dict(enabled=best is not None,threshold=best['threshold'] if best else 1.1,margin=best['margin'] if best else 1.1)
    return grid,operating


def property_label(s,pos,property):
    value=s['properties'][property][pos]
    if property!='upos':return value
    return 'nominal' if value in ('NOUN','PROPN','PRON','DET','ADJ','NUM') else 'verbal' if value in ('VERB','AUX') else 'function_other'


def readout_key(v,pos,arm):
    word=v['tokens'][pos]
    if arm=='baseline':return str((min(24,v['word_stats']['ranks'][word]),min(24,v['ending_stats']['ranks'][word[-2:]])))
    item=v['distribution'][word];return str((item['word']['cluster'],item['ending']['cluster']))


def fit_readouts(sentences,vv,arm):
    result={}
    for property in ('upos','case','number'):
        counts=defaultdict(Counter);overall=Counter()
        for s,v in zip(sentences,vv):
            for pos in range(len(s['tokens'])):
                label=property_label(s,pos,property)
                if label is None:continue
                counts[readout_key(v,pos,arm)][label]+=1;overall[label]+=1
        majority=lambda c:sorted(c,key=lambda l:(-c[l],l))[0]
        result[property]=dict(mapping={k:majority(c) for k,c in counts.items()},majority=majority(overall),training_counts=dict(overall))
    return result


def run():
    if not OUT.exists():prepare()
    if (OUT/'models.json').exists():raise ValueError('Preserve fitted models')
    data=load(OUT/'datasets.json');lattice=load(OUT/'morphology-lattice.json');raw_train,off=phase_views(data,'train',lattice);raw_tune,tune_off=phase_views(data,'tune',lattice)
    prototypes={name:fit_prototypes(observations(raw_train,shuffle=name=='shuffled_profiles')) for name in ('profiles','shuffled_profiles')}
    models={};calibration={};readouts={};start=time.monotonic()
    for arm in ARMS:
        if arm in prototypes:
            train=attach_profiles(raw_train,prototypes[arm],shuffle=arm=='shuffled_profiles');tune=attach_profiles(raw_tune,prototypes[arm],shuffle=arm=='shuffled_profiles')[tune_off:]
        else:train=raw_train;tune=raw_tune[tune_off:]
        x,y,slices,pairs=relation_matrix(data['train'],train,arm);tx,_,tslices,tpairs=relation_matrix(data['tune'],tune,arm)
        members=[];tune_prob=[];bags=[]
        for seed in SEEDS:
            bag=np.random.default_rng(seed).integers(len(data['train']),size=len(data['train']));indices=np.concatenate([np.arange(*slices[int(i)]) for i in bag]);bags.append(bag.tolist())
            model=fit(x[indices],np.asarray(y)[indices],len(LABELS));members.append(model);tune_prob.append(probabilities(tx,model))
        consensus_rows=[consensus(pair,[p[a:b] for p in tune_prob]) for (a,b),pair in zip(tslices,tpairs)]
        grid,operating=calibrate(consensus_rows,data['tune']);models[arm]=dict(members=members,bags=bags,operating=operating);calibration[arm]=dict(grid=grid,consensus=consensus_rows)
        if arm!='dictionary':readouts[arm]=fit_readouts(data['train'],train,arm)
        save(OUT/f'checkpoint-{arm}.json',models[arm])
        print(arm,'tune F1',round(max(r['f1'] for r in grid),3),'enabled',[k for k,v in operating.items() if v['enabled']],'elapsed',round(time.monotonic()-start,1),flush=True)
    save(OUT/'models.json',models);save(OUT/'prototypes.json',prototypes);save(OUT/'calibration.json',calibration);save(OUT/'readouts.json',readouts)
    paths=[OUT/p for p in ('models.json','prototypes.json','calibration.json','readouts.json','datasets.json','morphology-lattice.json','manifest.json')]
    save(OUT/'fit-freeze.json',dict(inputs={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},elapsed_seconds=time.monotonic()-start))
    print('All representation, readout, model and operating choices frozen before new test scoring.',flush=True)

if __name__=='__main__':run()
