"""Dependency-guided Latin minimal pairs; gold annotations never score inputs."""
from collections import Counter,defaultdict
from pathlib import Path
import random
import re

CASE={'Nom':'NOM','Acc':'ACC','Abl':'ABL','Dat':'DAT','Gen':'GEN','Voc':'VOC','Loc':'LOC'}
NUMBER={'Sing':'S','Plur':'P'}
GENDER={'Masc':'M','Fem':'F','Neut':'N','Com':'C'}
PREPOSITIONS={'ad':'ACC','ante':'ACC','apud':'ACC','per':'ACC','post':'ACC','propter':'ACC','contra':'ACC',
              'cum':'ABL','sine':'ABL','de':'ABL','ex':'ABL','ab':'ABL','a':'ABL','pro':'ABL'}
SPLITS={'phi0975':'fit','phi0972':'fit','phi0620':'fit','tlg0031':'fit',
        'phi0959':'calibration','phi0690':'calibration','phi1348':'calibration',
        'phi0631':'test','phi0474':'test','phi1351':'test','phi1221':'test'}
KNOWN={'subject_number','adjective_case','preposition_case'}

def canonical(word):return word.lower().replace('j','i').replace('v','u')

def read_conllu(path):
    document='';metadata={};tokens=[];sentences=[]
    def finish():
        if tokens:sentences.append({'document':document,'id':metadata.get('sent_id',''),'text':metadata.get('text',''),'tokens':list(tokens)})
    for line in Path(path).read_text().splitlines()+['']:
        if not line:
            finish();metadata={};tokens=[]
        elif line.startswith('# newdoc id ='):document=line.split('=',1)[1].strip()
        elif line.startswith('# ') and ' = ' in line:
            key,value=line[2:].split(' = ',1);metadata[key]=value
        elif not line.startswith('#'):
            fields=line.split('\t')
            if not fields[0].isdigit():continue
            features={} if fields[5]=='_' else dict(x.split('=',1) for x in fields[5].split('|'))
            tokens.append({'id':int(fields[0]),'word':canonical(fields[1]),'lemma':canonical(fields[2]),'pos':fields[3],
                'features':features,'head':int(fields[6]),'relation':fields[7]})
    return sentences

def expected(token):
    result={}
    for key,translation in [('Case',CASE),('Number',NUMBER),('Gender',GENDER)]:
        if token['features'].get(key) in translation:result[key]=translation[token['features'][key]]
    if token['features'].get('Person'):result['Person']=token['features']['Person']
    return result

def analyses(entries,word):
    return [(entry,inflection) for entry in entries(word) for inflection in entry['inflections'] if not entry.get('enclitic')]

def mutate(sentence,entries,lemma_forms,seed):
    rng=random.Random(seed);tokens=[t for t in sentence['tokens'] if t['pos']!='PUNCT']
    if not 6<=len(tokens)<=32 or any(not re.fullmatch('[a-z]+',t['word']) for t in tokens):return None
    by_id={t['id']:t for t in tokens};index={t['id']:i for i,t in enumerate(tokens)}
    children=defaultdict(list)
    for t in tokens:children[t['head']].append(t)
    changes=[]
    for t in tokens:
        constraints=[];exp=expected(t)
        if t['pos'] in ('VERB','AUX') and t['features'].get('VerbForm')=='Fin' and t['features'].get('Person')=='3':
            subjects=[s for s in children[t['id']] if s['relation']=='nsubj' and expected(s).get('Case')=='NOM']
            if len(subjects)==1 and expected(subjects[0]).get('Number')==exp.get('Number') and not any(c['relation']=='conj' for c in children[subjects[0]['id']]):
                constraints.append(('subject_number','Number','V',subjects[0]['id']))
        if t['pos']=='ADJ' and t['relation']=='amod' and t['head'] in by_id:
            head=by_id[t['head']];hp=expected(head)
            if head['pos'] in ('NOUN','PROPN') and all(key in exp and exp[key]==hp.get(key) for key in ('Case','Number','Gender')):
                constraints.extend((name,key,'ADJ',head['id']) for name,key in [('adjective_case','Case'),('adjective_number','Number'),('adjective_gender','Gender')])
        if t['pos'] in ('NOUN','PROPN'):
            preps=[p for p in children[t['id']] if p['pos']=='ADP' and p['relation']=='case' and p['word'] in PREPOSITIONS]
            if len(preps)==1 and exp.get('Case')==PREPOSITIONS[preps[0]['word']]:constraints.append(('preposition_case','Case','N',preps[0]['id']))
        for family,key,pos,related in constraints:
            originals=[(a,i) for a,i in analyses(entries,t['word']) if i['part_of_speech']==pos and all(i['features'].get(k)==v for k,v in exp.items())]
            candidates=[]
            for entry,inflection in originals:
                original=inflection['features']
                if key not in original:continue
                for word in lemma_forms.get(entry.get('lexeme_id'),()):
                    if word==t['word'] or not re.fullmatch('[a-z]+',word):continue
                    # Retain lemma and other inflectional features. Reject every
                    # alternate reading that could rescue the broken feature.
                    available=analyses(entries,word)
                    if any(i['features'].get(key)==original[key] for a,i in available):continue
                    for a,i in available:
                        f=i['features']
                        if a.get('lexeme_id')==entry.get('lexeme_id') and i['part_of_speech']==pos and f.get(key) not in (None,'X',original[key]) and all(f.get(k)==v for k,v in original.items() if k!=key):
                            candidates.append((word,original[key],f[key]));break
            if candidates:
                word,before,after=rng.choice(sorted(set(candidates)));changed=[v['word'] for v in tokens];changed[index[t['id']]]=word
                changes.append({'family':family,'words':changed,'position':index[t['id']],'before':t['word'],'after':word,'lemma':t['lemma'],
                    'feature':key,'old_value':before,'new_value':after,'dependency':[related,t['id']]})
    if not changes:return None
    rng.shuffle(changes);selected={}
    for change in changes:selected.setdefault(change['family'],change)
    return {'id':sentence['id'],'document':sentence['document'],'original_text':sentence['text'],'words':[t['word'] for t in tokens],
        'tokens':tokens,'corruptions':list(selected.values())}
