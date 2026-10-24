"""Evaluation-only annotation paths. Never imported by bridge inference."""
from collections import Counter
from pathlib import Path
from benchmarks.grammar_relative_bridge_iteration14 import OUT,NINE,load,save

TREEBANK=Path('data/latin-grammar-benchmark/proiel-r2.17/la_proiel-ud-train.conllu')


def run():
    dev=load(NINE/'development-truth.json');metadata=load(NINE/'sentence-complexes.json')['development']
    wanted={s['sent_id'] for stream in dev for s in stream['sentences']}
    raw={}
    for block in TREEBANK.read_text().split('\n\n'):
        sid=next((l.split(' = ',1)[1] for l in block.splitlines() if l.startswith('# sent_id = ')),None)
        if sid not in wanted:continue
        rows=[l.split('\t') for l in block.splitlines() if l and not l.startswith('#') and l.split('\t')[0].isdigit() and l.split('\t')[3]!='PUNCT']
        positions={r[0]:i for i,r in enumerate(rows)}
        raw[sid]=[{'surface':r[1],'upos':r[3],'head':positions.get(r[6]),'relation':r[7]} for r in rows]
    complexes={s['sent_id']:{c['representative']:c['head'] for c in s['predicate_complexes']} for s in metadata}
    audit=[]
    for r in load(OUT/'predictions.json'):
        if r['mode']!='reference_scope' or r['boundaries']!='hidden':continue
        s=dev[r['stream']];offset=0
        for info,end in zip(s['sentences'],s['boundaries']):
            if r['child']<end:break
            offset=end
        sid=info['sent_id'];nodes=raw[sid];mapping=complexes[sid]
        childhead=mapping.get(r['child']-offset,r['child']-offset)
        parenthead=mapping.get(r['reference_parent']-offset,r['reference_parent']-offset) if r['reference_parent'] is not None else None
        node=nodes[childhead]['head'];path=[];seen=set()
        while node is not None and node!=parenthead and node not in seen:
            seen.add(node);path.append({'position':node+offset,**nodes[node]});node=nodes[node]['head']
        nominals=[n['position'] for n in path if n['upos'] in ('NOUN','PROPN','PRON','NUM','ADJ')]
        witnesses=r['result']['bridges'];parent_ok=r['result']['parents']==[r['reference_parent']]
        overlap=[w['antecedent'] for w in witnesses if w['antecedent'] in nominals and w['governor']==r['reference_parent']]
        audit.append({'stream':r['stream'],'sent_id':sid,'marker':r['marker'],'child':r['child'],
            'reference_parent':r['reference_parent'],'reference_nominal_path':nominals,'evaluation_only_path':path,
            'status':r['result']['status'],'parent_correct':parent_ok,
            'any_reference_path_bridge':bool(overlap),
            'all_claimed_bridges_on_reference_path':bool(witnesses) and parent_ok and all(w['antecedent'] in nominals for w in witnesses),
            'text':' '.join(s['tokens']),
            'claimed_bridges':[{'antecedent':w['antecedent'],'surface':s['tokens'][w['antecedent']],
                'governor':w['governor'],'governor_surface':s['tokens'][w['governor']],
                'relative_role':w['relative_role'],'governing_role':w['governing_role']} for w in witnesses]})
    unique=[a for a in audit if a['status']=='unique_parent']
    summary={'reference_scope_hidden':{'unique_parent_claims':len(unique),
        'correct_parent':sum(a['parent_correct'] for a in unique),
        'correct_parent_with_any_nominal_path_overlap':sum(a['any_reference_path_bridge'] for a in unique),
        'correct_parent_with_all_bridges_on_nominal_path':sum(a['all_claimed_bridges_on_reference_path'] for a in unique)},
        'interpretation':'UD path overlap is evaluation evidence, not adjudicated antecedent gold; correct parent alone does not establish a correct grammatical bridge.'}
    save(OUT/'annotation-audit.json',{'summary':summary,'cases':audit});print(summary)

if __name__=='__main__':run()
