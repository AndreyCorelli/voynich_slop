"""Replay independent class evidence and calibration; audit private-label separation."""
from benchmarks.grammar_anchor_class_audit_iteration91 import *

def compare_records(a,b):
    assert len(a)==len(b)
    for x,y in zip(a,b):
        for k in x:
            if k=='mean':assert np.allclose(x[k],y[k],rtol=1e-10,atol=1e-12)
            elif isinstance(x[k],float):assert math.isclose(x[k],y[k],rel_tol=1e-10,abs_tol=1e-12)
            else:assert x[k]==y[k],(k,x[k],y[k])

def run():
    for freeze in ('design-freeze.json','policy-freeze.json'):
        for p,h in load(OUT/freeze)['inputs'].items():assert digest(p)==h,p
    data=load(ROOT/'iteration44/annotations-truth.json');part=load(ROOT/'iteration49/manifest.json')['partitions']['0'];source=lambda split:[dict(sent_id=sid,**data[sid]) for sid in part[split]];catalogue=load(ROOT/'iteration85/anchor-budgets.json');anchors=catalogue['195'];candidates=load(OUT/'candidate-words.json');assert candidates==sorted(w for w,p in catalogue['20'].items() if p in ('ADP','CCONJ'));patterns=load(OUT/'patterns.json');assert patterns==challenge_patterns(source('fit'),catalogue['20']);models=load(BASE/'models.json');chosen=load(OUT/'policy.json');threshold=float('inf') if chosen['threshold'] is None else chosen['threshold'];cal={};summary={};cache=load(CACHE);decl=load(DECLARATION)['split_ids'];datasets={'calibration':source('calibration'),'source':source('test')};datasets.update({a:cached_sentences(cache,decl[a]) for a in AUTHORS})
    for name,sentences in datasets.items():
        salt='cal91' if name=='calibration' else 'eval91-'+name
        for pattern in (('correct','rehearsed_in_et') if name=='calibration' else patterns):
            rows,identities=prepare_audit(sentences,anchors,candidates,patterns[pattern],salt,models)
            if name=='calibration':stored=load(OUT/('calibration-'+pattern+'.json'));cal[pattern]=stored['records']
            else:
                folder=OUT/(name.lower()+'-'+pattern)
                for p,h in load(folder/'prediction-freeze.json')['inputs'].items():assert digest(p)==h,p
                stored=load(folder/'predictions.json');result=metrics(stored['records'],threshold);assert result==load(folder/'evaluation.json');summary[name+'/'+pattern]=result
            assert identities==stored['identities'];compare_records(rows,stored['records'])
        # Strip all reference POS/dependency data; context evidence must be unchanged.
        altered=[dict(sent_id=s['sent_id'],tokens=[dict(word=t['word']) for t in s['tokens']]) for s in sentences]
        baseline,_=prepare_audit(sentences,anchors,candidates,{},salt,models);changed,_=prepare_audit(altered,anchors,candidates,{},salt,models);compare_records(baseline,changed)
        print('replayed',name,flush=True)
    selected,curve=choose_threshold(cal['correct'],cal['rehearsed_in_et']);assert selected==chosen and curve==load(OUT/'calibration-curve.json');assert summary==load(OUT/'evaluation.json');checked=0
    for path in ROOT.glob('iteration*/verification-manifest.json'):
        if path.parent==OUT:continue
        for p,h in load(path).get('inputs',{}).items():assert digest(p)==h,(path,p);checked+=1
    bypos=defaultdict(Counter)
    for sentence in source('fit'):
        for t in sentence['tokens']:bypos[t['pos']]['visible' if t['word'] in anchors else 'hidden']+=1
    diagnostic={'fit_pos_by_visibility':{k:dict(v) for k,v in bypos.items()},'masked_type_distributions':{}}
    for path in [OUT/'calibration-correct.json']+list(OUT.glob('*-correct/predictions.json')):
        records=load(path)['records'];classes=models['pos_classes']
        diagnostic['masked_type_distributions'][str(path)]=dict(n=len(records),supported=sum(r['supported'] for r in records),minimum_mass=min(r['class_mass'] for r in records),maximum_mass=max(r['class_mass'] for r in records),binary_preferred=dict(Counter('ADP' if r['mean'][classes.index('ADP')]>=r['mean'][classes.index('CCONJ')] else 'CCONJ' for r in records)),top_pos=dict(Counter(classes[int(np.argmax(r['mean']))] for r in records)))
    assert diagnostic==load(OUT/'diagnostic-summary.json')
    save(OUT/'audit.json',dict(diagnostic_summary_verified=True,all26conditions_replayed=True,source_only_calibration_known_pair=True,hidden_entire_type_before_prediction=True,reference_annotation_removal_invariant=True,prior_input_hashes_verified=checked,reserve_unscored=True));print('audit passed',checked,'prior hashes')
if __name__=='__main__':run()
