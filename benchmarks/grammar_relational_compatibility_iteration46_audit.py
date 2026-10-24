"""Per-author effects and false uniqueness under the paired wrong-token probes."""
from benchmarks.grammar_relational_compatibility_iteration46 import OUT,load,save
from voynich_smt.relational_compatibility import sv_value


def run():
    examples=load(OUT/'sv-lattices.json');index={(e['sent_id'],e['subject'],e['predicate']):e for e in examples};author={};wrong={}
    for a in ('Cicero','Palladius'):
        selected=[e for e in examples if e['author']==a];author[a]=dict(n=len(selected),baseline_unique={arm:sum(e['arms'][arm]['summaries']['none']['unique_link_correct'] for e in selected) for arm in ('none','number','agreement','hidden')},cross_propagation={f:sum(e['arms']['agreement']['summaries'][f]['unrevealed_resolved'].get('predicate' if f=='subject' else 'subject',False) and not e['arms']['agreement']['summaries']['none']['unrevealed_resolved'].get('predicate' if f=='subject' else 'subject',False) for e in selected) for f in ('subject','predicate')})
    for probe in load(OUT/'sv-wrong-fact-probes.json'):
        e=index[probe['sent_id'],probe['subject'],probe['predicate']];field=probe['field'];opposite='predicate' if field=='subject' else 'subject';candidates=[c for c in e['arms'][probe['arm']]['candidates'] if sv_value(c,field)==probe['wrong_value']];conditioned=[c for c in candidates if sv_value(c,opposite)==sv_value(e['reference'],opposite)];row=wrong.setdefault(probe['arm']+'/'+field,dict(n=0,alone_nonempty=0,alone_unique_wrong_link=0,with_correct_opposite_nonempty=0,with_correct_opposite_unique_wrong_link=0));row['n']+=1;row['alone_nonempty']+=bool(candidates);row['with_correct_opposite_nonempty']+=bool(conditioned);row['alone_unique_wrong_link']+=len({tuple(c[:2]) for c in candidates})==1;row['with_correct_opposite_unique_wrong_link']+=len({tuple(c[:2]) for c in conditioned})==1
    save(OUT/'additional-audit.json',dict(authors=author,wrong_facts=wrong,note='Same frozen samples/probes, no fitting or model selection. Wrong means differs from annotated reference link; surviving pairs are not proven ungrammatical.'))
    print(author);print(wrong)
if __name__=='__main__':run()
