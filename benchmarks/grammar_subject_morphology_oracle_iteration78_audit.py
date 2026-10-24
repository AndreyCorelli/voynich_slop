"""Replay oracle conditioning independently and verify source-only policies."""
from benchmarks.grammar_subject_morphology_oracle_iteration78 import *
def run():
    for p,h in load(OUT/'design-freeze.json')['inputs'].items():assert digest(p)==h,p
    for p,h in load(OUT/'calibration-freeze.json')['inputs'].items():assert digest(p)==h,p
    assert digest(OUT/'predictions.json')==load(OUT/'prediction-freeze.json')['predictions']
    cal=load(OUT/'calibration-predictions.json');pol=load(OUT/'policies.json')
    for arm in ARMS:assert select_policy(cal,'subject',arm)==pol[arm]
    m=load(ROOT/'iteration70/model.json');pm=load(ROOT/'iteration71/word-pos-model.json');lex=load(ROOT/'iteration23/morphology-lattice.json');lex.update(load(ROOT/'iteration1/morphology-lattice.json'));data=load(ROOT/'iteration44/annotations-truth.json');split=load(ROOT/'iteration49/manifest.json')['partitions']['0'];assert not set(split['fit'])&set(split['calibration']);source=[dict(sent_id=sid,**data[sid]) for sid in split['calibration']]
    assert json.loads(json.dumps(predictions(source,m,pm,lex,7701)))==cal
    old={(r['sid'],r['index']):r for r in load(ROOT/'iteration71/predictions.json')};rows=load(OUT/'predictions.json');assert len(rows)==1273
    for r in rows:
        b=old[r['sid'],r['index']];assert r['labels']['subject']==(b['role']=='nsubj');assert list(r['gold_profile'])==b['gold_profile']
        for name,q in [('context',posterior(m,b['context'])),('shuffle',posterior(m,b['shuffled_context'])),('prior',m['prior'])]:
            for full,kind in [(False,'pos'),(True,'profile')]:
                pairs=[(label,v) for label,v in zip(m['labels'],q) if (label[1]==b['gold_profile'] if full else label[1][0]==b['gold_profile'][0])];z=sum(v for _,v in pairs);expected=sum(v for (role,_),v in pairs if role=='nsubj')/z if z else 0
                assert abs(r['scores']['oracle_'+kind+'_'+name]['subject']-expected)<1e-12
    local={(r['sid'],r['index']):r for r in load(PREVIOUS/'predictions.json')};assert all(r['scores']['local']['subject']==local[r['sid'],r['index']]['scores']['local']['subject'] for r in rows)
    assert evaluation(rows,pol)==load(OUT/'evaluation.json')
    chosen=[r for r in rows if r['scores']['oracle_profile_context']['subject']>=pol['oracle_profile_context']['precision90']['threshold']]
    checked=0
    for path in ROOT.glob('iteration*/verification-manifest.json'):
        if path.parent==OUT:continue
        for p,h in load(path).get('inputs',{}).items():assert digest(p)==h,(path,p);checked+=1
    save(OUT/'audit.json',dict(calibration_replayed=len(cal),target_independent_replay=len(rows),prior_hashes_verified=checked,highprecision_target_types=len({r['word'] for r in chosen}),highprecision_target_sentences=len({r['sid'] for r in chosen}),calibration_fit_disjoint=True,reserve_unscored=True));print(load(OUT/'audit.json'))
if __name__=='__main__':run()
