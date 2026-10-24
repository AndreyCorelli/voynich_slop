"""Independent marginal-probability replay and recorded serialization repair."""
from benchmarks.grammar_context_prediction_iteration74 import *
def run():
    fix=load(OUT/'serialization-fix.json');code=Path('benchmarks/grammar_context_prediction_iteration74.py');assert digest(code)==fix['corrected_code_hash']
    original=code.read_text().replace('zero_probability=int(sum(p==0 for p in prob))','zero_probability=sum(p==0 for p in prob)')
    assert hashlib.sha256(original.encode()).hexdigest()==fix['original_code_hash']
    for p,h in load(OUT/'design-freeze.json')['inputs'].items():
        if p.endswith('/grammar_context_prediction_iteration74.py'):assert h==fix['original_code_hash']
        else:assert digest(p)==h,p
    assert digest(OUT/'predictions.json')==load(OUT/'prediction-freeze.json')['predictions']
    rows=load(OUT/'predictions.json');old=load(ROOT/'iteration71/predictions.json');m=load(ROOT/'iteration70/model.json');assert len(rows)==len(old)==1273
    for r,b in zip(rows,old):
        assert all(r[k]==b[k] for k in ('sid','index','word','gold_profile'))
        for arm,p in [('context',posterior(m,b['context'])),('shuffle',posterior(m,b['shuffled_context'])),('prior',m['prior'])]:
            g=b['gold_profile'];pp=sum(q for (_,a),q in zip(m['labels'],p) if a[0]==g[0]);jp=sum(q for (_,a),q in zip(m['labels'],p) if a==g);s=r['predictions'][arm]
            assert np.allclose([pp,jp,jp/pp if pp else 0],[s['pos_probability'],s['joint_probability'],s['conditional_probability']],atol=1e-12,rtol=1e-12)
    assert evaluate(rows)==load(OUT/'evaluation.json')
    checked=0
    for path in ROOT.glob('iteration*/verification-manifest.json'):
        if path.parent==OUT:continue
        for p,h in load(path).get('inputs',{}).items():assert digest(p)==h,(path,p);checked+=1
    save(OUT/'audit.json',dict(independent_probability_replay=1273,prior_hashes_verified=checked,serialization_change_only=True,reserve_unscored=True));print(load(OUT/'audit.json'))
if __name__=='__main__':run()
