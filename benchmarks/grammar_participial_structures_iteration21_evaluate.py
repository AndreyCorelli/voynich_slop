"""Evaluation-only local nominal/participial dependency and POS comparison."""
from collections import Counter
from benchmarks.grammar_participial_structures_iteration21 import OUT,TWENTY,SEVENTEEN,NINE,SIXTEEN,load,save
from benchmarks.grammar_argument_structures_iteration20_evaluate import source_nodes


def reference_edges(nodes,unit,start,end):
    predicates={unit['parent'],*unit['members']}
    parts={p for p in range(start,end) if nodes[p]['upos']=='VERB' and nodes[p]['features'].get('VerbForm')=='Part'}
    edges=[]
    for p in range(start,end):
        node=nodes[p]
        if node['upos'] not in ('NOUN','PRON','DET') and p not in parts and not (node['word']=='nisi' and node['head'] in parts):continue
        n=p;seen=set()
        while nodes[n]['relation']=='conj' and nodes[n]['head'] is not None and nodes[n]['head'] not in predicates|parts and n not in seen:
            seen.add(n);n=nodes[n]['head']
        head=nodes[n]['head']
        if head in predicates|parts:edges.append([p,head])
    return sorted(edges)


def source_match(nodes,structure):
    for segment in structure['witness']:
        readings={}
        if 'clause' in segment:
            c=segment['clause'];readings={int(p):r for p,r in c['analyses'].items()}
            if c['marker'] is not None:readings[c['marker']]=c['marker_reading']
        elif 'phrases' in segment:
            for p in segment['phrases']:readings.update({int(k):v for k,v in p['analyses'].items()})
            readings.update({p:{'pos':'CONJ','features':[]} for p in segment['markers']})
        elif segment['reading'] is not None:readings[segment['positions'][0]]=segment['reading']
        for p,r in readings.items():
            n=nodes[p];tag=n['upos'];pos=r['pos']
            permitted={'NOUN':{'N'},'PRON':{'PRON'},'DET':{'ADJ','PRON'},'ADJ':{'ADJ'},'NUM':{'NUM'},'ADV':{'ADV'},'CCONJ':{'CONJ'},'SCONJ':{'CONJ'},'ADP':{'PREP'}}.get(tag,{'VPAR'} if n['features'].get('VerbForm')=='Part' else {'V'})
            if tag=='ADV' and n['word'] in ('enim','autem','ergo','igitur','nisi'):permitted=permitted|{'CONJ'}
            if pos not in permitted:return False
            # Compare morphological nominal/participle features where supplied.
            for k in ('Case','Gender','Number'):
                actual=dict(r['features']).get(k);v=n['features'].get(k)
                expected={'Abl':'ABL','Acc':'ACC','Nom':'NOM','Gen':'GEN','Dat':'DAT','Loc':'LOC','Masc':'M','Fem':'F','Neut':'N','Sing':'S','Plur':'P'}.get(v,v)
                if actual in (None,'X','0') or expected is None:continue
                if actual!=expected and not (k=='Gender' and actual=='C' and expected in ('M','F')):return False
    return True


def evaluate(rows,truth,dev,models):
    refs={(t['stream'],str(t['position'])):t['owner'] for t in truth if t['form']=='Inf'}
    idx={(m['stream'],m['mode'],m['boundaries']):m['model'] for m in models if m['arm']=='units_open'}
    nodes=source_nodes(dev);metrics={};audits=[]
    for row in rows:
        key='/'.join([row['morphology'],row['arm'],row['mode'],row['boundaries']]);c=metrics.setdefault(key,Counter());matched=set();unique=set()
        for nf,parents in row['result']['parents'].items():
            if (row['stream'],nf) in refs:c['reference_owner_retained']+=refs[row['stream'],nf] in parents
        model=idx[row['stream'],row['mode'],row['boundaries']]
        for entry in row['result']['units']:
            r=entry['result'];c['truncated_units']+=r['status']=='truncated'
            if r['status']!='supported':continue
            u=model['units'][entry['unit']];expected=reference_edges(nodes[row['stream']],u,r['start'],r['end'])
            c['supported_units']+=1;c['multiple_structures']+=len(r['structures'])>1
            matches=[sorted({(h,t) for h,t,role in s['links']})==[tuple(x) for x in expected] and source_match(nodes[row['stream']],s) for s in r['structures']]
            part_matches=[m and any('clause' in seg for seg in s['witness']) for m,s in zip(matches,r['structures'])]
            c['matching_participial_unit_available']+=any(part_matches)
            if any(matches):matched.update(n for n in u['members'] if refs.get((row['stream'],str(n)))==u['parent'])
            if all(matches) and len(r['structures'])==1 and r['attachment_status']=='unique_within_grammar':unique.update(n for n in u['members'] if refs.get((row['stream'],str(n)))==u['parent'])
            if row['mode']=='reference_scope' and row['boundaries']=='hidden' and (row['stream'] in (49,58,61) or any(any('clause' in seg for seg in s['witness']) for s in r['structures'])):
                audits.append(dict(stream=row['stream'],morphology=row['morphology'],arm=row['arm'],unit=entry['unit'],members=u['members'],parent=u['parent'],reference_edges=expected,matches=matches,part_matches=part_matches,result=r))
        c['reference_owner_with_matching_local_analysis']+=len(matched)
        c['reference_owner_with_unique_matching_local_analysis']+=len(unique)
    return {k:dict(v) for k,v in metrics.items()},audits

if __name__=='__main__':
    metrics,audits=evaluate(load(OUT/'predictions.json'),load(SIXTEEN/'evaluation-truth.json'),load(NINE/'development-truth.json'),load(SEVENTEEN/'models.json'))
    save(OUT/'evaluation.json',metrics);save(OUT/'audit.json',audits)
    for k,v in metrics.items():
        if k.endswith('reference_scope/hidden'):print(k,v)
