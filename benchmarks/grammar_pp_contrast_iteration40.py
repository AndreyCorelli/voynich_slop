"""Predeclared oracle PP ranking diagnostic on reused development slices."""
from pathlib import Path
from collections import Counter
import math
import numpy as np
from benchmarks.grammar_latent_classes_iteration26 import ROOT,TREEBANK,RESERVE,load,save,digest
from voynich_smt.pp_contrast import train,score
OUT=ROOT/'iteration40'


def constructions(tokens):
    result=[]
    for p,t in enumerate(tokens):
        h=t['head']
        if t['pos']!='ADP' or t['rel']!='case' or h is None or tokens[h]['pos'] not in ('NOUN','PROPN','PRON') or not tokens[h]['case']:continue
        members={p,h}
        members.update(i for i,r in enumerate(tokens) if r['head']==h and r['rel'] in ('amod','det','nummod','flat','compound'))
        left,right=min(members),max(members)
        if set(range(left,right+1))!=members:continue
        result.append(dict(prep=p,head=h,left=left,right=right,case=tokens[h]['case']))
    return result


def corruptions(tokens,candidate,frequencies,case_counts):
    p,h=candidate['prep'],candidate['head'];result=[]
    # Same sentence, case, nominal POS, and adjacent log2 source-frequency bin.
    bucket=lambda w:int(math.log2(1+frequencies.get(w,0)))
    targets=[i for i,t in enumerate(tokens) if i!=h and t['pos']==tokens[h]['pos'] and t['case']==tokens[h]['case'] and abs(i-p)<=12 and abs(bucket(t['word'])-bucket(tokens[h]['word']))<=1]
    if targets:
        target=min(targets,key=lambda i:(abs(abs(i-p)-abs(h-p)),i));result.append(('attachment',dict(candidate,head=target,left=min(p,target),right=max(p,target))))
    alternatives=[c for c in case_counts if c!=candidate['case'] and c!='_']
    if alternatives:
        alt=min(alternatives,key=lambda c:(abs(math.log1p(case_counts[c])-math.log1p(case_counts.get(candidate['case'],0))),c));result.append(('morphology',dict(candidate,case=alt)))
    # Preserve prep/head; alter exactly one endpoint by one token.
    left,right=candidate['left'],candidate['right'];bounds=[]
    if left>0:bounds.append((left-1,right))
    if right+1<len(tokens):bounds.append((left,right+1))
    if left not in (p,h):bounds.append((left+1,right))
    if right not in (p,h):bounds.append((left,right-1))
    for j,(l,r) in enumerate(bounds):result.append((f'boundary{j}',dict(candidate,left=l,right=r)))
    return result


