"""Does grammatical evidence improve discovery of a predictive compact key?"""
import argparse,hashlib,json,math,re,time
from collections import Counter,defaultdict
from pathlib import Path
import numpy as np
import torch
from voynich_smt.letter_discovery import ALPHABET,SPACE,BASE,pattern,encode_text,decode_text,language_model,trie,prepare,gram_positions,initialization,search,full_score
from voynich_smt.latin_sentence_cases import read_conllu,expected
from voynich_smt.data.corpus import write_json,digest
OUT=Path('experiments/results/latin-compact-cipher')
TRAIN=Path('experiments/results/latin-sentence-role/dataset.json')
CORPUS=Path('experiments/results/latin-passage-proxy-audit/dataset.json')
INVENTORY=Path('experiments/results/latin-large-dictionary/forms-100000.jsonl')
ARMS=('baseline','word_candidates','inferred_pos','oracle_pos','oracle_roles')
TAGS=('N','ADJ','V','PREP','PRON','ADV','CONJ','NUM','OTHER')
UD={'NOUN':'N','PROPN':'N','ADJ':'ADJ','VERB':'V','AUX':'V','ADP':'PREP','PRON':'PRON','DET':'PRON','ADV':'ADV','CCONJ':'CONJ','SCONJ':'CONJ','NUM':'NUM'}
RES={'VPAR':'V','SUPINE':'V','PACK':'PRON','TACKON':'OTHER','INTERJ':'OTHER'}


def tag(t):return UD.get(t['pos'],'OTHER')

def load_inventory():
    rows=[json.loads(l) for l in INVENTORY.read_text().splitlines()];rows=[r for r in rows if all(c in ALPHABET for c in r['surface'])];rows.sort(key=lambda r:r['surface']);words=[r['surface'] for r in rows]
    return rows,words


def section(sentences,limit,reverse=False):
    selected=[];total=0
    for s in reversed(sentences) if reverse else sentences:
        selected.append(s);total+=len(s['tokens'])
        if total>=limit:break
    return list(reversed(selected)) if reverse else selected


