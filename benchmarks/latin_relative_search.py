"""Near-truth dictionary search audit using frozen structural pair rankers."""
import argparse,hashlib,json,math,random
from collections import Counter,defaultdict
from functools import lru_cache
from pathlib import Path
from types import SimpleNamespace
import numpy as np
from benchmarks.latin_passage_proxy_audit import OUT as PARENT,chunks
from benchmarks import word_mapping_anchor_recovery as resource
from voynich_smt.data.corpus import digest,write_json
from voynich_smt.latin_sentence_cases import expected,analyses,PREPOSITIONS
from voynich_smt.word_mapping.corpora import WordStream
from voynich_smt.structural_language import StructuralLanguageModel
from voynich_smt.bootstrap_mapping import AgreementModel
from voynich_smt.bootstrap_marginal import MarginalAgreementModel
from voynich_smt.relative_search import PassageScorer
OUT=Path('experiments/results/latin-relative-search')
RANK=Path('experiments/results/latin-relative-ranking')
SEEDS=(11,29);STEPS=1000;ACTIVE_LIMIT=24;EXTRA_POOL=64
INDICES=[5,6,7,8,14,15,16,17]


def grammatical_metrics(sentences,mapping,truth,entries):
    # Dictionary ambiguity is allowed. Each edge is independently existential;
    # this is an upper bound, not an inferred globally consistent parse.
    signatures={}
    def domain(word,pos):
        key=(word,pos)
        if key not in signatures:
            signatures[key]=[i['features'] for a,i in analyses(lambda w:entries.get(w,[]),word) if i['part_of_speech']==pos]
        return signatures[key]
    translate={'NOUN':'N','PROPN':'N','ADJ':'ADJ','VERB':'V','AUX':'V'}
    token_good=token_total=edge_good=edge_total=0;family=defaultdict(lambda:[0,0])
    token_of_word={w:t for t,w in truth.items()}
    for sentence in sentences:
        byid={t['id']:t for t in sentence['tokens']};children=defaultdict(list)
        for t in sentence['tokens']:children[t['head']].append(t)
        def ds(t,decoded):
            return domain(mapping[token_of_word[t['word']]] if decoded else t['word'],translate.get(t['pos'],'?'))
        def compatible(a,b,fields):
            return all(a.get(k) not in (None,'X') and b.get(k) not in (None,'X') and (a[k]==b[k] or k=='Gender' and {a[k],b[k]}<={'C','M','F'} and 'C' in {a[k],b[k]}) for k in fields)
        for t in sentence['tokens']:
            ex=expected(t);pos=translate.get(t['pos']);keys=('Case','Number','Gender') if pos in ('N','ADJ') else ('Number','Person')
            required={k:ex[k] for k in keys if k in ex}
            if pos and required and any(all(a.get(k)==v for k,v in required.items()) for a in ds(t,False)):
                token_total+=1;token_good+=any(all(a.get(k)==v for k,v in required.items()) for a in ds(t,True))
            constraints=[]
            if t['pos']=='ADJ' and t['relation']=='amod' and t['head'] in byid and byid[t['head']]['pos'] in ('NOUN','PROPN'):
                constraints.append(('adjective_agreement',byid[t['head']],('Case','Number','Gender'),None))
            if t['pos'] in ('VERB','AUX') and t['features'].get('VerbForm')=='Fin':
                subjects=[s for s in children[t['id']] if s['relation']=='nsubj' and s['pos'] in ('NOUN','PROPN')]
                if len(subjects)==1 and not any(c['relation']=='conj' for c in children[subjects[0]['id']]):constraints.append(('subject_agreement',subjects[0],('Number',),None))
            if t['pos'] in ('NOUN','PROPN'):
                pp=[p for p in children[t['id']] if p['relation']=='case' and p['word'] in PREPOSITIONS]
                if len(pp)==1:constraints.append(('preposition_case',None,(),PREPOSITIONS[pp[0]['word']]))
            for name,other,fields,governed in constraints:
                def passed(decoded):
                    aa=ds(t,decoded)
                    if governed:return any(a.get('Case')==governed for a in aa)
                    return any(compatible(a,b,fields) for a in aa for b in ds(other,decoded))
                if passed(False):
                    edge_total+=1;ok=passed(True);edge_good+=ok;family[name][0]+=int(ok);family[name][1]+=1
    return {'role_inflection_compatible_tokens':token_good,'role_inflection_eligible_tokens':token_total,'role_inflection_accuracy':token_good/max(1,token_total),'satisfied_gold_edges':edge_good,'eligible_gold_edges':edge_total,'gold_edge_accuracy':edge_good/max(1,edge_total),'edge_families':dict(family)}


