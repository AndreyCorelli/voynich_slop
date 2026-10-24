"""Post hoc coverage/score attribution; never change the frozen lexical gate."""
import sqlite3
from benchmarks.grammar_lexical_bridge_iteration69 import *


def run():
    inventory=Path('experiments/results/scalable-latin-caesar/v1/resources/inventory.sqlite');save(OUT/'posthoc-inventory-design.json',dict(inputs={str(Path(__file__)):digest(Path(__file__)),str(inventory):digest(inventory)},scope='Posthoc read-only membership check in larger old Latin inventory; no candidate pools/search/scoring changes.'))
    connection=sqlite3.connect(inventory.resolve().as_uri()+'?mode=ro',uri=True);metadata=dict(connection.execute('SELECT key,value FROM metadata'));rows=load(OUT/'first-corruption-scores.json');scorer=build_scorer();cases=[];counts=Counter()
    for r in rows:
        availability=[]
        for change in r['changes']:
            old=connection.execute('SELECT id FROM forms WHERE word=?',(change['old'],)).fetchone() is not None;new=connection.execute('SELECT id FROM forms WHERE word=?',(change['new'],)).fetchone() is not None;availability.append(dict(**change,old_in_full=old,new_in_full=new));counts['originals_available_full']+=old
        crops=[]
        for c in r['crops']:
            frames={};details={};tokens={}
            for version in ('before','after'):
                words=c[version+'_tokens'];ts,origins,fs=scorer.frames(words);tokens[version]=ts;frames[version]=fs;positions=[j for j,(a,b) in enumerate(zip(c['before_tokens'],c['after_tokens'])) if a!=b];p,_=decode(fs,scorer.policy['cutoff'],scorer.policy['selected']['carrier']['penalty']);details[version]=[dict(position=j,word=words[j],pos=ts[j]['pos'],outgoing_candidates=next((len(f['predicates']) for f in fs if f['subject']==j),0),incoming_candidate_edges=sum(j in f['predicates'] for f in fs),selected_as_subject=p.get(j) is not None,selected_as_carrier=sum(v==j for v in p.values())) for j in positions]
            identical=frames['before']==frames['after'];counts['crops']+=1;counts['identical_scored_lattice_crops']+=identical;crops.append(dict(identical_scored_lattice=identical,changed=details))
        cases.append(dict(target=r['target'],seed=r['seed'],availability=availability,crops=crops,aggregate=r['aggregate']))
    connection.close();save(OUT/'posthoc-diagnostics.json',dict(inventory_metadata=metadata,counts=dict(counts),cases=cases,warning='Coverage in a different older inventory is not a rerun with that inventory and does not repair failed scoring.'))
    print(dict(counts))
    for r in cases:print(r['target'],r['seed'],r['availability'],[c['identical_scored_lattice'] for c in r['crops']])
if __name__=='__main__':run()