def build():
    if (OUT/'fixtures.json').exists():raise ValueError('Existing frozen fixtures')
    OUT.mkdir(parents=True,exist_ok=True);docs=json.loads(CORPUS.read_text());paths=[TRAIN,CORPUS,INVENTORY]
    # Read full Palladius work, excluded from training and calibration authors.
    palladius=[]
    for path in sorted(Path('data/latin-grammar-benchmark/proiel-r2.17').glob('*.conllu')):
        paths.append(path);blocks=[b.replace('# source =','# newdoc id =',1) for b in path.read_text().split('\n\n') if '# source = Opus agriculturae,' in b]
        tmp=OUT/'palladius-input.conllu';tmp.write_text('\n\n'.join(blocks)+'\n\n');palladius.extend(read_conllu(tmp))
    palladius.sort(key=lambda s:int(s['id']));clean=[]
    for s in palladius:
        tokens=[t for t in s['tokens'] if t['pos']!='PUNCT']
        if tokens and all(re.fullmatch('[a-z]+',t['word']) for t in tokens):clean.append({**s,'tokens':tokens})
    docs.append({'document':'palladius.opus_agriculturae','split':'test','sentences':clean})
    fixtures=[]
    for d in docs:
        if d['split'] not in ('calibration','test'):continue
        holdout=section(d['sentences'],300,True);holdids={s['id'] for s in holdout}
        for width in (100,300) if d['split']=='calibration' else (100,1000):
            discovery=section(d['sentences'],width)
            if any(s['id'] in holdids for s in discovery) or sum(len(s['tokens']) for s in discovery)<width:continue
            keys=(701,709) if d['split']=='calibration' else (1709,1721,1733)
            for keyseed in keys:
                rng=np.random.default_rng(int(digest((d['document'],keyseed))[:16],16));encryption=rng.permutation(SPACE);decryption=np.argsort(encryption)
                def cipher(ss):return [[ ''.join(ALPHABET[encryption[ALPHABET.index(c)]] for c in t['word']) for t in s['tokens']] for s in ss]
                name=d['document']+'/'+str(width)+'/'+digest((d['document'],keyseed))[:12]
                fixture={'id':name,'document':d['document'],'split':d['split'],'width':width,'discovery':cipher(discovery),'heldout':cipher(holdout)}
                truth={'discovery':discovery,'heldout':holdout,'key':decryption.tolist(),'generation_seed':keyseed};write_json(OUT/'truth'/f'{digest(name)}.json',truth);fixtures.append(fixture)
    # Exact overlap audits: authors and sentence words, including held-out passage.
    train=json.loads(TRAIN.read_text());trainingtexts={tuple(t['word'] for t in s['tokens']) for s in train if s['split']=='fit'}
    for f in fixtures:
        truth=json.loads((OUT/'truth'/f"{digest(f['id'])}.json").read_text());assert not any(tuple(t['word'] for t in s['tokens']) in trainingtexts for s in truth['discovery']+truth['heldout'])
        assert not {s['id'] for s in truth['discovery']}&{s['id'] for s in truth['heldout']}
    write_json(OUT/'fixtures.json',fixtures)
    protocol={'inputs_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},'alphabet':ALPHABET,'cipher_family':'one bijective letter substitution, spaces/word/sentence boundaries preserved; canonical j->i,v->u; no word-specific exceptions','key_description_bits':math.lgamma(SPACE+1)/math.log(2),'heldout_words_target':300,'discovery_widths':{'calibration':[100,300],'test':[100,1000]},'steps_per_restart':10000,'restarts':[17,43],'weights':[0,.03,.1,.3],'arms':ARMS,'ngrams':4,'smoothing':.1,'annealing':'temperature .05 to .001 in repeating 2,000-step cycles; archive best discovery objective; equal initializations across arms','selection':'weight selected by mean calibration heldout letter accuracy; ties prefer zero/smaller weight. Test unopened until selection frozen.','training':'prior author-disjoint fit sources; POS model observes only cipher-invariant shape and local shape context, not target spelling; no function anchors','scope':'first compact-family downstream experiment; existing authors/passages reused from earlier diagnostics; heldout different sentences under same key, not new author; only one cipher family tested'}
    write_json(OUT/'build-manifest.json',protocol);print('BUILT',Counter(f['split'] for f in fixtures),flush=True)


def shape(word):return '.'.join(map(str,pattern(word)))

def features(words,i):
    f=['bias','own:'+shape(words[i]),'length:'+str(len(words[i]))]
    for d in (-3,-2,-1,1,2,3):
        j=i+d
        if 0<=j<len(words):f.extend((str(d)+':'+shape(words[j]),str(d)+':length:'+str(len(words[j]))))
        else:f.append(str(d)+':boundary')
    return f


class ShapePOS:
    def __init__(self,vocabulary,weights):self.vocabulary=vocabulary;self.weights=weights
    def predict(self,words):
        logits=np.asarray([self.weights[[self.vocabulary.get(f,0) for f in features(words,i)]].sum(0) for i in range(len(words))]);logits-=logits.max(1,keepdims=True);p=np.exp(logits);return p/p.sum(1,keepdims=True)


def train_signals():
    torch.set_num_threads(4);torch.manual_seed(4103);sentences=json.loads(TRAIN.read_text());train=[s for s in sentences if s['split']=='fit'];cal=[s for s in sentences if s['split']=='calibration'];counter=Counter(f for s in train for i in range(len(s['tokens'])) for f in features([t['word'] for t in s['tokens']],i));vocab={f:i+1 for i,f in enumerate(sorted(f for f,n in counter.items() if n>=3))}
    x=[];y=[]
    for s in train:
        words=[t['word'] for t in s['tokens']]
        for i,t in enumerate(s['tokens']):fs=features(words,i);x.append([vocab.get(f,0) for f in fs]+[0]*(15-len(fs)));y.append(TAGS.index(tag(t)))
    x=torch.tensor(x);y=torch.tensor(y);layer=torch.nn.Embedding(max(vocab.values())+1,len(TAGS),padding_idx=0);torch.nn.init.zeros_(layer.weight);optimizer=torch.optim.Adam(layer.parameters(),lr=.01);history=[];best=float('inf')
    for epoch in range(1,7):
        losses=[]
        for ids in torch.randperm(len(y)).split(512):
            optimizer.zero_grad();logits=layer(x[ids]).sum(1);loss=torch.nn.functional.cross_entropy(logits,y[ids])+1e-5*layer.weight.square().mean();loss.backward();optimizer.step();losses.append(float(loss.detach()))
        model=ShapePOS(vocab,layer.weight.detach().numpy());nll=correct=n=0
        for s in cal:
            p=model.predict([t['word'] for t in s['tokens']])
            for i,t in enumerate(s['tokens']):j=TAGS.index(tag(t));nll-=float(np.log(max(p[i,j],1e-12)));correct+=int(p[i].argmax())==j;n+=1
        history.append({'epoch':epoch,'train_loss':float(np.mean(losses)),'calibration_nll':nll/n,'calibration_pos_accuracy':correct/n});print('POS',history[-1],flush=True)
        if nll/n<best:best=nll/n;selected=epoch;np.save(OUT/'pos-weights.npy',model.weights.copy())
    write_json(OUT/'pos-model.json',{'vocabulary':vocab,'tags':TAGS,'history':history,'selected_epoch':selected,'training_seed':4103,'training_tokens':len(y),'features':'own/neighbor letter-equality patterns and lengths, 3-word context; substitution-invariant. No lexical target identity.'})
    logs,frequency=language_model([[t['word'] for t in s['tokens']] for s in train]);np.save(OUT/'char-lm.npy',logs);np.save(OUT/'frequency.npy',frequency)
    rows,words=load_inventory();nodes,terminal=trie(words);np.save(OUT/'trie.npy',nodes);np.save(OUT/'trie-terminal.npy',terminal)
    write_json(OUT/'resource.json',{'dictionary_surfaces':len(words),'dictionary_policy':'Previously frozen 100,000 form inventory selected independently of these target authors; exclude non-alphabet words; rule-generated not necessarily attested.','character_training_tokens':sum(len(s['tokens']) for s in train),'char_order':4})


def resource():
    rows,words=load_inventory()
    for row in rows:row['_cached_readings']=readings(row)
    m=json.loads((OUT/'pos-model.json').read_text());return rows,words,ShapePOS(m['vocabulary'],np.load(OUT/'pos-weights.npy')),np.load(OUT/'char-lm.npy'),np.load(OUT/'frequency.npy'),np.load(OUT/'trie.npy'),np.load(OUT/'trie-terminal.npy')


def readings(row):
    if '_cached_readings' in row:return row['_cached_readings']
    return [(RES.get(p,p if p in TAGS else 'OTHER'),dict(fs)) for p,enclitic,fs in row['signatures'] if enclitic is None]

def role_compatible(token,pos,fs):
    if tag(token)!=pos:return False
    e=expected(token);fields=('Case','Number','Gender') if pos in ('N','ADJ') else ('Number','Person') if pos=='V' else ()
    return all(fs.get(k) in (e[k],'X') or (k=='Gender' and fs.get(k)=='C') for k in fields if k in e)


def evidence(f,arm,prepared,rows,posmodel,oracle_discovery=None):
    scores=np.zeros(len(prepared['candidate_ids']),dtype=np.float64);unknown=np.full(len(prepared['unique']),-8.,dtype=np.float64);idx={w:i for i,w in enumerate(prepared['unique'])};prob=defaultdict(list);annotations=defaultdict(list)
    for si,words in enumerate(f['discovery']):
        if arm=='inferred_pos':
            p=posmodel.predict(words)
            for i,w in enumerate(words):prob[w].append(p[i])
        if arm.startswith('oracle'):
            assert oracle_discovery is not None
            for i,w in enumerate(words):annotations[w].append(oracle_discovery[si]['tokens'][i])
    available=[readings(r) for r in rows];wordid={r['surface']:i for i,r in enumerate(rows)};eligible=0
    for w,wi in idx.items():
        if arm=='inferred_pos':p=np.mean(prob[w],axis=0)
        labels=[]
        if arm.startswith('oracle'):
            for t in annotations[w]:
                original=available[wordid[t['word']]] if t['word'] in wordid else []
                if any(role_compatible(t,pos,fs) if arm=='oracle_roles' else tag(t)==pos for pos,fs in original):labels.append(t);eligible+=1
        for k in range(prepared['ptr'][wi],prepared['ptr'][wi+1]):
            candidate=prepared['candidate_ids'][k];rr=available[candidate]
            if arm=='inferred_pos':scores[k]=math.log(max(.01,sum(p[TAGS.index(t)] for t in set(pos for pos,_ in rr))))
            elif arm.startswith('oracle') and labels:scores[k]=float(np.mean([0. if any(role_compatible(t,pos,fs) if arm=='oracle_roles' else tag(t)==pos for pos,fs in rr) else -4. for t in labels]))
    return scores,unknown,{'oracle_eligible_occurrences':eligible}


def metrics(cipher,key,truth_words,truekey):
    predicted=decode_text(cipher,key).split();assert len(predicted)==len(truth_words)
    target=' '.join(truth_words);actual=' '.join(predicted);valid=[i for i,c in enumerate(target) if c!=' ']
    observed=sorted(set(int(c) for c in cipher if c!=SPACE))
    return {'letter_accuracy':sum(actual[i]==target[i] for i in valid)/len(valid),'word_accuracy':sum(a==b for a,b in zip(predicted,truth_words))/len(predicted),'observed_key_accuracy':float(np.mean(key[observed]==np.asarray(truekey)[observed])),'all_key_accuracy':float(np.mean(key==truekey)),'letters':len(valid),'words':len(predicted),'observed_cipher_symbols':len(observed)}


def solve(f,arm,weight,r,truth=None):
    rows,words,posmodel,logs,frequency,nodes,terminal=r;cipher=encode_text(' '.join(w for s in f['discovery'] for w in s));prepared=prepare([w for s in f['discovery'] for w in s],words);positions,counts=gram_positions(cipher,4)
    # Ordinary evidence builder receives no original words/roles/key.
    scores,unknown,info=evidence(f,arm,prepared,rows,posmodel,None if not arm.startswith('oracle') else truth['discovery']);runs=[];best=None
    for seed in (17,43):
        initial=initialization(cipher,frequency,seed);key,value,accepted,trace=search(cipher,initial,logs,4,positions,counts,prepared['words'],prepared['lengths'],prepared['frequency'],nodes,terminal,prepared['ptr'],prepared['candidate_ids'],scores,unknown,prepared['affected_words'],prepared['affected_word_counts'],weight,10000,seed)
        assert np.isclose(value,full_score(cipher,key,logs,4,prepared,nodes,terminal,scores,unknown,weight),atol=1e-7)
        run={'seed':seed,'key':key.tolist(),'objective':float(value),'accepted':int(accepted),'checkpoints':trace.tolist()};runs.append(run)
        if best is None or value>best[0]:best=(value,key.copy())
    # Persist the selected hypothesis before decoding or measuring held-out text.
    key=best[1];hypothesis={'alphabet':ALPHABET,'decryption_permutation':key.tolist(),'exceptions':[],'key_description_bits':math.lgamma(SPACE+1)/math.log(2),'selection':'maximum discovery objective across equal-budget restarts'}
    return {'fixture':f['id'],'arm':arm,'weight':weight,'hypothesis':hypothesis,'runs':runs,'evidence':info},prepared


def evaluate(f,result,truth):
    key=np.asarray(result['hypothesis']['decryption_permutation']);discovery=encode_text(' '.join(w for s in f['discovery'] for w in s));heldout=encode_text(' '.join(w for s in f['heldout'] for w in s))
    result={'discovery':metrics(discovery,key,[t['word'] for s in truth['discovery'] for t in s['tokens']],truth['key']),'heldout':metrics(heldout,key,[t['word'] for s in truth['heldout'] for t in s['tokens']],truth['key'])}
    predicted=decode_text(heldout,key).split();tokens=[t for s in truth['heldout'] for t in s['tokens']]
    for name,positions in [('auxiliary_words',[i for i,t in enumerate(tokens) if t['pos']=='AUX']),('function_words',[i for i,t in enumerate(tokens) if t['pos'] in ('AUX','ADP','PRON','DET','CCONJ','SCONJ','PART')])]:
        result['heldout'][name+'_accuracy']=sum(predicted[i]==tokens[i]['word'] for i in positions)/len(positions) if positions else None
        result['heldout'][name+'_count']=len(positions)
    return result


def calibration():
    r=resource();fixtures=[f for f in json.loads((OUT/'fixtures.json').read_text()) if f['split']=='calibration'];results=[]
    for f in fixtures:
        truth=json.loads((OUT/'truth'/f"{digest(f['id'])}.json").read_text())
        for arm in ARMS:
            for weight in (0,) if arm=='baseline' else (.03,.1,.3):
                solved,_=solve(f,arm,weight,r,truth);solved.update(evaluate(f,solved,truth));results.append(solved)
        print('CALIBRATED',f['id'],flush=True)
    selection={};summaries={}
    for arm in ARMS:
        candidates={0:float(np.mean([x['heldout']['letter_accuracy'] for x in results if x['arm']=='baseline']))}
        if arm!='baseline':
            for weight in (.03,.1,.3):candidates[weight]=float(np.mean([x['heldout']['letter_accuracy'] for x in results if x['arm']==arm and x['weight']==weight]))
        chosen=min(candidates,key=lambda w:(-candidates[w],w));selection[arm]=chosen;summaries[arm]=candidates
    write_json(OUT/'calibration.json',results);write_json(OUT/'selection.json',{'weights':selection,'heldout_calibration_letter_accuracy':summaries,'scope':'Frozen before test evaluation; zero weight uses baseline, not a newly selected key.'})
    paths=[Path(__file__),Path('src/voynich_smt/letter_discovery.py'),OUT/'build-manifest.json',OUT/'fixtures.json',OUT/'pos-weights.npy',OUT/'pos-model.json',OUT/'char-lm.npy',OUT/'frequency.npy',OUT/'trie.npy',OUT/'trie-terminal.npy',OUT/'selection.json',INVENTORY,TRAIN]
    write_json(OUT/'manifest.json',{'files_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}});print('SELECTED',selection,flush=True)


def test(validate=False):
    manifest=json.loads((OUT/'manifest.json').read_text())
    for p,h in manifest['files_sha256'].items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h,p
    r=resource();fixtures=[f for f in json.loads((OUT/'fixtures.json').read_text()) if f['split']=='test'];selection=json.loads((OUT/'selection.json').read_text())['weights'];results=[]
    for f in fixtures:
        # Oracle labels are a separately identified answer-supplied diagnostic.
        truth=json.loads((OUT/'truth'/f"{digest(f['id'])}.json").read_text())
        for arm in ARMS:
            solved,prepared=solve(f,arm,selection[arm],r,truth)
            path=OUT/'frozen-hypotheses'/f"{digest((f['id'],arm))}.json"
            if validate:assert json.loads(path.read_text())==solved
            else:write_json(path,solved)
            original=json.loads(path.read_text());scored=evaluate(f,original,truth);assert original==json.loads(path.read_text());solved.update(scored);results.append(solved)
        print('TESTED',f['id'],flush=True)
    summary={}
    for arm in ARMS:
        rr=[x for x in results if x['arm']==arm];summary[arm]={'weight':selection[arm],'mean_heldout_letter_accuracy':float(np.mean([x['heldout']['letter_accuracy'] for x in rr])),'mean_heldout_word_accuracy':float(np.mean([x['heldout']['word_accuracy'] for x in rr])),'perfect_heldout_runs':sum(x['heldout']['letter_accuracy']==1 for x in rr),'fixtures':len(rr),'widths':{str(width):float(np.mean([x['heldout']['letter_accuracy'] for x in rr if next(f for f in fixtures if f['id']==x['fixture'])['width']==width])) for width in (100,1000)}}
    report={'runs':results,'summary':summary,'scope':'One compact letter-permutation family; no word-specific exceptions; grammar usefulness measured by frozen-key heldout decryption. POS is pattern-based, oracle roles not supplied to ordinary arms. No learned/joint dependency decoder tested.'}
    if validate:assert json.loads((OUT/'report.json').read_text())==report;write_json(OUT/'validation.json',{'frozen_hypotheses_searches_and_heldout_metrics_replayed':True})
    else:write_json(OUT/'report.json',report)
    print('RESULT',summary,flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['build','train','calibrate','test','validate']);a=p.parse_args();{'build':build,'train':train_signals,'calibrate':calibration,'test':test,'validate':lambda:test(True)}[a.stage]()
