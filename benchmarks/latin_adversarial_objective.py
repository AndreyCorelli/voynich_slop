"""One adversarial objective-training round; frozen fresh optimizer attacks."""
import argparse,hashlib,json,math,random,re
from collections import Counter,defaultdict
from functools import lru_cache
from pathlib import Path
from types import SimpleNamespace
import numpy as np
from benchmarks.latin_relative_search import PARENT,RANK,INDICES,grammatical_metrics
from benchmarks.latin_passage_proxy_audit import chunks
from benchmarks import word_mapping_anchor_recovery as resource
from voynich_smt.data.corpus import digest,write_json
from voynich_smt.latin_sentence_cases import read_conllu,mutate,expected,analyses,PREPOSITIONS
from voynich_smt.word_mapping.corpora import WordStream
from voynich_smt.word_mapping.morphology import WhitakerAnnotator
from voynich_smt.structural_language import StructuralLanguageModel
from voynich_smt.bootstrap_mapping import AgreementModel
from voynich_smt.bootstrap_marginal import MarginalAgreementModel
from voynich_smt.relative_search import PassageScorer
from voynich_smt.relative_ranking import fit_ranker
OUT=Path('experiments/results/latin-adversarial-objective')
NEW=Path('data/latin-grammar-benchmark/proiel-r2.17')
RIDGES=(.001,.01,.1,1.,10.)
STARTS=('truth','control_high','corrupt_low','corrupt_high')
BUDGETS=(100,1000,5000)


