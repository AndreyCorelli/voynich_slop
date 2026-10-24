"""Compare the old relaxation on the exact coherent-grammar control pairs."""
from pathlib import Path
import hashlib
import json
from voynich_smt.data.corpus import write_json
from voynich_smt.grammar_diagnostic import GrammarScorer,BoundaryModel,LatinAdapter
from voynich_smt.word_mapping.morphology import WhitakerAnnotator
from benchmarks.grammar_restoration_iteration2 import OUT,FIXTURES


def run():
    fixtures=json.loads(FIXTURES.read_text())
    scorer=GrammarScorer(LatinAdapter(WhitakerAnnotator('data/vendor/whitakers-words')),BoundaryModel(9.483833303395006))
    rows=[]
    for pair in fixtures['pairs']:
        # Supplied single-clause diagnostic; no latent boundary confound.
        reference=scorer.score(pair['reference'].split(),latent=False)
        corrupted=scorer.score(pair['corrupted'].split(),latent=False)
        rows.append({'id':pair['id'],'split':pair['split'],'kind':pair['kind'],
            'reference':reference.total,'corrupted':corrupted.total,
            'delta':corrupted.total-reference.total,'component_delta':{
                k:corrupted.components[k]-reference.components[k] for k in reference.components}})
    write_json(OUT/'old-relaxation-control-ablation.json',{'rows':rows,
        'scope':'same authored controls; old unnormalized penalty ranking versus new restricted-parser feasibility, not matched probabilities',
        'old_intact_preferred':sum(r['delta']< -1e-9 for r in rows),
        'old_ties':sum(abs(r['delta'])<=1e-9 for r in rows),
        'old_corruption_preferred':sum(r['delta']>1e-9 for r in rows),
        'code_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),Path('src/voynich_smt/grammar_diagnostic.py')]}})
    print('Old relaxation:',sum(r['delta']< -1e-9 for r in rows),'of 16 intact references strictly preferred.')


if __name__=='__main__':run()
