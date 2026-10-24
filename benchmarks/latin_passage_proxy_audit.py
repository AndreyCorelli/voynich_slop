"""Frozen passage aggregation audit; no dictionary optimization in this run."""
import argparse,hashlib,json,math,random,re
from collections import Counter,defaultdict
from pathlib import Path
from types import SimpleNamespace
import numpy as np
from benchmarks.latin_sentence_proxy_cases import DATA,OUT as SENTENCE
from benchmarks.latin_sentence_proxy_combination import FEATURES,REGULARIZATIONS
from benchmarks.word_mapping_neural_model import DEFAULT_MODEL
from benchmarks import word_mapping_anchor_recovery as resource
from voynich_smt.data.corpus import digest,write_json
from voynich_smt.latin_sentence_cases import read_conllu,SPLITS,expected,analyses
from voynich_smt.word_mapping.morphology import WhitakerAnnotator
from voynich_smt.word_mapping.corpora import WordStream
from voynich_smt.word_mapping.ngram import NgramModel,NgramConfig
from voynich_smt.structural_language import StructuralLanguageModel
from voynich_smt.bootstrap_mapping import AgreementModel
from voynich_smt.bootstrap_marginal import MarginalAgreementModel
from voynich_smt.neural_scoring import WholeWordScorer
from voynich_smt.proxy_combination import fit_linear,threshold,evaluate
OUT=Path('experiments/results/latin-passage-proxy-audit')