def build():
    if (OUT/'dataset.json').exists():raise ValueError('Existing frozen dataset')
    docs=json.loads((PARENT/'dataset.json').read_text());e=json.loads((PARENT/'morphology.json').read_text())['entries'];annotator=WhitakerAnnotator(Path('data/vendor/whitakers-words'))
    def entries(w):
        if w not in e or any('lexeme_id' not in a for a in e[w]):e[w]=annotator.annotate(w)
        return e[w]
    # PROIEL has source comments instead of Perseus newdoc comments.
    corpus=[]
    for path in sorted(NEW.glob('*.conllu')):
        text=path.read_text();blocks=text.split('\n\n');selected=[]
        for block in blocks:
            if '# source = Opus agriculturae,' in block:selected.append(block.replace('# source =','# newdoc id =',1))
        tmp=OUT/'palladius-input.conllu';tmp.parent.mkdir(parents=True,exist_ok=True);tmp.write_text('\n\n'.join(selected)+'\n\n')
        corpus.extend(read_conllu(tmp))
    corpus.sort(key=lambda s:int(s['id']));sentences=[];words=0
    for s in corpus:
        tokens=[t for t in s['tokens'] if t['pos']!='PUNCT']
        if not tokens or any(not re.fullmatch('[a-z]+',t['word']) for t in tokens):continue
        sentences.append({**s,'document':'palladius.opus_agriculturae','tokens':tokens,'words':[t['word'] for t in tokens]});words+=len(tokens)
        if words>=3200:break
    if words<3000:raise ValueError('Insufficient fresh Palladius text')
    _,records=resource.resource_entries();lemma_forms=defaultdict(list)
    for record in records:
        if 'lexeme_id' in record['witness']:lemma_forms[record['witness']['lexeme_id']].append(record['surface'])
    vocab={w for s in sentences for w in s['words']};changes={};occupied=set();witnesses={}
    for i,s in enumerate(sentences):
        row=mutate(s,entries,lemma_forms,2901+i)
        if row:
            for c in row['corruptions']:
                if c['before'] not in changes and c['after'] not in vocab|occupied:
                    changes[c['before']]=c['after'];occupied.add(c['after']);witnesses[c['before']]={**c,'base':s['id']}
    occurrences=defaultdict(list)
    for s in sentences:
        for t in s['tokens']:occurrences[t['word']].append(t)
    pool=defaultdict(set)
    for d in docs:
        for s in d['sentences']:
            for t in s['tokens']:
                if t['pos']=='NOUN':pool[tuple(sorted(expected(t).items()))].add(t['word'])
    controls={};used=set();rng=random.Random(2901)
    target=sum(w in changes for s in sentences for w in s['words']);mass=0
    for word in sorted(occurrences):
        ts=occurrences[word];profiles={tuple(sorted(expected(t).items())) for t in ts}
        if any(t['pos']!='NOUN' for t in ts) or len(profiles)!=1:continue
        profile=next(iter(profiles));ex=dict(profile)
        if not all(k in ex for k in ('Case','Number','Gender')) or mass+len(ts)>target:continue
        options=sorted(pool[profile]-vocab-used);rng.shuffle(options)
        for after in options:
            if any(i['part_of_speech']=='N' and all(i['features'].get(k)==v for k,v in ex.items()) for _,i in analyses(entries,after)):
                controls[word]=after;used.add(after);mass+=len(ts);break
    keys=sorted(changes);rng.shuffle(keys)
    doc={'document':'palladius.opus_agriculturae','split':'test','sentences':sentences,'words':words,'mappings':{'original':{},'corrupt_high':changes,'corrupt_low':{w:changes[w] for w in keys[:max(1,len(keys)//4)]},'control_high':controls},'corruption_witnesses':witnesses};docs.append(doc)
    fixtures=[]
    for d in docs:
        for width in (250,1000):
            blocks=chunks(d['sentences'],width)
            if not blocks:continue
            ss=[d['sentences'][i] for i in blocks[0]];ww=sorted({w for s in ss for w in s['words']});encoding={w:f'c{i:05d}' for i,w in enumerate(ww)};truth={t:w for w,t in encoding.items()};freq=Counter(w for s in ss for w in s['words']);eligible=set(d['mappings']['corrupt_high'])|set(d['mappings']['control_high']);activewords=sorted(eligible&set(ww),key=lambda w:(-freq[w],w))[:24]
            if len(activewords)<2:continue
            fixtures.append({'id':d['document']+'/'+str(width),'document':d['document'],'split':d['split'],'width':width,'sentences':ss,'segments':[[encoding[w] for w in s['words']] for s in ss],'truth':truth,'active':[encoding[w] for w in activewords],'starts':{start:{t:d['mappings'].get(start,{}).get(w,w) if w in activewords else w for t,w in truth.items()} for start in STARTS}})
    # Use dictionary lookup for all scoring vocabulary, with no syntax labels in features.
    training=list(WordStream.load(resource.PARENT/'splits/train.json').segments());counts=Counter(w for s in training for w in s);extra=[w for w,n in sorted(counts.items(),key=lambda x:(-x[1],x[0])) if e.get(w) and all(a['part_of_speech'] in ('N','ADJ','V','VPAR','SUPINE') for a in e[w])][:64]
    for f in fixtures:
        fixed={w for t,w in f['truth'].items() if t not in f['active']};f['pool']=sorted(({f['truth'][t] for t in f['active']}|set(extra)|{mapping[t] for mapping in f['starts'].values() for t in f['active']})-fixed)
        for w in {w for s in f['sentences'] for w in s['words']}|set(f['pool']):entries(w)
        assert all(len(set(m.values()))==len(m) for m in f['starts'].values())
    write_json(OUT/'dataset.json',fixtures);write_json(OUT/'morphology.json',{'entries':e})
    paths=[Path(__file__),Path('src/voynich_smt/relative_search.py'),Path('src/voynich_smt/relative_ranking.py'),Path('benchmarks/latin_relative_search.py'),PARENT/'dataset.json',PARENT/'selection.json',RANK/'selection.json',resource.PARENT/'splits/train.json']+list(NEW.glob('*'))
    protocol={'dataset_sha256':digest(fixtures),'inputs_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths if p.is_file()},'morphology_sha256':hashlib.sha256((OUT/'morphology.json').read_bytes()).hexdigest(),'collection_seed':211,'collection_steps':500,'calibration_attack_seed':503,'calibration_steps':1000,'test_seeds':[907,919],'test_budgets':BUDGETS,'ridge_grid':RIDGES,'models':['linear_nonnegative','linear_signed','quadratic_signed'],'optimizer':'unchanged strict ascent; 25% swaps, 75% injective single replacements; no gold filters','split':'whole works, all runs and mutations of a work together','gate':{'stable_valid_run_fraction':.95,'median_repair_fraction':.5,'corrupt_nonregression_fraction':.8,'budget_nonregression_fraction':.9,'worst_valid_damage_fraction':.01},'scope':'assisted near-truth fixtures; original forms in pool, other assignments fixed; prior test authors reused plus fresh Palladius; gold labels only train/eval, never score inputs'}
    write_json(OUT/'manifest.json',{'protocol':protocol,'sha256':digest(protocol)})
    print('BUILT',len(fixtures),'fixtures; new Palladius',words,'words',len(changes),'corrupt types',flush=True)


class Engine:
    def __init__(self):
        self.fixtures=json.loads((OUT/'dataset.json').read_text());self.e=json.loads((OUT/'morphology.json').read_text())['entries'];self.manifest=json.loads((OUT/'manifest.json').read_text());p=self.manifest['protocol']
        assert digest(p)==self.manifest['sha256'] and digest(self.fixtures)==p['dataset_sha256']
        assert hashlib.sha256((OUT/'morphology.json').read_bytes()).hexdigest()==p['morphology_sha256']
        for path,h in p['inputs_sha256'].items():assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==h
        train=list(WordStream.load(resource.PARENT/'splits/train.json').segments());self.lm=StructuralLanguageModel(self.e).fit(train);self.lm.log_transition=lru_cache(maxsize=500000)(self.lm.log_transition);m=SimpleNamespace(entries=self.e,identity=self.manifest['sha256']);self.agreement=AgreementModel(m);self.marginal=MarginalAgreementModel(m);self.tails=np.asarray(json.loads((PARENT/'selection.json').read_text())['tails'])[INDICES[:4]]
        rank=json.loads((RANK/'selection.json').read_text());self.baselines={name:np.asarray(next(x for x in rank['models'] if x['name']==name)['weights'])[INDICES]/np.asarray(rank['scale'])[INDICES] for name in ('structural_features_signed','structural_features_nonnegative')}
        self.base=lru_cache(maxsize=150000)(self.base)
    def base(self,words):
        n=len(words);v=np.asarray([self.lm.score([words])/n,self.agreement.score([words])/max(1,n-1),self.marginal.score([words])/max(1,n-1),sum(bool(self.e.get(w)) for w in words)/n]);return np.r_[v,-(v<self.tails).astype(float)]
    def passage(self,f,mapping):
        weights=np.asarray([len(s) for s in f['segments']]);values=np.asarray([self.base(tuple(mapping[t] for t in s)) for s in f['segments']]);return np.average(values,axis=0,weights=weights)
    def evaluate(self,f,mapping):return grammatical_metrics(f['sentences'],mapping,f['truth'],self.e)
    def details(self,f,mapping):
        # Inspect each eligible relationship independently by assigning a
        # minimal synthetic token set with the same gold dependency.
        status={};reverse={w:t for t,w in f['truth'].items()}
        for s in f['sentences']:
            byid={t['id']:t for t in s['tokens']};children=defaultdict(list)
            for t in s['tokens']:children[t['head']].append(t)
            for t in s['tokens']:
                related=[]
                if t['pos']=='ADJ' and t['relation']=='amod' and t['head'] in byid:related.append(('adjective',byid[t['head']]))
                if t['pos'] in ('VERB','AUX') and t['features'].get('VerbForm')=='Fin':
                    subs=[a for a in children[t['id']] if a['relation']=='nsubj' and a['pos'] in ('NOUN','PROPN')]
                    if len(subs)==1 and not any(a['relation']=='conj' for a in children[subs[0]['id']]):related.append(('subject',subs[0]))
                if t['pos'] in ('NOUN','PROPN'):
                    pp=[a for a in children[t['id']] if a['relation']=='case' and a['word'] in PREPOSITIONS]
                    if len(pp)==1:related.append(('preposition',pp[0]))
                for family,other in related:
                    small={'tokens':[t,other]};base=grammatical_metrics([small],f['truth'],f['truth'],self.e)
                    if base['eligible_gold_edges']:
                        now=grammatical_metrics([small],mapping,f['truth'],self.e);status[f"{s['id']}:{family}:{other['id']}->{t['id']}"]={'tokens':[reverse[t['word']],reverse[other['word']]],'satisfied':now['satisfied_gold_edges']==now['eligible_gold_edges']}
        return status
    def attack(self,f,start,seed,coef,budget,collect=False,transform=None):
        rng=random.Random(seed);mapping=dict(f['starts'][start]);scorer=PassageScorer(f['segments'],mapping,self.base,coef if transform is None else np.zeros(8));initial=self.evaluate(f,mapping);initial_features=self.passage(f,mapping);logs=[];snapshots=[];worst_edges=0;worst_roles=0;initial_state=dict(mapping)
        def value(v):return float(v@coef) if transform is None else float(transform(v)@coef)
        current=value(scorer.totals/scorer.words);initial_score=current
        def snapshot(step):
            if transform is None:assert math.isclose(scorer.full_score(),scorer.score,abs_tol=1e-7,rel_tol=1e-10)
            assert math.isclose(value(self.passage(f,scorer.mapping)),current,abs_tol=1e-7,rel_tol=1e-10)
            return {'budget':step,'score':current,'grammar':self.evaluate(f,scorer.mapping),'mapping':dict(scorer.mapping),'features':(scorer.totals/scorer.words).tolist(),'worst_high_scoring_edge_loss':worst_edges,'worst_high_scoring_role_loss':worst_roles}
        snapshots.append(snapshot(0));accepted=0
        for step in range(1,budget+1):
            changes=None;t=rng.choice(f['active'])
            if rng.random()<.25:
                other=rng.choice(f['active'])
                if other!=t:changes={t:scorer.mapping[other],other:scorer.mapping[t]}
            else:
                target=rng.choice(f['pool'])
                if target not in scorer.mapping.values():changes={t:target}
            if changes:
                proposal=scorer.propose(changes);candidate=value(proposal.totals/scorer.words)
                if candidate>current+1e-10:
                    before=dict(scorer.mapping);before_features=scorer.totals/scorer.words;bg=self.evaluate(f,before);before_score=current
                    scorer.commit(proposal);current=candidate;accepted+=1;ag=self.evaluate(f,scorer.mapping);worst_edges=max(worst_edges,initial['satisfied_gold_edges']-ag['satisfied_gold_edges']);worst_roles=max(worst_roles,initial['role_inflection_compatible_tokens']-ag['role_inflection_compatible_tokens'])
                    if collect:
                        bd=self.details(f,before);ad=self.details(f,scorer.mapping)
                        lost=[k for k in bd if bd[k]['satisfied'] and not ad[k]['satisfied']];gained=[k for k in bd if not bd[k]['satisfied'] and ad[k]['satisfied']]
                        logs.append({'step':step,'changes':{k:{'before':before[k],'after':v} for k,v in changes.items()},'before_mapping':before,'after_mapping':dict(scorer.mapping),'before_features':before_features.tolist(),'after_features':(scorer.totals/scorer.words).tolist(),'score_change':current-before_score,'before_grammar':bg,'after_grammar':ag,'lost_relationships':lost,'gained_relationships':gained})
            if step in BUDGETS or step==budget:snapshots.append(snapshot(step))
        return {'fixture':f['id'],'document':f['document'],'split':f['split'],'start':start,'seed':seed,'budget':budget,'accepted':accepted,'initial_score':initial_score,'initial_mapping':initial_state,'initial_features':initial_features.tolist(),'snapshots':snapshots,'mutations':logs}


def collect():
    engine=Engine();runs=[]
    for f in engine.fixtures:
        if f['split']=='test':continue
        for name,coef in engine.baselines.items():
            for start in STARTS:
                run=engine.attack(f,start,211,coef,500,True);run['model']=name;runs.append(run)
        print('COLLECTED',f['id'],len(runs),flush=True)
    write_json(OUT/'collection.json',runs)


def expanded(v,center,scale,quadratic):
    x=(np.asarray(v)-center)/scale
    if not quadratic:return x
    return np.r_[x,[x[i]*x[j] for i in range(8) for j in range(i,8)]]


def quality(attack_runs):
    valid=[];repairs=[];nonreg=[];worst=[]
    for r in attack_runs:
        a=r['snapshots'][0]['grammar'];b=r['snapshots'][-1]['grammar'];ed=b['satisfied_gold_edges']-a['satisfied_gold_edges'];rd=b['role_inflection_compatible_tokens']-a['role_inflection_compatible_tokens']
        if r['start'] in ('truth','control_high'):
            valid.append(ed>=0 and rd>=0);worst.append(max(r['snapshots'][-1]['worst_high_scoring_edge_loss']/max(1,a['eligible_gold_edges']),r['snapshots'][-1]['worst_high_scoring_role_loss']/max(1,a['role_inflection_eligible_tokens'])))
        else:
            fractions=[]
            for good,total,d in [(a['satisfied_gold_edges'],a['eligible_gold_edges'],ed),(a['role_inflection_compatible_tokens'],a['role_inflection_eligible_tokens'],rd)]:
                if total>good:fractions.append(d/(total-good))
            if fractions:repairs.append(min(fractions))
            nonreg.append(ed>=0 and rd>=0)
    return {'valid_stability':float(np.mean(valid)),'median_minimum_edge_role_repair':float(np.median(repairs)) if repairs else 0.,'corrupt_nonregression':float(np.mean(nonreg)),'worst_valid_degradation':float(max(worst,default=0))}


def train():
    engine=Engine();runs=json.loads((OUT/'collection.json').read_text());pairs=[];equivalents=[]
    def add(run,before,after,bg,ag,kind):
        de=ag['satisfied_gold_edges']-bg['satisfied_gold_edges'];dr=ag['role_inflection_compatible_tokens']-bg['role_inflection_compatible_tokens']
        if de<=0 and dr<=0 and (de<0 or dr<0):good,bad=before,after
        elif de>=0 and dr>=0 and (de>0 or dr>0):good,bad=after,before
        else:return
        pairs.append({'document':run['document'],'fixture':run['fixture'],'run':f"{run['model']}/{run['start']}/{run['seed']}",'split':run['split'],'kind':kind,'good':good,'bad':bad})
    byfixture={f['id']:f for f in engine.fixtures}
    for run in runs:
        for m in run['mutations']:add(run,m['before_features'],m['after_features'],m['before_grammar'],m['after_grammar'],'mutation')
        first,last=run['snapshots'][0],run['snapshots'][-1];add(run,first['features'],last['features'],first['grammar'],last['grammar'],'endpoint')
        f=byfixture[run['fixture']]
        for goodstart in ('truth','control_high'):
            good=engine.passage(f,f['starts'][goodstart]);gg=engine.evaluate(f,f['starts'][goodstart]);add(run,good.tolist(),last['features'],gg,last['grammar'],'valid_vs_endpoint')
    write_json(OUT/'pairs.json',pairs)
    fitting=[p for p in pairs if p['split']=='fit'];cal=[p for p in pairs if p['split']=='calibration'];originals=[engine.passage(f,f['truth']) for f in engine.fixtures if f['split']=='fit'];center=np.mean(originals,axis=0);scale=np.std(originals,axis=0);scale[scale<1e-8]=1
    models=[]
    for name,quadratic,nonnegative in [('linear_nonnegative',False,True),('linear_signed',False,False),('quadratic_signed',True,False)]:
        diffs=np.asarray([expanded(p['good'],center,scale,quadratic)-expanded(p['bad'],center,scale,quadratic) for p in fitting]);weights=[]
        cells=Counter((p['document'],p['fixture'],p['run'],p['kind']) for p in fitting)
        # Equal mass by work, fixture, run, local/complete example kind.
        for p in fitting:
            fixtures={q['fixture'] for q in fitting if q['document']==p['document']};rr={q['run'] for q in fitting if q['fixture']==p['fixture']};kk={q['kind'] for q in fitting if q['fixture']==p['fixture'] and q['run']==p['run']};weights.append(1/(len(fixtures)*len(rr)*len(kk)*cells[p['document'],p['fixture'],p['run'],p['kind']]))
        for ridge in RIDGES:
            coef=fit_ranker(diffs,weights,ridge,nonnegative);transform=lambda v,q=quadratic:expanded(v,center,scale,q)
            cp=np.asarray([transform(p['good'])-transform(p['bad']) for p in cal])@coef
            attacks=[engine.attack(f,start,503,coef,1000,False,transform) for f in engine.fixtures if f['split']=='calibration' for start in STARTS]
            metrics=quality(attacks);metrics['calibration_pair_accuracy']=float(np.mean(cp>1e-10));models.append({'name':name,'ridge':ridge,'weights':coef.tolist(),'quadratic':quadratic,'calibration':metrics});print('CALIBRATED',name,ridge,metrics,flush=True)
    chosen=max(models,key=lambda m:(m['calibration']['valid_stability'],m['calibration']['median_minimum_edge_role_repair'],-m['calibration']['worst_valid_degradation'],m['calibration']['calibration_pair_accuracy']))
    selection={'manifest_sha256':engine.manifest['sha256'],'collection_sha256':hashlib.sha256((OUT/'collection.json').read_bytes()).hexdigest(),'pairs_sha256':digest(pairs),'center':center.tolist(),'scale':scale.tolist(),'models':models,'chosen':chosen,'fit_pairs':len(fitting),'calibration_pairs':len(cal),'scope':'Selection from calibration attacks only. No test attacks used.'}
    write_json(OUT/'selection.json',selection);print('FROZEN',chosen['name'],chosen['ridge'],flush=True)


def test():
    engine=Engine();selection=json.loads((OUT/'selection.json').read_text());chosen=selection['chosen'];coef=np.asarray(chosen['weights']);center=np.asarray(selection['center']);scale=np.asarray(selection['scale']);transform=lambda v:expanded(v,center,scale,chosen['quadratic']);runs=[]
    models=[('adversarial',coef,transform),('previous_structural_signed',engine.baselines['structural_features_signed'],None)]
    for f in engine.fixtures:
        if f['split']!='test':continue
        for name,w,tr in models:
            for start in STARTS:
                for seed in (907,919):
                    run=engine.attack(f,start,seed,w,5000,False,tr);run['model']=name;runs.append(run)
            print('ATTACKED',f['id'],name,flush=True)
    summaries={}
    for name,_,_ in models:
        local=[r for r in runs if r['model']==name];bybudget=[]
        for budget in BUDGETS:
            partial=[{**r,'snapshots':[r['snapshots'][0],next(s for s in r['snapshots'] if s['budget']==budget)]} for r in local];bybudget.append({'budget':budget,**quality(partial)})
        nonworse=[]
        for r in local:
            a=next(s for s in r['snapshots'] if s['budget']==100)['grammar'];b=r['snapshots'][-1]['grammar'];nonworse.append(b['satisfied_gold_edges']>=a['satisfied_gold_edges'] and b['role_inflection_compatible_tokens']>=a['role_inflection_compatible_tokens'])
        passed=all(q['valid_stability']>=.95 and q['median_minimum_edge_role_repair']>=.5 and q['corrupt_nonregression']>=.8 and q['worst_valid_degradation']<=.01 for q in bybudget) and np.mean(nonworse)>=.9
        fresh=[r for r in local if r['document']=='palladius.opus_agriculturae'];summaries[name]={'budgets':bybudget,'budget_nonregression':float(np.mean(nonworse)),'fresh_palladius':quality(fresh),'gate_passed':bool(passed)}
    report={'manifest_sha256':engine.manifest['sha256'],'selection_sha256':digest(selection),'runs':runs,'summaries':summaries,'scope':'One adversarial round, assisted near-truth search. Old held-out authors plus newly reserved Palladius; no grammar annotation enters scorer. Best archive equals current state under unchanged strict ascent.'}
    if (OUT/'report.json').exists():assert json.loads((OUT/'report.json').read_text())==report;write_json(OUT/'validation.json',{'fresh_attacks_fully_replayed':True,'report_sha256':digest(report)})
    else:write_json(OUT/'report.json',report)
    print('RESULT',summaries,flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['build','collect','train','test']);args=p.parse_args();globals()[args.stage]()
