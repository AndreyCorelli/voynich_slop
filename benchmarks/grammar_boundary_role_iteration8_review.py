"""Trace original UD paths and document development-only residual review."""
from collections import Counter
import hashlib
import json
from pathlib import Path
from benchmarks.grammar_boundary_role_iteration8 import OUT,PREVIOUS
from benchmarks.grammar_markers_iteration5 import marker_sentences,TREEBANKS
from voynich_smt.data.corpus import write_json

# Qualitative readings of the saved normalized sentences, not external gold labels.
NOTES={
1:('parenthetical_interference','The free-relative subject belongs to perdet in the UD tree; dico is an intervening parataxis parenthetical. The model selects the parenthetical.'),
2:('intervening_relative','The quia clause modifies coepit in the reference. The model selects sunt inside the intervening relative clause factae sunt.'),
3:('nested_clause','The si clause factae essent belongs to egissent; the model selects sunt in its embedded relative. The si marker is omitted because its lexical head factae is not finite.'),
4:('nested_clause','The conditional factae fuissent depends on mansissent inside the quia clause; the model skips that level to descendes. Its si marker is omitted by the finite-head requirement.'),
5:('projection_artifact','The nearest-finite-ancestor rule skips the outer passive auxiliary fuissent because it is a sibling branch under factae. Reference sunt->mansissent is reproducible, but the predicted sunt->fuissent is plausible at the clause-complex level. Do not call this an independently confirmed linguistic error.'),
6:('nested_clause','The quia clause mansissent depends on descendes; choosing sunt instead makes it depend on an embedded relative. The oracle wrongly routes quae to mansissent under the finite-ancestor projection.'),
7:('coordination_level','reficiam is coordinated with the main imperative uenite in UD. The model coordinates it with estis inside the relative/participial complex instead.'),
8:('relative_scope','nocent modifies animalia, whose finite ancestor is patieris; consueuimus belongs to a separate relative modifying cantharides. The model attaches the two relative predicates together.'),
9:('intervening_relative','The purpose clause generent modifies the imperative sicca in UD. The model attaches it to es in the relative quae sparsurus es.'),
10:('coordination_level','The alternative imperative sere coordinates with sicca, not es in the relative. The role label alone does not identify the coordination level.'),
11:('nested_clause','The relative/free-relative optaueris belongs to adolescant in the reference, not repetas. The exact obj analysis is annotation-derived; the normalized text still supports a nested construction.'),
12:('nested_clause','donec adolescant modifies repetas in UD. The chosen optaueris is inside that donec clause, reversing the intended nesting level.'),
13:('intervening_relative','The cum clause feceris modifies extingues. The intervening relative quod nocebat modifies genus and is not its reference governor.'),
14:('coordinated_subordinates','The first seu ut clause displiceat modifies auertunt. The model instead makes it subordinate to the second seu ut clause cedat.'),
15:('coordination_level','cedat coordinates with displiceat as paired seu ut clauses; accipiunt is the sentence-level main predicate. The model chooses the wrong coordination level.'),
16:('coordination_level','auertunt coordinates with accipiunt in UD. The model attaches it to cedat inside its own subordinate material.'),
17:('sibling_subordinates','The si clause uoluerint and cum clause defuerit both depend on utentur in UD. The model attaches the former to the latter.'),
}


def run():
    load=lambda p:json.loads(p.read_text());cases=load(OUT/'review-cases.json')
    path=TREEBANKS/'proiel-r2.17/la_proiel-ud-train.conllu';records,_=marker_sentences(path,'proiel')
    byid={s['sent_id']:s for s in records};raw={};deps={}
    for block in path.read_text().split('\n\n'):
        sid=next((l.split(' = ',1)[1] for l in block.splitlines() if l.startswith('# sent_id = ')),None)
        rr=[l.split('\t') for l in block.splitlines() if l and not l.startswith('#') and l.split('\t')[0].isdigit()]
        if sid:deps[sid]=[r[7].split(':')[0] for r in rr if r[3]!='PUNCT']
        if sid in {c['sent_id'] for c in cases}:raw[sid]=rr
    reviewed=[]
    for c in cases:
        s=byid[c['sent_id']];offset=c['sentence_start'];local=c['child']-offset
        assert ' '.join(s['tokens'])==c['sentence_text']
        rr=raw[c['sent_id']];kept=[r for r in rr if r[3]!='PUNCT'];index={r[0]:r for r in rr}
        node=kept[local];chain=[]
        while True:
            chain.append({'id':int(node[0]),'form':node[1],'upos':node[3],'features':node[5],'head':int(node[6]),'deprel':node[7]})
            if node[6]=='0':break
            node=index[node[6]]
        finite_ids={int(kept[p][0]) for p in s['finite']}
        nearest=next((r for r in chain[1:] if r['id'] in finite_ids),None)
        assert nearest is not None and nearest['id']==int(kept[c['reference_parent']-offset][0])
        category,note=NOTES[c['case']]
        reviewed.append({**c,'category':category,'review_note':note,'ud_path':chain,
            'reference_derivation_verified':True,'linguistic_review':'qualitative assessment of saved UD/text; no independent expert adjudication'})
    # Audit the projection mechanism across already-inspected evaluation material.
    projection=[]
    for split in ['development','confirmation']:
        streams=load(PREVIOUS/(split+'-truth.json'));counts=Counter();examples=[]
        for stream in streams:
            for info in stream['sentences']:
                s=byid[info['sent_id']];complexes={}
                for p in s['finite']:
                    h=s['heads'][p]
                    if s['upos'][p]=='AUX' and h is not None and s['upos'][h]=='VERB' and h not in s['finite']:
                        complexes.setdefault(h,[]).append(p)
                counts['finite_auxiliary_complexes']+=sum(len(v)==1 for v in complexes.values())
                for i,dep in enumerate(deps[s['sent_id']]):
                    h=s['heads'][i]
                    if dep in {'mark','cc'} and h in complexes and len(complexes[h])==1 and i not in s['markers']:
                        counts['direct_mark_cc_omitted_at_auxiliary_complex']+=1
                for i,m in s['markers'].items():
                    # Relative marker paths can pass lexical heads whose own
                    # finite auxiliary lies on a child branch, not this path.
                    cursor=s['heads'][int(i)];target=None
                    while cursor is not None:
                        if cursor in s['finite']:break
                        if len(complexes.get(cursor,[]))==1:target=complexes[cursor][0];break
                        cursor=s['heads'][cursor]
                    if target is not None and target!=m['target']:
                        counts['existing_marker_targets_skip_local_auxiliary']+=1
                        examples.append({'sent_id':s['sent_id'],'marker':int(i),'surface':s['tokens'][int(i)],'old_target':m['target'],
                            'old_surface':s['tokens'][m['target']],'local_auxiliary':target,'local_surface':s['tokens'][target]})
        projection.append({'split':split,'counts':dict(counts),'examples':examples,
            'scope':'mechanical finite-auxiliary projection audit; proposed alternatives are not revised gold labels'})
    result={'reviewed':len(reviewed),'authors':dict(Counter(c['author'] for c in reviewed)),
        'categories':dict(Counter(c['category'] for c in reviewed)),'cases':reviewed,'projection_audit':projection,
        'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    write_json(OUT/'review.json',result)
    print('Reviewed',len(reviewed),'residuals;',result['categories'])
    for p in projection:print(p['split'],p['counts'])


if __name__=='__main__':run()
