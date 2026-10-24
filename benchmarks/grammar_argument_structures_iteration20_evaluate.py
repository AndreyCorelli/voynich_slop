"""Owner metrics and explicitly bounded local nominal-attachment comparison."""
from collections import Counter
from benchmarks.grammar_argument_structures_iteration20 import OUT,ARMS,EIGHTEEN,SEVENTEEN,NINE,SIXTEEN,load,save
from benchmarks.grammar_oracle_morphology_iteration19 import TREEBANK
from benchmarks.scalable_latin_caesar import words


def source_nodes(dev):
    wanted={s['sent_id'] for r in dev for s in r['sentences']};sources={}
    for block in TREEBANK.read_text().split('\n\n'):
        sid=next((l.split(' = ',1)[1] for l in block.splitlines() if l.startswith('# sent_id = ')),None)
        if sid not in wanted:continue
        rows=[l.split('\t') for l in block.splitlines() if l and not l.startswith('#') and l.split('\t')[0].isdigit() and l.split('\t')[3]!='PUNCT']
        mapping={r[0]:i for i,r in enumerate(rows)}
        sources[sid]=[dict(word=words(r[1])[0],upos=r[3],head=mapping.get(r[6]),relation=r[7],features=dict(x.split('=',1) for x in r[5].split('|') if '=' in x)) for r in rows]
    streams=[]
    for s in dev:
        nodes=[]
        for sentence in s['sentences']:
            offset=len(nodes)
            nodes.extend({**n,'head':n['head']+offset if n['head'] is not None else None} for n in sources[sentence['sent_id']])
        assert [n['word'] for n in nodes]==s['tokens'];streams.append(nodes)
    return streams


def nominal_links(nodes,unit,start,end):
    """Direct nominal dependents, plus nominal conjuncts inheriting their head.

    Compare only head-to-predicate links, not semantic adjunct labels, NP internal
    edges or a full parse. Shared alternatives need not match a single UD tree.
    """
    predicates={unit['parent'],*unit['members']};links=[]
    for p in range(start,end):
        if nodes[p]['upos'] not in ('NOUN','PRON','DET'):continue
        n=p;seen=set()
        while nodes[n]['relation']=='conj' and nodes[n]['head'] is not None and nodes[n]['head'] not in predicates and n not in seen:
            seen.add(n);n=nodes[n]['head']
        head=nodes[n]['head']
        if head in predicates:links.append([p,head])
    return sorted(links)


def source_pos_match(nodes,structure):
    """Coarse source reading audit, independent of owner evaluation.

    Dictionary CONJ discourse particles are accepted as a declared projection.
    No semantic adjunct labels or complete NP dependency tree is evaluated.
    """
    for segment in structure['witness']:
        readings={}
        if 'phrases' in segment:
            for phrase in segment['phrases']:readings.update({int(p):r for p,r in phrase['analyses'].items()})
            readings.update({p:{'pos':'CONJ','features':[]} for p in segment['markers']})
        elif segment['reading'] is not None:readings[segment['positions'][0]]=segment['reading']
        for p,r in readings.items():
            n=nodes[p];tag=n['upos'];pos=r['pos']
            permitted={'NOUN':{'N'},'PRON':{'PRON'},'DET':{'ADJ','PRON'},'ADJ':{'ADJ'},'NUM':{'NUM'},
                'ADV':{'ADV'},'CCONJ':{'CONJ'},'SCONJ':{'CONJ'},'ADP':{'PREP'}}.get(tag,{'VPAR'} if n['features'].get('VerbForm')=='Part' else {'V'})
            if tag=='ADV' and n['word'] in ('enim','autem','ergo','igitur'):permitted=permitted|{'CONJ'}
            if pos not in permitted:return False
    return True


def evaluate(rows,truth,dev,models):
    refs={(t['stream'],str(t['position'])):t['owner'] for t in truth if t['form']=='Inf'}
    idx={(r['stream'],r['mode'],r['boundaries']):r['model'] for r in models if r['arm']=='units_open'}
    nodes=source_nodes(dev);metrics={};audits=[]
    for row in rows:
        key='/'.join([row['morphology'],row['arm'],row['mode'],row['boundaries']]);c=metrics.setdefault(key,Counter())
        for nf,parents in row['result']['parents'].items():
            owner=refs.get((row['stream'],nf))
            if (row['stream'],nf) not in refs:continue
            c['reference_owner_retained']+=owner in parents
            c['unique_owner_candidates']+=len(parents)==1
            c['unique_correct_owner_candidates']+=len(parents)==1 and owner==parents[0]
        model=idx[row['stream'],row['mode'],row['boundaries']];matched_owners=set();unambiguous_owners=set()
        for entry in row['result']['units']:
            r=entry['result'];c['truncated_units']+=r['status']=='truncated'
            if r['status']!='supported':continue
            c['supported_units']+=1;c['multiple_structures']+=len(r['structures'])>1
            c['unresolved_attachment']+=r['attachment_status']=='unresolved'
            u=model['units'][entry['unit']];expected=nominal_links(nodes[row['stream']],u,r['start'],r['end'])
            matches=[sorted({(h,t) for h,t,role in structure['links']})==[tuple(x) for x in expected] for structure in r['structures']]
            pos_matches=[source_pos_match(nodes[row['stream']],structure) for structure in r['structures']]
            combined=[a and b for a,b in zip(matches,pos_matches)]
            if any(combined):
                matched_owners.update(n for n in u['members'] if refs.get((row['stream'],str(n)))==u['parent'])
            if all(combined) and len(r['structures'])==1 and r['attachment_status']=='unique_within_grammar':
                unambiguous_owners.update(n for n in u['members'] if refs.get((row['stream'],str(n)))==u['parent'])
            c['reference_links_and_pos_available']+=any(combined)
            c['all_structures_match_links_and_pos']+=all(combined)
            c['reference_local_links_available']+=any(matches)
            c['all_structures_match_local_links']+=all(matches)
            if row['mode']=='reference_scope' and row['boundaries']=='hidden' and row['stream'] in (4,49,56,58,61):
                audits.append(dict(stream=row['stream'],morphology=row['morphology'],arm=row['arm'],unit=entry['unit'],members=u['members'],parent=u['parent'],
                    expected_nominal_links=expected,matches=matches,source_pos_matches=pos_matches,links_and_pos_matches=combined,result=r))
        c['reference_owner_with_matching_local_analysis']+=len(matched_owners)
        c['reference_owner_with_unique_matching_local_analysis']+=len(unambiguous_owners)
    return {k:dict(v) for k,v in metrics.items()},audits

if __name__=='__main__':
    metrics,audit=evaluate(load(OUT/'predictions.json'),load(SIXTEEN/'evaluation-truth.json'),load(NINE/'development-truth.json'),load(SEVENTEEN/'models.json'))
    save(OUT/'evaluation.json',metrics);save(OUT/'audit.json',audit)
    for k,v in metrics.items():
        if k.endswith('reference_scope/hidden'):print(k,v)
