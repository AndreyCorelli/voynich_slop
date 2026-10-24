"""Qualitative audit of all twenty predetermined same-child contrasts."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import numpy as np
from benchmarks.grammar_nonlinear_contrasts_iteration13 import OUT,observations
from benchmarks.grammar_markers_iteration5 import marker_sentences,TREEBANKS
from benchmarks.grammar_decoder_confusions_iteration12 import pair_rows
from voynich_smt.data.corpus import write_json

# Construction readings are hypotheses from saved text/UD, not adjudicated gold.
NOTES={
1:('relative','parallel relatives and elliptical coordination','Repeated quod non ... et ... quod non and parallel passive predicates are observable. A clause-span/coordination analysis could connect the relatives. The omitted matrix copula makes the reference clause level less straightforward; do not assume a simple nominal bridge.'),
2:('relative','free relative with nominal bridge','omnis ... qui confitebitur and the later confitebor ... eum supply a topic/relative and matrix argument pattern. The UD path goes through omnis; pronoun/argument linkage is absent from the pair summaries. Child-to-parent verb agreement would not be a valid replacement.'),
3:('relative','nominal relative with locative copula','qui est in caelis modifies patre in the annotation; the relative copular complex and its nominal antecedent must be distinguished. Gender/number candidates and a nominal attachment path could help, but the observed feature vector does not contain that path.'),
4:('relative','free relative, coordination and copular matrix','qui non accipit ... et sequitur precedes non est me dignus. Recognizing the relative span and dignus/est matrix complex could distinguish two identical est surface candidates. A relative marker flag alone does not close the coordinated relative.'),
5:('temporal','cum clause and factum est formula','factum est cum ... consummasset supplies an observable verbal-complex/temporal frame. The reference parent is the finite representative of factum est; lexical/complex structure is not explicitly represented, and the source sentence is fragment-like.'),
6:('conditional','conditional before copular matrix','si uultis recipere precedes ipse est helias. Recognizing the conditional span and helias/est predicate could help; the competing previous-sentence prophetauerunt is exactly as distant. The trailing qui uenturus est introduces another relative complex.'),
7:('relative','free relative with modal/infinitive and nominal path','cui uoluerit filius reuelare is embedded in a nisi/coordination context. The UD path traverses filius and quis before nouit, but this is not independent proof of a simple lexical antecedent. A consistent argument/coordination analysis is required.'),
8:('relative','nominal relative and nonfinite main arguments','quae uitibus nocent modifies animalia, an adjunct of patieris in UD. Pronoun-to-antecedent agreement and nominal governance could connect them across intervening material. The wrong crucifigunt can agree with nocent in verb number, so child/parent agreement alone is misleading.'),
9:('conditional','conditional with reported instruction','si uitibus consulemus precedes feruntur ungendae. The conditional-to-instruction/reporting span and nonfinite complement matter; local distance and generic marker kinds do not identify the reporting governor.'),
10:('relative','free-relative argument with nonfinite complement','quaecunque ... uolueris esse belongs to the later perfundas instruction in UD. Closing the verbal-complement/free-relative span and identifying the matrix argument are candidate evidence, not supplied outputs.'),
11:('temporal','donec clause after coordinated instruction','hoc repetas donec ... adolescant gives an observable temporal endpoint; optaueris is nested inside it. Marker identity/order and the scope of the repeated instruction are lost in coarse interval aggregates.'),
12:('conditional','conditional through reported infinitive','si ... fundatur attaches through nonfinite pelli to dicuntur in the annotation. An explicit nonfinite-complement/conditional-span analysis is needed; the nearby cross-sentence aestimant is also a reporting predicate.'),
13:('conditional','conditional through modal infinitive','si aliqui ex his urantur belongs inside the fugari posse report under aestimant. Nonfinite complement scope and argument references could distinguish it; current summaries do not commit to that scope.'),
14:('temporal','ubi clause in coordinated main structure','ubi instare malum uiderint precedes accipiunt, followed by coordinated auertunt and two seu ut clauses. The surface introducer and verb-complement span are observable; exact ubi scope and the main-clause level require structure, not a presumed gold boundary.'),
15:('conditional','long conditional in reported nonfinite structure','si ... macerentur belongs to a long feruntur ... seruari report. A nonfinite-complement span could support the long correct link over nearby est; proximity does not favor the reference here.'),
16:('relative','nominal relative through locare/debemus','quae ... submoueat has a nominal bridge in the annotation, via parte and locare to debemus. Several feminine singular nouns are plausible antecedents in the text; UD selection of parte is not expert adjudication. Agreement and constituent structure must be combined.'),
17:('relative','nominal relative through participial modifier','quibus excipiatur modifies aluearia under habens, attached to accedat. Relative-pronoun case/gender/number candidates, a nominal antecedent and the participial argument span are observable hypotheses. The UD bridge itself is unavailable at inference.'),
18:('causal','causal clause after intervening relative and copula','aluearia meliora sunt ... quia non transmittunt combines a copular matrix, intervening relative and causal explanation. Copular-complex membership and clause/argument scope could support sunt rather than cross-sentence possunt.'),
19:('relative','relative on measurement phrase with modal structure','ea magnitudine quae ... non possit excedere links a relative to a measurement phrase, then the quantified clause under debebunt. This requires a nominal/quantifier bridge and a consistent modal-complement analysis; generic morphology existence flags do not encode them.'),
20:('conditional','conditional/modal plus intervening temporal clause','si apes obsidere uoluerint precedes utentur with an intervening cum ... defuerit clause. Closing the modal/infinitive span and distinguishing sibling subordinate clauses could identify the matrix; gold sentence membership is not an observable cue.'),
}


def run():
    load=lambda p:json.loads(p.read_text());samples,train,dev,source_predictions,devpred,adapter=observations()
    report=load(OUT/'report.json');path=TREEBANKS/'proiel-r2.17/la_proiel-ud-train.conllu'
    original,_=marker_sentences(path,'proiel');byid={s['sent_id']:s for s in original};deps={}
    for block in path.read_text().split('\n\n'):
        sid=next((l.split(' = ',1)[1] for l in block.splitlines() if l.startswith('# sent_id = ')),None)
        if sid:deps[sid]=[l.split('\t')[7] for l in block.splitlines() if l and not l.startswith('#') and l.split('\t')[0].isdigit() and l.split('\t')[3]!='PUNCT']
    metadata=load(Path('experiments/results/grammar-restoration/iteration9/sentence-complexes.json'))['development']
    complexes={s['sent_id']:s for s in metadata};cases=[]
    for case,contrast in enumerate(samples['development']['same_child'],1):
        p,n=contrast['positive'],contrast['negative'];gold=dev[p['stream']];start=0
        for info,end in zip(gold['sentences'],gold['boundaries']):
            if p['child']<end:break
            start=end
        sid=info['sent_id'];s=byid[sid];node=p['child']-start;chain=[]
        mapping={c['head']:c['representative'] for c in complexes[sid]['predicate_complexes']}
        bridge=[];reached=False
        while node is not None:
            representative=mapping.get(node,node if node in s['finite'] else None)
            chain.append({'position':node,'surface':s['tokens'][node],'upos':s['upos'][node],'deprel':deps[sid][node],
                'head':s['heads'][node],'projected_representative':representative})
            if representative==p['parent']-start:reached=True;break
            if representative!=p['child']-start and s['upos'][node] in ['NOUN','PROPN','PRON','NUM','ADJ'] and node!=p['child']-start:
                bridge.append(node)
            node=s['heads'][node]
        assert reached,(sid,p)
        positive=pair_rows([p],dev,devpred,adapter,True)[0];negative=pair_rows([n],dev,devpred,adapter,True)[0]
        difference=np.array(positive)-np.array(negative)
        family,subtype,note=NOTES[case]
        relevant=[i for i,w in enumerate(gold['tokens']) if start<=i<end and (w in ['qui','quae','quod','quibus','cui','quaecunque','cum','si','donec','ubi','quia'] or i in [start+j for j in bridge])]
        cases.append({'case':case,'stream':p['stream'],'sent_id':sid,'family':family,'subtype':subtype,'qualitative_note':note,
            'sentence_text':' '.join(gold['tokens'][start:end]),'child':p['child'],'child_surface':gold['tokens'][p['child']],
            'reference_parent':p['parent'],'reference_surface':gold['tokens'][p['parent']],
            'cross_parent':n['parent'],'cross_surface':gold['tokens'][n['parent']],
            'positive_distance':p['token_distance'],'negative_distance':n['token_distance'],'distance_matched':contrast['distance_matched'],
            'ud_to_projected_parent_path':chain,'nominal_bridge_positions':bridge,'predicate_complexes':complexes[sid]['predicate_complexes'],
            'predicted_markers':[m for m in devpred[p['stream']]['marker_attachments'] if start<=m['position']<end],
            'independent_morphology':[{'position':i,'surface':gold['tokens'][i],'readings':[{'pos':r.pos,'features':dict(r.features)} for r in adapter.analyze(gold['tokens'][i])]} for i in relevant],
            'feature_difference_counts':{name:int(np.count_nonzero(difference[lo:hi])) for name,lo,hi in [('geometry',0,2),('endpoint_windows',2,92),('between_summaries',92,122),('marker_flags',122,137)]},
            'classifier_preferences':{name:result['same_child_preference']['rows'][case-1] for name,result in report['evaluations'].items()},
            'inference_limit':'UD paths and complex membership are audit-only annotations, not available classifier inputs; proposed cues are hypotheses, not tested mechanisms'})
    audit={'cases':cases,'case_count':len(cases),'families':dict(Counter(c['family'] for c in cases)),
        'relative_cases_with_nominal_bridge':sum(c['family']=='relative' and bool(c['nominal_bridge_positions']) for c in cases),
        'scope':'all predetermined same-child development cases; qualitative construction review without expert adjudication or relabeling',
        'recommendation':'first test relative-pronoun/nominal-antecedent/governor bridges on controlled source contrasts, with committed morphology and explicit scope',
        'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'audit_code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    write_json(OUT/'construction-audit.json',audit);print('Audited',len(cases),'contrasts;',audit['families'],'nominal relative bridges',audit['relative_cases_with_nominal_bridge'])


if __name__=='__main__':run()
