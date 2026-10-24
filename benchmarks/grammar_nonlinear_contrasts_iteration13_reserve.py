"""Reserve unseen sentence IDs without evaluating tokens or model features."""
import hashlib
import json
from pathlib import Path
from benchmarks.grammar_markers_iteration5 import marker_sentences,TREEBANKS
from voynich_smt.data.corpus import write_json

RESERVATION=Path('experiments/holdouts/grammar-construction-next.json')


def strings(value):
    if isinstance(value,str):yield value
    elif isinstance(value,list):
        for x in value:yield from strings(x)
    elif isinstance(value,dict):
        for x in value.values():yield from strings(x)


def run():
    if RESERVATION.exists():raise ValueError('Preserve holdout reservation')
    root=Path('experiments/results/grammar-restoration')
    files=sorted(set(root.rglob('*manifest*.json'))|set(root.rglob('*truth*.json')))
    used=set();hashes={}
    for p in files:
        used.update(strings(json.loads(p.read_text())));hashes[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
    path=TREEBANKS/'proiel-r2.17/la_proiel-ud-train.conllu';records,_=marker_sentences(path,'proiel');reserved={}
    for author in ['Jerome','Palladius']:
        candidates=[(i,s['sent_id']) for i,s in enumerate([s for s in records if s['author']==author]) if i>=700 and s['sent_id'] not in used]
        selected=candidates[:100]
        if len(selected)!=100:raise ValueError('Insufficient undeclared held-out source sentences for '+author)
        reserved[author]=[{'retained_position':i,'sent_id':sid} for i,sid in selected]
    ids=[r['sent_id'] for group in reserved.values() for r in group]
    assert len(set(ids))==200 and not set(ids)&used
    write_json(RESERVATION,{'status':'reserved; no model features, scores or predictions evaluated',
        'reference_version':'predicate-complex-v1','selection':'first 100 undeclared retained sentences per author at or beyond position 700',
        'authors':reserved,'prior_declaration_sha256':hashes,'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
        'scope':'disjoint from declared manifest/truth samples in grammar-restoration artifacts; not a claim about every other repository experiment',
        'reservation_code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})
    print('Reserved',len(ids),'sentence IDs after auditing',len(files),'prior declaration artifacts.')


if __name__=='__main__':run()
