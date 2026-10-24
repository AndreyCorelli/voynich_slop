"""Explicit UD-to-pinned-Whitaker feature compatibility on source text only."""
from collections import Counter
import json

from .latin_corpus import normalize, sha


POS={'NOUN':{'N'},'PROPN':{'N'},'ADJ':{'ADJ'},'ADV':{'ADV'},'VERB':{'V','VPAR'},
     'AUX':{'V'},'ADP':{'PREP'},'PRON':{'PRON'},'DET':{'PRON','ADJ'},
     'NUM':{'NUM'},'CCONJ':{'CONJ'},'SCONJ':{'CONJ'},'INTJ':{'INTERJ'}}
VALUES={'Case':{'Nom':'NOM','Voc':'VOC','Acc':'ACC','Gen':'GEN','Dat':'DAT','Abl':'ABL','Loc':'LOC'},
        'Number':{'Sing':'S','Plur':'P'},'Gender':{'Masc':'M','Fem':'F','Neut':'N'},
        'Person':{'1':'1','2':'2','3':'3'},'Mood':{'Ind':'IND','Sub':'SUB','Imp':'IMP'},
        'Voice':{'Act':'ACTIVE','Pass':'PASSIVE'},
        'Tense':{'Pres':'PRES','Imp':'IMPF','Perf':'PERF','Pqp':'PLUP','Fut':'FUT'},
        'Degree':{'Pos':'POS','Cmp':'COMP','Sup':'SUPER'}}


def compatible(grammar,upos,features):
    pos,pairs,_=json.loads(grammar); available=dict(pairs)
    if upos not in POS or pos not in POS[upos]:return False
    if features.get('VerbForm')=='Inf' and available.get('Mood')!='INF':return False
    if features.get('VerbForm')=='Part' and pos!='VPAR':return False
    # UD tense/aspect does not map one-to-one to Whitaker tense. Only constrain
    # tense when Aspect does not create a compound interpretation.
    for key,values in VALUES.items():
        if key=='Tense':continue
        expected=values.get(features.get(key))
        actual=available.get(key)
        if actual in ('X','0'):actual=None
        if key=='Gender' and actual=='C' and expected in ('M','F'):continue
        if expected is not None and actual is not None and actual!=expected:return False
    return True


def source_evidence(index,inventory,paths,excluded_authors):
    from benchmarks.scalable_latin_caesar import PROIEL,PERSEUS
    evidence=Counter(); report=Counter(); source=[]
    reverse={v:k for k,v in index.labels['grammar'].items()}
    for corpus,path in paths:
        source.append({'corpus':corpus,'path':str(path),'sha256':sha(path)})
        for block in path.read_text().strip().split('\n\n'):
            metadata={}
            for line in block.splitlines():
                if line.startswith('# ') and ' = ' in line:
                    k,v=line[2:].split(' = ',1);metadata[k]=v
            if corpus=='proiel':author=PROIEL.get(metadata.get('source','').split(',')[0])
            else:author=PERSEUS.get(metadata.get('sent_id','').split('.perseus-')[0])
            if author is None:raise ValueError('Unknown annotated training author')
            if author in excluded_authors:report['excluded_tokens']+=sum(l[:1].isdigit() for l in block.splitlines());continue
            for line in block.splitlines():
                cols=line.split('\t')
                if len(cols)<6 or not cols[0].isdigit() or cols[3]=='PUNCT':continue
                form=normalize(cols[1])
                if len(form)!=1:report['non_single_surface']+=1;continue
                try:wid=inventory.id(form[0])
                except KeyError:report['not_in_training_inventory']+=1;continue
                # Lemma text is not forced to a lexeme ID: headword vs resource
                # stems is not a safe identity mapping. Resolve POS/features only.
                features=dict(p.split('=',1) for p in cols[5].split('|') if '=' in p)
                start,end=map(int,index.offsets[wid:wid+2]); choices=[]
                for i in range(start,end):
                    if compatible(reverse[int(index.grammar[i])],cols[3],features):choices.append(i)
                report['source_tokens']+=1
                if choices:
                    for i in choices:evidence[i]+=1/len(choices)
                    report['compatible_tokens']+=1
                else:report['no_compatible_analysis']+=1
    return evidence,{'counts':dict(report),'sources':source,
        'crosswalk':'ud-whitaker-features-v1; tense unconstrained; lemma strings never equated with lexeme IDs',
        'limitations':['Source treebanks contain disjoint passages and differing annotation conventions.',
                      'Compatibility constrains observed features, not an independently gold lexeme identity.',
                      'Attached enclitic/syntactic-token mismatches can remain unresolved.']}
