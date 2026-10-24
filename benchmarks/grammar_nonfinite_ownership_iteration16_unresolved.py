"""Check dependence on the assumption that a licensed INF has a modeled owner.

Relax the independent Boolean CSP to admit an unknown owner at every NF token.
No objective penalizes that state. This is an assumption diagnostic, not tuning.
"""
from benchmarks.grammar_nonfinite_ownership_iteration16 import OUT,NINE,ARMS,load,save
from benchmarks.grammar_nonfinite_ownership_iteration16_validate import Independent,FrozenAdapter


def run():
    dev=load(NINE/'development-truth.json');adapter=FrozenAdapter(load(OUT/'morphology-lattice.json'));records=[]
    saved=next(r['ownership'] for r in load(OUT/'ownership.json') if (r['stream'],r['mode'],r['boundaries'],r['arm'])==(49,'reference_scope','hidden','joint'))
    s=dev[49];scopes=tuple((int(m),v['target']) for m,v in s['markers'].items() if v['kind']=='relative')
    comp=next(c for c in saved['components'] if 4 in c['positions'])
    relaxed=Independent(s['tokens'],s['finite'],adapter,scopes,(),ARMS['joint'],saved,comp['positions'],unknown_owner=True)
    all_unknown=relaxed.query(*[relaxed.null[nf] for nf in comp['positions']])
    assert all_unknown
    for nf in (4,26):
        parents=sorted({c['parent'] for c in saved['candidates'][str(nf)]})
        possible=[p for p in parents if relaxed.query(relaxed.owner(nf,p))]
        assert possible==[0,27]
        records.append({'position':nf,'surface':s['tokens'][nf],'unknown_owner_possible':relaxed.query(relaxed.null[nf]),
            'possible_parents':possible})
    # The bridge's own readings and requirement to select its INF do not restore
    # the excluded-owner proof when the other INF can have an unknown owner.
    old=next(r for r in load(OUT/'predictions.json') if (r['stream'],r['mode'],r['boundaries'],r['arm'],r['marker'])==(49,'reference_scope','hidden','original',5))
    w=old['result']['chains'][0]
    bridge=Independent(s['tokens'],s['finite'],adapter,scopes,(),ARMS['joint'],saved,comp['positions'],unknown_owner=True)
    binding=bridge.bind_witness(w,5,6)
    false_bridge_possible=bridge.query(binding,bridge.owner(4,27))
    assert false_bridge_possible
    save(OUT/'unresolved-owner-diagnostic.json',{'all_unknown_assignment_satisfiable':all_unknown,
        'source_records':records,'old_false_bridge_possible':false_bridge_possible,
        'conclusion':'Excluding the false bridge depends on forcing licensed unambiguous INFs into the modeled frame inventory. An unrestricted unknown-owner state leaves both ownerships possible; constraints alone do not solve inventory incompleteness.'})
    print(load(OUT/'unresolved-owner-diagnostic.json'))

if __name__=='__main__':run()
