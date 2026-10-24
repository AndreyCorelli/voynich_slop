"""Linear feature-block explanation of a wrong ROOT choice under full oracles."""
import hashlib
import json
from pathlib import Path
import numpy as np

from benchmarks.grammar_marker_oracle_iteration6 import OUT,FIVE
from benchmarks.grammar_structure_iteration3_validate import FrozenAdapter
from voynich_smt.parent_ranking import ConditionalRanker,typed_features,RELATIONS
from voynich_smt.marker_structure import attachment_features
from voynich_smt.predicate_structure import morph_features
from voynich_smt.data.corpus import write_json,digest


def run():
    rows=json.loads((OUT/'predictions.json').read_text())
    truth={r['id']:r for r in json.loads((FIVE/'target-evaluation-only-truth.json').read_text())}
    raw=json.loads((FIVE/'models.json').read_text())
    adapter=FrozenAdapter(json.loads((FIVE/'morphology-lattice.json').read_text()))
    examples=[]
    for name in ['marker_only','marker_interactions']:
        selected=None
        for r in rows:
            if (r['dataset'],r['model'],r['marker_mode'],r['evidence'],r['boundaries'])!=('target',name,'oracle_full','oracle_predicates','supplied'):continue
            for audit in r['score_audit']['per_child']:
                if audit['error']!='false_root':continue
                own=[m for m in r['prediction']['marker_attachments'] if m['target']==audit['child']]
                if own:selected=(r,audit,own);break
            if selected:break
        if not selected:continue
        r,audit,own=selected;gold=truth[r['id']];child=audit['child'];parent=audit['reference_parent'];relation=audit['reference_relation']
        pred=r['prediction'];morph=[morph_features(adapter.analyze(w)) for w in gold['tokens']]
        def feature(p,kind):return attachment_features(gold['tokens'],child,p,pred['predicates'],morph,kind,pred['marker_attachments'],name=='marker_interactions')
        correct=feature(parent,relation);wrong=feature(None,'root')
        model=ConditionalRanker(**raw[name]);difference=(np.asarray(wrong)-np.asarray(correct))*np.asarray(model.weights[1:])/np.asarray(model.scale)
        old_length=len(typed_features(gold['tokens'],child,parent,pred['predicates'],morph,relation))
        old_width=old_length//3;new_width=(len(difference)-old_length)//3;components={}
        for i,kind in enumerate(RELATIONS):
            components[f'base_{kind}']=float(sum(difference[i*old_width:(i+1)*old_width]))
            components[f'explicit_marker_{kind}']=float(sum(difference[old_length+i*new_width:old_length+(i+1)*new_width]))
        gap=float(model.logits([wrong])[0]-model.logits([correct])[0])
        assert np.isclose(sum(components.values()),gap,atol=1e-10)
        options=pred['arc_candidates'][str(child)]
        recorded_gap=next(x['logit'] for x in options if x['parent'] is None)-next(x['logit'] for x in options if x['parent']==parent and x['relation']==relation)
        assert np.isclose(gap,recorded_gap,atol=1e-10)
        examples.append({'id':r['id'],'model':name,'child':child,'child_surface':gold['tokens'][child],
            'reference_parent':parent,'reference_parent_surface':gold['tokens'][parent],'reference_relation':relation,
            'reference_marker_evidence':own,'ROOT_minus_reference_typed_score':gap,'additive_feature_block_deltas':components,
            'context_tokens':gold['tokens'][max(0,min(child,parent)-3):min(len(gold['tokens']),max(child,parent)+4)]})
    report={'examples':examples,'scope':'Fixed linear-model score differences, not causal proof that one feature block alone explains all errors',
        'report_sha256':digest(json.loads((OUT/'report.json').read_text())),
        'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    write_json(OUT/'parent-score-explanation.json',report)
    print(json.dumps(examples,indent=2))


if __name__=='__main__':run()