def build():
    if (OUT/'dataset.json').exists():raise ValueError('Dataset already frozen')
    rows=[s for p in sorted(DATA.glob('*.conllu')) for s in read_conllu(p)]
    docs=defaultdict(list)
    for s in rows:
        if s['document'].split('.')[0] not in SPLITS:continue
        tokens=[t for t in s['tokens'] if t['pos']!='PUNCT']
        if tokens and all(re.fullmatch('[a-z]+',t['word']) for t in tokens):docs[s['document']].append({**s,'tokens':tokens,'words':[t['word'] for t in tokens]})
    e=json.loads((SENTENCE/'morphology.json').read_text())['entries'];annotator=WhitakerAnnotator(Path('data/vendor/whitakers-words'))
    def entries(w):
        if w not in e or any('lexeme_id' not in a for a in e[w]):e[w]=annotator.annotate(w)
        return e[w]
    pool=defaultdict(set)
    for s in rows:
        for t in s['tokens']:
            ex=expected(t)
            if t['pos']=='NOUN' and all(k in ex for k in ('Case','Number','Gender')) and re.fullmatch('[a-z]+',t['word']):pool[tuple(sorted(ex.items()))].add(t['word'])
    prior=json.loads((SENTENCE/'cases.json').read_text());all_docs=[]
    for number,(doc,sentences) in enumerate(sorted(docs.items())):
        rng=random.Random(1711+number);counts=Counter(w for s in sentences for w in s['words']);vocab=set(counts)
        proposals=defaultdict(list)
        for r in prior:
            if r['document']==doc and not r['valid'] and r['after'] not in vocab:proposals[r['before']].append(r)
        changes={};used=set();witnesses={}
        for word in sorted(proposals):
            options=sorted(proposals[word],key=lambda r:r['after']);rng.shuffle(options)
            for r in options:
                if r['after'] not in used:
                    changes[word]=r['after'];used.add(r['after']);witnesses[word]=r;break
        keys=sorted(changes);rng.shuffle(keys)
        lowkeys=keys[:max(1,len(keys)//4)]
        mappings={'original':{},'corrupt_low':{w:changes[w] for w in lowkeys},'corrupt_high':changes}
        occurrences=defaultdict(list)
        for s in sentences:
            for t in s['tokens']:occurrences[t['word']].append(t)
        # Every occurrence must be a noun with the same annotated morphology.
        controls={};occupied=set()
        for word in sorted(occurrences):
            ts=occurrences[word];profiles={tuple(sorted(expected(t).items())) for t in ts}
            if any(t['pos']!='NOUN' for t in ts) or len(profiles)!=1:continue
            profile=next(iter(profiles));ex=dict(profile)
            if not all(k in ex for k in ('Case','Number','Gender')):continue
            candidates=sorted(pool[profile]-vocab-occupied);rng.shuffle(candidates)
            for target in candidates:
                aa=analyses(entries,target)
                if any(i['part_of_speech']=='N' and all(i['features'].get(k)==v for k,v in ex.items()) for a,i in aa) and not {t['lemma'] for t in ts}&{t['lemma'] for s in rows for t in s['tokens'] if t['word']==target}:
                    controls[word]=target;occupied.add(target);break
        controlkeys=sorted(controls);rng.shuffle(controlkeys)
        for tier in ('low','high'):
            target=sum(counts[w] for w in mappings['corrupt_'+tier]);selected={};mass=0
            for w in controlkeys:
                if mass+counts[w]<=target:
                    selected[w]=controls[w];mass+=counts[w]
            mappings['control_'+tier]=selected
        for mapping in mappings.values():
            assert len(set(mapping.values()))==len(mapping) and not set(mapping.values())&vocab
        all_docs.append({'document':doc,'split':SPLITS[doc.split('.')[0]],'sentences':sentences,'mappings':mappings,'corruption_witnesses':witnesses,'token_counts':{f:sum(counts[w] for w in m) for f,m in mappings.items()},'words':sum(counts.values())})
        print('built',doc,sum(counts.values()),len(changes),all_docs[-1]['token_counts'],flush=True)
    for d in all_docs:
        for s in d['sentences']:
            for w in s['words']:entries(w)
        for m in d['mappings'].values():
            for w in m.values():entries(w)
    # Earlier search-selected mapping, transferred only as an unlabeled stress control.
    pp=Path('experiments/results/word-mapping/widening-calibration')
    truth=json.loads((pp/'truth/fit-32000.json').read_text());forms=json.loads((pp/'candidates-oracle.json').read_text())['forms']
    saved=Path('experiments/results/word-mapping/zero-corruption-calibration/runs/32000/greedy/seed-101/report.json');run=json.loads(saved.read_text())
    print('truth keys',truth.keys(),flush=True)
    decoding=truth['decoding'];transfer={w:forms[run['best_assignments'][cipher]] for cipher,w in decoding.items() if forms[run['best_assignments'][cipher]]!=w}
    for d in all_docs:
        if d['split']=='test':
            vocabulary={w for s in d['sentences'] for w in s['words']};mapping={w:t for w,t in transfer.items() if w in vocabulary}
            d['mappings']['optimizer_transfer']=mapping
            for w in mapping.values():entries(w)
    write_json(OUT/'dataset.json',all_docs);write_json(OUT/'morphology.json',{'entries':e})
    protocol={'seed':1711,'widths':[250,1000,'whole_work'],'splits':SPLITS,'features':FEATURES,'passage_features':'token weighted proxy means; negative low-tail rates relative to fit-original sentence 10th percentiles; earlier sentence-combination acceptance rate','regularizations':REGULARIZATIONS,'labels':'original and globally morphology-preserving noun mappings positive; globally applied witnessed inflection violations negative; optimizer transfer unlabeled stress test','injective_generated_maps':True,'tail_threshold_fit_only':True,'reliability_gate':{'balanced_accuracy':.95,'paired_accuracy':.95,'control_acceptance':.95},'dataset_sha256':digest(all_docs),'morphology_sha256':hashlib.sha256((OUT/'morphology.json').read_bytes()).hexdigest(),'source_optimizer_sha256':hashlib.sha256(saved.read_bytes()).hexdigest(),'source_sentence_selection_sha256':hashlib.sha256((SENTENCE/'selection.json').read_bytes()).hexdigest(),'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    write_json(OUT/'manifest.json',{'protocol':protocol,'sha256':digest(protocol)})

def chunks(sentences,width):
    if width=='whole_work':return [list(range(len(sentences)))]
    result=[];current=[];n=0
    for i,s in enumerate(sentences):
        current.append(i);n+=len(s['words'])
        if n>=width:result.append(current);current=[];n=0
    return result

def run():
    docs=json.loads((OUT/'dataset.json').read_text());manifest=json.loads((OUT/'manifest.json').read_text());p=manifest['protocol']
    assert digest(docs)==p['dataset_sha256'] and digest(p)==manifest['sha256']
    assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest()==p['code_sha256']
    e=json.loads((OUT/'morphology.json').read_text())['entries'];train=list(WordStream.load(resource.PARENT/'splits/train.json').segments())
    neural=WholeWordScorer.load(DEFAULT_MODEL/'inference',batch_size=16,threads=4)
    bigram=NgramModel.train(train,NgramConfig(bigram_weight=1.,trigram_weight=0.));trigram=NgramModel.train(train,NgramConfig(bigram_weight=0.,trigram_weight=1.))
    structural=StructuralLanguageModel(e).fit(train);morph=SimpleNamespace(entries=e,identity=digest(p['morphology_sha256']));agreement=AgreementModel(morph);marginal=MarginalAgreementModel(morph)
    counts=Counter(w for s in train for w in s);total=sum(counts.values());vocab=len(counts)+1
    cache={}
    # Reuse identical earlier scores only where all statistical resources match;
    # expanded morphology can change scores, so recompute everything here.
    def score(words):
        key=tuple(words)
        if key not in cache:
            # Long sentences are split consistently into <=64-word local contexts.
            parts=[key[i:i+64] for i in range(0,len(key),64)];n=len(key);a=[neural.segment(part).totals() for part in parts]
            cache[key]=[sum(x['word_normalized_log_sum'] for x in a)/n,sum(x['word_masked_log_sum'] for x in a)/n,sum(math.log((counts[w]+.1)/(total+.1*vocab)) for w in key)/n,bigram.score([key]).log_likelihood/n,trigram.score([key]).log_likelihood/n,structural.score([key])/n,agreement.score([key])/max(1,n-1),marginal.score([key])/max(1,n-1),sum(bool(e.get(w)) for w in key)/n]
        return cache[key]
    selection=json.loads((SENTENCE/'selection.json').read_text());old=selection['candidates'][0]
    def sentence_values(split):
        result=[]
        for d in docs:
            if d['split']!=split:continue
            path=OUT/'sentences'/f"{d['document']}.json"
            if path.exists():saved=json.loads(path.read_text());result.append((d,saved));continue
            saved={}
            for family,mapping in d['mappings'].items():
                saved[family]=[]
                for i,s in enumerate(d['sentences']):
                    saved[family].append(score([mapping.get(w,w) for w in s['words']]))
                    if (i+1)%100==0:print('scored',split,d['document'],family,i+1,flush=True)
            write_json(path,saved);result.append((d,saved));print('finished',split,d['document'],flush=True)
        return result
    fit=sentence_values('fit');cal=sentence_values('calibration')
    tails=np.quantile(np.concatenate([np.asarray(v['original']) for d,v in fit]),.1,axis=0)
    def aggregate(groups):
        rows=[]
        for d,v in groups:
            weights=np.asarray([len(s['words']) for s in d['sentences']])
            for width in p['widths']:
                for ci,idx in enumerate(chunks(d['sentences'],width)):
                    for family,values in v.items():
                        if family!='original' and not any(w in d['mappings'][family] for i in idx for w in d['sentences'][i]['words']):continue
                        witnessed=sum(r['base'] in {d['sentences'][i]['id'] for i in idx} for word,r in d['corruption_witnesses'].items() if word in d['mappings'][family])
                        if family.startswith('corrupt_') and not witnessed:continue
                        x=np.asarray(values)[idx];w=weights[idx];means=np.average(x,axis=0,weights=w);rates=-np.average(x<tails,axis=0,weights=w)
                        oldscore=((x-np.asarray(selection['mean']))/np.asarray(selection['scale']))@np.asarray(old['parameters'][:-1])+old['parameters'][-1]
                        acceptance=float(np.average(oldscore>=old['threshold'],weights=w))
                        rows.append({'id':f"{d['document']}/{width}/{ci}/{family}",'base':f"{d['document']}/{width}/{ci}",'document':d['document'],'split':d['split'],'width':width,'family':family,'valid':family in ('original','control_low','control_high'),'words':int(w.sum()),'changed_tokens':sum(word in d['mappings'][family] for i in idx for word in d['sentences'][i]['words']),'witnessed_violations':witnessed,'features':[*means,*rates,acceptance]})
        return rows
    fr=aggregate(fit);cr=aggregate(cal);x=np.asarray([r['features'] for r in fr]);cx=np.asarray([r['features'] for r in cr]);mean=x.mean(0);scale=x.std(0);scale[scale<1e-10]=1;x=(x-mean)/scale;cx=(cx-mean)/scale
    models=[]
    for nonnegative in (True,False):
        trials=[]
        for ridge in REGULARIZATIONS:
            w=fit_linear(x,[r['valid'] for r in fr],ridge,nonnegative);scores=cx@w[:-1]+w[-1];t=threshold(scores,np.asarray([r['valid'] for r in cr]));metrics=evaluate(cr,scores,t);trials.append({'parameters':w.tolist(),'threshold':t,'ridge':ridge,'calibration':metrics})
        best=max(trials,key=lambda r:(r['calibration']['balanced_accuracy'],r['calibration']['paired_accuracy'],-r['ridge']))
        models.append({'name':'passage_nonnegative' if nonnegative else 'passage_signed',**best})
    for i,name in enumerate(FEATURES+['low_tail_'+f for f in FEATURES]+['sentence_acceptance_rate']):
        w=np.zeros(20);w[i]=1;sc=cx[:,i];t=threshold(sc,np.asarray([r['valid'] for r in cr]));models.append({'name':name,'parameters':w.tolist(),'threshold':t,'calibration':evaluate(cr,sc,t)})
    frozen={'manifest_sha256':manifest['sha256'],'tails':tails.tolist(),'mean':mean.tolist(),'scale':scale.tolist(),'models':models,'best_single':max(models[2:],key=lambda m:(m['calibration']['balanced_accuracy'],m['calibration']['paired_accuracy']))['name']}
    if (OUT/'selection.json').exists():assert json.loads((OUT/'selection.json').read_text())==frozen
    else:write_json(OUT/'selection.json',frozen)
    print('SELECTION FROZEN',[(m['name'],m['calibration']['balanced_accuracy']) for m in models[:2]],frozen['best_single'],flush=True)
    tr=aggregate(sentence_values('test'));allrows=fr+cr+tr;write_json(OUT/'passages.json',allrows)
    results=[]
    for model in models:
        records=[]
        for width in p['widths']:
            rr=[r for r in tr if r['width']==width and r['family']!='optimizer_transfer'];z=(np.asarray([r['features'] for r in rr])-mean)/scale;w=np.asarray(model['parameters']);scores=z@w[:-1]+w[-1];metrics=evaluate(rr,scores,model['threshold'])
            bydoc={}
            for doc in sorted({r['document'] for r in rr}):
                ii=[i for i,r in enumerate(rr) if r['document']==doc];bydoc[doc]=evaluate([rr[i] for i in ii],scores[ii],model['threshold'])
            records.append({'width':width,'metrics':metrics,'by_document':bydoc,'predictions':[{'id':r['id'],'score':float(s),'predicted_valid':bool(s>=model['threshold'])} for r,s in zip(rr,scores)]})
        stress=[]
        for row in tr:
            if row['family']=='optimizer_transfer':
                z=(np.asarray(row['features'])-mean)/scale;w=np.asarray(model['parameters']);value=float(z@w[:-1]+w[-1]);base=next(r for r in tr if r['base']==row['base'] and r['family']=='original');bv=float(((np.asarray(base['features'])-mean)/scale)@w[:-1]+w[-1]);stress.append({'id':row['id'],'words':row['words'],'changed_tokens':row['changed_tokens'],'score':value,'original_score':bv,'original_preferred':bv>value+1e-10})
        results.append({'name':model['name'],'lengths':records,'optimizer_transfer_unlabeled':stress})
    report={'manifest_sha256':manifest['sha256'],'selection_sha256':digest(frozen),'passages_sha256':digest(allrows),'document_counts':dict(Counter(d['split'] for d in docs)),'documents':[{'document':d['document'],'split':d['split'],'words':d['words'],'changed_tokens':d['token_counts']} for d in docs],'results':results,'warning':'Exploratory reuse of earlier benchmark authors; at most four test works. Nested lengths and variants correlated. Optimizer transfer is not a certified grammatical corruption.'}
    write_json(OUT/'report.json',report)
    for m in results[:2]+[next(x for x in results if x['name']==frozen['best_single'])]:print('RESULT',m['name'],[(x['width'],x['metrics']['balanced_accuracy'],x['metrics']['paired_accuracy']) for x in m['lengths']],flush=True)
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--build',action='store_true');args=a.parse_args();build() if args.build else run()
