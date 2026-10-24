"""Track previously reviewed errors and inspect revised-reference residuals."""
from collections import Counter
import hashlib
import json
from pathlib import Path
from benchmarks.grammar_predicate_complex_iteration9 import OUT,PREVIOUS
from voynich_smt.data.corpus import write_json

NEW_NOTES={
('13301','sunt'):'The relative factae sunt belongs inside factae essent. The revised reference now represents that parent at essent; the model still skips to egissent. This exposes a previously hidden nesting error.',
('160136','noceant'):'The negative-purpose clause ne ... noceant belongs to the main passive obligation sunt conterendae in the revised reference. The model chooses acuuntur in the intervening relative qua falces acuuntur.',
('160201','transmittunt'):'The quia clause depends on the copular main clause aluearia meliora sunt in the revised reference; formabit is inside the intervening relative. This remains a scope distinction after fixing copular projection.',
('160227','miseris'):'The si clause miseris is nested inside the ut clause possit; the model instead chooses sit in the outer inclinata sit clause.',
('160227','possit'):'The ut clause possit depends on the outer inclinated-stratum clause represented at sit. The model attaches it to miseris in the embedded si clause.',
}


def run():
    load=lambda p:json.loads(p.read_text());truth=load(OUT/'development-truth.json')
    rows=load(OUT/'predictions.json');selected={r['stream']:r for r in rows if (r['split'],r['model'],r['markers'],r['condition'])==('development','revised_gold','gold','both')}
    old=load(Path('experiments/results/grammar-restoration/iteration8/review.json'))['cases']
    tracking=[];notes={}
    for c in old:
        gold=truth[c['stream']];pred=selected[c['stream']]['prediction'];child=str(c['child']);reference=gold['parents'][child]
        tracking.append({'old_case':c['case'],'stream':c['stream'],'child':c['child'],'surface':c['child_surface'],
            'old_reference':c['reference_parent'],'revised_reference':reference,'old_chosen':c['chosen_parent'],
            'revised_chosen':pred['parents'][child],'unchanged_old_choice_matches_new_parent':c['chosen_parent']==reference,
            'new_prediction_correct':pred['parents'][child]==reference,'reference_changed':c['reference_parent']!=reference})
        updated={
            3:'The si clause factae essent belongs to egissent; the model selects sunt in its embedded relative. The si marker now correctly targets essent, so its previous omission has been repaired.',
            4:'The conditional factae fuissent depends on mansissent inside the quia clause; the model skips that level to descendes. The si marker now targets fuissent, but this does not repair the parent choice.',
            6:'The quia clause mansissent depends on descendes; choosing sunt makes it depend on an embedded relative. The repaired reference routes quia to mansissent and quae to sunt, so the old marker-projection error has been removed.'}
        notes[c['stream'],c['child']]=updated.get(c['case'],c['review_note'])
    residuals=[]
    for i,row in sorted(selected.items()):
        gold=truth[i]
        for local in row['audit']['per_child']:
            if local['error']=='correct_parent':continue
            child=local['child'];start=0
            for s,end in zip(gold['sentences'],gold['boundaries']):
                if child<end:break
                start=end
            note=notes.get((i,child),NEW_NOTES.get((s['sent_id'],gold['tokens'][child])))
            assert note is not None
            residuals.append({'sent_id':s['sent_id'],'stream':i,'child':child,'surface':gold['tokens'][child],
                'reference_parent':local['reference_parent'],'reference_surface':gold['tokens'][local['reference_parent']],
                'chosen_parent':local['chosen_parent'],'chosen_surface':gold['tokens'][local['chosen_parent']],
                'sentence_text':' '.join(gold['tokens'][start:end]),'local_audit':local,
                'candidates':row['prediction']['arc_candidates'][str(child)],'review_note':note})
    review={'scope':'development only, revised_gold/gold markers/both oracles; qualitative review, not expert adjudication',
        'previous_cases':tracking,'previous_cases_correct_under_revised_model':sum(c['new_prediction_correct'] for c in tracking),
        'previous_cases_relabeled_to_old_prediction':sum(c['reference_changed'] and c['unchanged_old_choice_matches_new_parent'] for c in tracking),
        'remaining_residuals':residuals,'residuals':len(residuals),'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    write_json(OUT/'review.json',review)
    print('Tracked',len(tracking),'previous cases;',review['previous_cases_relabeled_to_old_prediction'],'projection correction;',len(residuals),'current development residuals.')


if __name__=='__main__':run()