def run(validate=False):
    paths=[PARENT/'dataset.json',PARENT/'morphology.json',PARENT/'selection.json',RANK/'selection.json',resource.PARENT/'splits/train.json',Path(__file__),Path('src/voynich_smt/relative_search.py')]
    protocol={'inputs_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},'seeds':SEEDS,'steps':STEPS,'active_limit':ACTIVE_LIMIT,'extra_pool':EXTRA_POOL,'widths':[250,1000,'whole_work'],'models':['structural_features_signed','structural_features_nonnegative','morphological_sequence'],'starts':['truth','corrupt_low','corrupt_high','control_high'],'policy':'strict ascent, 25% injective pair swaps, 75% single replacement','scope':'oracle near-truth stress test; active selection from known corruption/control types, true forms in pool, other dictionary assignments fixed; gold metrics never used in proposals or score'}
    manifest={'protocol':protocol,'sha256':digest(protocol)}
    if (OUT/'manifest.json').exists():assert validate and json.loads((OUT/'manifest.json').read_text())==json.loads(json.dumps(manifest))
    else:write_json(OUT/'manifest.json',manifest)
    docs=json.loads((PARENT/'dataset.json').read_text());e=json.loads((PARENT/'morphology.json').read_text())['entries'];rank=json.loads((RANK/'selection.json').read_text());tails=np.asarray(json.loads((PARENT/'selection.json').read_text())['tails'])[INDICES[:4]]
    training=list(WordStream.load(resource.PARENT/'splits/train.json').segments());structural=StructuralLanguageModel(e).fit(training);structural.log_transition=lru_cache(maxsize=500000)(structural.log_transition)
    m=SimpleNamespace(entries=e,identity=digest(protocol['inputs_sha256']));agreement=AgreementModel(m);marginal=MarginalAgreementModel(m)
    counts=Counter(w for s in training for w in s)
    extra=[w for w,n in sorted(counts.items(),key=lambda x:(-x[1],x[0])) if e.get(w) and all(a['part_of_speech'] in ('N','ADJ','V','VPAR','SUPINE') for a in e[w])][:EXTRA_POOL]
    models={name:np.asarray(next(x for x in rank['models'] if x['name']==name)['weights'])[INDICES]/np.asarray(rank['scale'])[INDICES] for name in protocol['models'][:2]}
    models['morphological_sequence']=np.r_[1.,np.zeros(7)]
    @lru_cache(maxsize=100000)
    def features(words):
        n=len(words);values=np.asarray([structural.score([words])/n,agreement.score([words])/max(1,n-1),marginal.score([words])/max(1,n-1),sum(bool(e.get(w)) for w in words)/n]);return np.r_[values,-(values<tails).astype(float)]
    results=[];fixtures=[]
    for doc in docs:
        if doc['split']!='test':continue
        for width in protocol['widths']:
            groups=chunks(doc['sentences'],width)
            if not groups:continue
            sentences=[doc['sentences'][i] for i in groups[0]];words=sorted({w for s in sentences for w in s['words']});encoding={w:f'c{i:05d}' for i,w in enumerate(words)};truth={encoding[w]:w for w in words};segments=[[encoding[w] for w in s['words']] for s in sentences];frequencies=Counter(w for s in sentences for w in s['words'])
            eligible=set(doc['mappings']['corrupt_high'])|set(doc['mappings']['control_high']);active_words=sorted(eligible&set(words),key=lambda w:(-frequencies[w],w))[:ACTIVE_LIMIT];active=[encoding[w] for w in active_words]
            if len(active)<2:continue
            fixed={w for w in words if w not in active_words};pool=sorted((set(active_words)|set(extra)|{m[w] for f,m in doc['mappings'].items() if f in ('corrupt_low','corrupt_high','control_high') for w in active_words if w in m})-fixed)
            fid=f"{doc['document']}/{width}";fixtures.append({'id':fid,'words':sum(map(len,segments)),'active_types':len(active),'candidate_forms':len(pool),'truth':truth,'segments':segments,'active':active,'pool':pool})
            for name,coef in models.items():
                for start in protocol['starts']:
                    mapping={token:doc['mappings'].get(start,{}).get(word,word) if token in active else word for token,word in truth.items()};initial_grammar=grammatical_metrics(sentences,mapping,truth,e)
                    for seed in SEEDS:
                        rng=random.Random(seed);scorer=PassageScorer(segments,mapping,features,coef);initial_score=scorer.score;accepted=0;trace=[];first_damage=None
                        def snapshot(step):
                            assert math.isclose(scorer.full_score(),scorer.score,abs_tol=1e-7,rel_tol=1e-10)
                            grammar=grammatical_metrics(sentences,scorer.mapping,truth,e)
                            return {'step':step,'score':scorer.score,'exact_tokens':sum(frequencies[word] for token,word in truth.items() if scorer.mapping[token]==word),'grammar':grammar}
                        trace.append(snapshot(0))
                        for step in range(1,STEPS+1):
                            token=rng.choice(active)
                            if rng.random()<.25:
                                other=rng.choice(active)
                                if other==token:continue
                                changes={token:scorer.mapping[other],other:scorer.mapping[token]}
                            else:
                                target=rng.choice(pool)
                                if target in scorer.mapping.values():continue
                                changes={token:target}
                            proposal=scorer.propose(changes)
                            if proposal.score>scorer.score+1e-10:
                                scorer.commit(proposal);accepted+=1
                                if start in ('truth','control_high') and first_damage is None:
                                    mm=grammatical_metrics(sentences,scorer.mapping,truth,e)
                                    if mm['satisfied_gold_edges']<initial_grammar['satisfied_gold_edges'] or mm['role_inflection_compatible_tokens']<initial_grammar['role_inflection_compatible_tokens']:first_damage={'step':step,'changes':changes,'grammar':mm,'score':scorer.score}
                            if step in (100,500,STEPS):trace.append(snapshot(step))
                        final=snapshot(STEPS)
                        row={'fixture':fid,'model':name,'start':start,'seed':seed,'steps':STEPS,'accepted':accepted,'score_gain':scorer.score-initial_score,'trace':trace,'first_structural_damage':first_damage,'initial_grammar':initial_grammar,'final_grammar':final['grammar'],'final_mapping':scorer.mapping,'token_recovery':final['exact_tokens']/sum(map(len,segments))}
                        results.append(row)
                    print('finished',fid,name,start,'edges',initial_grammar['satisfied_gold_edges'],'->',[x['final_grammar']['satisfied_gold_edges'] for x in results[-2:]],flush=True)
    report={'manifest_sha256':manifest['sha256'],'fixtures':fixtures,'runs':results,'segment_feature_cache':features.cache_info()._asdict(),'evaluation_scope':'Gold-edge existential agreement/government and original-role inflection compatibility; not inferred dependency trees, verb valency, meaning or unrestricted decryption.'}
    if validate:
        saved=json.loads((OUT/'report.json').read_text());assert saved==report;write_json(OUT/'validation.json',{'full_search_replayed':True,'report_sha256':digest(report)})
    else:write_json(OUT/'report.json',report)
    print('COMPLETE',len(fixtures),'fixtures',len(results),'runs',features.cache_info(),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--validate',action='store_true');run(p.parse_args().validate)