def run():
    assert not OUT.exists()
    for p,h in load(ROOT/'iteration39/verification-manifest.json')['inputs'].items():assert digest(p)==h,p
    previous=load(ROOT/'iteration24/datasets.json');old=load(ROOT/'iteration26/datasets.json');splits={'source':[s['sent_id'] for s in previous['train']], 'Jerome':[s['sent_id'] for s in old['jerome']], 'Caesar':[s['sent_id'] for s in old['caesar']]};wanted={sid for ids in splits.values() for sid in ids};reserved={r['sent_id'] for rows in load(RESERVE)['authors'].values() for r in rows};assert not wanted&reserved
    data={}
    for block in TREEBANK.read_text().split('\n\n'):
        lines=block.splitlines();sid=next((l.split(' = ',1)[1] for l in lines if l.startswith('# sent_id = ')),None)
        if sid in reserved or sid not in wanted:continue
        rows=[l.split('\t') for l in lines if l and not l.startswith('#')];rows=[r for r in rows if r[0].isdigit() and r[3]!='PUNCT'];indices={r[0]:i for i,r in enumerate(rows)};tokens=[]
        for r in rows:
            feats=dict(x.split('=',1) for x in r[5].split('|') if '=' in x)
            tokens.append(dict(word=r[1].lower().replace('v','u').replace('j','i'),pos=r[3],case=feats.get('Case',''),number=feats.get('Number',''),gender=feats.get('Gender',''),head=indices.get(r[6]),rel=r[7].split(':')[0]))
        data[sid]=tokens
    assert wanted==set(data)
    examples=[(data[sid],c) for sid in splits['source'] for c in constructions(data[sid])];model=train(examples);freq=Counter(t['word'] for sid in splits['source'] for t in data[sid]);pairs=[];coverage={}
    for author in ('Jerome','Caesar'):
        counts=Counter()
        for sid in splits[author]:
            tokens=data[sid]
            for index,c in enumerate(constructions(tokens)):
                counts['constructions']+=1
                for kind,bad in corruptions(tokens,c,freq,model['counts']['case']):
                    family='boundary' if kind.startswith('boundary') else kind;counts[family]+=1
                    pairs.append(dict(author=author,sent_id=sid,construction=index,family=family,kind=kind,correct=c,corrupt=bad))
        coverage[author]=dict(counts)
    OUT.mkdir();save(OUT/'model.json',model);save(OUT/'data-truth.json',data);save(OUT/'pairs-truth.json',pairs)
    paths=[Path(__file__),Path('src/voynich_smt/pp_contrast.py'),TREEBANK,RESERVE,ROOT/'iteration24/datasets.json',ROOT/'iteration26/datasets.json',ROOT/'iteration39/verification-manifest.json']
    save(OUT/'manifest.json',dict(inputs={str(p):digest(p) for p in paths},split_ids=splits,source_constructions=len(examples),coverage=coverage,
        scope='Reused development100 queries each author; Caesar author absent from source Jerome/Palladius. Oracle POS, morphology, plaintext preposition identity and gold-conditioned candidate generation. No ciphertext reconstruction or independent fresh confirmation.',
        scoring='Source-only add-half categorical terms: preposition-case government, distance, internal POS boundary template, modifier agreement. Equal additive weights fixed before scoring. Local control global case plus distance. No target fitting.',
        negatives='Annotation contrasts; alternate attachments may also be grammatical. Frequency-matched attachment uses same POS/case and +/-1 log2 source-frequency bin within12 tokens. Morphology changes only case to nearest source-frequency case; boundaries alter one endpoint one token. Attachment spans necessarily change with head; not isolated boundary-free intervention.',
        evaluation='Pairwise strict win/tie/loss, equal-construction family means, complete-set strict accuracy; 10000 sentence cluster draws. No hyperparameter selection; reserve excluded before annotation parsing.'))
    save(OUT/'evaluation-freeze.json',dict(inputs={str(p):digest(p) for p in OUT.glob('*.json')}));pred=[]
    for row in pairs:pred.append(dict(**row,correct_scores=score(model,data[row['sent_id']],row['correct']),corrupt_scores=score(model,data[row['sent_id']],row['corrupt'])))
    save(OUT/'predictions.json',pred);evaluate(pred)


def evaluate(rows):
    result={}
    for author in ('Jerome','Caesar'):
        for family in ('attachment','morphology','boundary'):
            selected=[r for r in rows if r['author']==author and r['family']==family]
            for arm in ('local','structural'):
                margins=np.array([r['correct_scores'][arm]-r['corrupt_scores'][arm] for r in selected]);groups={}
                for r,m in zip(selected,margins):groups.setdefault((r['sent_id'],r['construction']),[]).append(float(m))
                result[f'{author}/{family}/{arm}']=dict(pairs=len(selected),constructions=len(groups),wins=int((margins>1e-12).sum()),ties=int((abs(margins)<=1e-12).sum()),losses=int((margins< -1e-12).sum()),construction_mean_win=float(np.mean([np.mean(np.array(v)>1e-12) for v in groups.values()])) if groups else None)
    complete={}
    for author in ('Jerome','Caesar'):
        grouped={}
        for r in rows:
            if r['author']==author:grouped.setdefault((r['sent_id'],r['construction']),[]).append(r)
        eligible={k:v for k,v in grouped.items() if {r['family'] for r in v}=={'attachment','morphology','boundary'}}
        complete[author]={a:dict(eligible=len(eligible),strictly_correct=sum(all(r['correct_scores'][a]>r['corrupt_scores'][a]+1e-12 for r in v) for v in eligible.values())) for a in ('local','structural')}
    save(OUT/'evaluation.json',dict(pairwise=result,whole_construction=complete));print(result,complete)
if __name__=='__main__':run()
