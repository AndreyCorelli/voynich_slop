"""Freeze author-disjoint annotated sentence pairs and grammar-preserving controls."""
from collections import Counter,defaultdict
import hashlib
import json
from pathlib import Path
import random
from benchmarks import word_mapping_anchor_recovery as resource
from voynich_smt.data.corpus import digest,write_json
from voynich_smt.latin_sentence_cases import read_conllu,mutate,expected,analyses,SPLITS,KNOWN
from voynich_smt.word_mapping.morphology import WhitakerAnnotator

DATA=Path('data/latin-grammar-benchmark/perseus-r2.17')
OUT=Path('experiments/results/latin-sentence-proxy-calibration')

def build():
    if (OUT/'cases.json').exists():raise ValueError('Existing frozen cases')
    base_entries,records=resource.resource_entries();cache=dict(base_entries)
    annotator=WhitakerAnnotator(Path('data/vendor/whitakers-words'))
    def entries(word):
        if word not in cache or any('lexeme_id' not in entry for entry in cache[word]):cache[word]=annotator.annotate(word)
        return cache[word]
    lemma_forms=defaultdict(list)
    for r in records:
        if 'lexeme_id' in r['witness']:lemma_forms[r['witness']['lexeme_id']].append(r['surface'])
    sources=[p for p in sorted(DATA.glob('*.conllu'))];sentences=[s for p in sources for s in read_conllu(p)]
    assert len({s['id'] for s in sentences})==len(sentences)
    rng=random.Random(1207);rng.shuffle(sentences);counts=Counter();bases=[]
    limits={'fit':30,'calibration':25,'test':30}
    for number,sentence in enumerate(sentences):
        split=SPLITS.get(sentence['document'].split('.')[0])
        if not split or counts[sentence['document']]>=limits[split]:continue
        row=mutate(sentence,entries,lemma_forms,1207+number)
        if row is None:continue
        if split!='test':row['corruptions']=[r for r in row['corruptions'] if r['family'] in KNOWN]
        if not row['corruptions']:continue
        row['split']=split;counts[sentence['document']]+=1;bases.append(row)
        if len(bases)%20==0:print('curated bases',len(bases),dict(counts),flush=True)
    # Lexical controls use attested noun forms with the same gold morphology.
    noun_pool=defaultdict(list)
    for sentence in sentences:
        for token in sentence['tokens']:
            if token['pos']=='NOUN' and set(('Case','Number','Gender'))<=set(expected(token)):
                noun_pool[tuple(sorted(expected(token).items()))].append((token['word'],token['lemma']))
    cases=[]
    for row in bases:
        original={'id':row['id']+'/original','base':row['id'],'document':row['document'],'split':row['split'],'family':'original','valid':True,'words':row['words']}
        cases.append(original)
        for change in row['corruptions']:
            cases.append({**original,**change,'id':row['id']+'/'+change['family'],'valid':False})
        made=False
        for i,token in enumerate(row['tokens']):
            if token['pos']!='NOUN':continue
            ex=expected(token);pool=sorted(set(noun_pool.get(tuple(sorted(ex.items())),[])));rng.shuffle(pool)
            for word,lemma in pool:
                if lemma==token['lemma'] or word==token['word']:continue
                if not any(v['part_of_speech']=='N' and all(v['features'].get(k)==value for k,value in ex.items()) for a,v in analyses(entries,word)):continue
                words=list(row['words']);words[i]=word
                cases.append({**original,'id':row['id']+'/lexical_control','family':'lexical_control','words':words,'before':token['word'],'after':word,'position':i})
                made=True;break
            if made:break
        index={t['id']:i for i,t in enumerate(row['tokens'])}
        for i,t in enumerate(row['tokens']):
            if t['pos']=='ADJ' and t['relation']=='amod' and t['head'] in index and abs(index[t['head']]-i)==1:
                j=index[t['head']];words=list(row['words']);words[i],words[j]=words[j],words[i]
                cases.append({**original,'id':row['id']+'/order_control','family':'order_control','words':words});break
    # Annotation of unseen words is dictionary lookup, not fitting on test text.
    from voynich_smt.word_mapping.corpora import WordStream
    training=list(WordStream.load(resource.PARENT/'splits/train.json').segments())
    for word in sorted({w for row in cases for w in row['words']}|{w for s in training for w in s}):entries(word)
    write_json(OUT/'morphology.json',{'entries':cache,'annotator_resource':annotator.resource})
    write_json(OUT/'cases.json',cases)
    protocol={'seed':1207,'limits_per_document':limits,'splits_by_work':SPLITS,'known_corruptions':sorted(KNOWN),'unseen_corruptions':['adjective_gender','adjective_number'],
        'label_scope':'original annotated structure; corruption violates recorded dependency with no rescue of the changed feature in the morphology resource; automatic labels, not expert-adjudicated unrestricted grammaticality',
        'grammar_sources':['https://dcc.dickinson.edu/grammar/latin/agreement','https://www.nationalarchives.gov.uk/latin/stage-1-latin/resources/stage-1-latin-grammar-resource/prepositions/'],
        'corpus_source':'https://github.com/UniversalDependencies/UD_Latin-Perseus/tree/r2.17','license':'CC BY-NC-SA 2.5',
        'input_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in DATA.iterdir() if p.is_file()},
        'cases_sha256':digest(cases),'morphology_sha256':hashlib.sha256((OUT/'morphology.json').read_bytes()).hexdigest(),
        'code_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),Path('src/voynich_smt/latin_sentence_cases.py')]}}
    write_json(OUT/'dataset-manifest.json',{'protocol':protocol,'sha256':digest(protocol)})
    print('Dataset',len(cases),'cases',dict(Counter((c['split'],c['family']) for c in cases)),flush=True)
if __name__=='__main__':build()
