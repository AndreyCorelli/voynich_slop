"""Frozen overlap signal without sentence boundaries and under word-order nulls."""
from benchmarks.grammar_context_overlap_iteration135 import *
OUT=ROOT/'iteration137';ORDER_SEEDS=[13700,13701,13702];NULL_SEEDS=list(range(13710,13726))

def run():
    assert not OUT.exists();OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),ROOT/'iteration135/verification-manifest.json',ROOT/'iteration135/models.json',ROOT/'iteration135/calibrators.json',ROOT/'iteration135/predictions.json',ROOT/'iteration136/verification-manifest.json',ROOT/'iteration118/public.json',ROOT/'iteration85/anchor-budgets.json',Path('src/voynich_smt/opaque_context_overlap.py'),Path('experiments/holdouts/grammar-construction-next.json')]+[p for vv in INPUTS.values() for p in vv.values()]
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='Frozen135anchor-free correctedoverlapclassmodel/calibrator/q>.5, NO PP/fitting. Same5contexts source770 andJerome/Caesar base/expanded. Eachcontext 1original-orderconcatwithoutANYsentenceboundary,3SHA-SIDsentenceorders seeds13700..2 thenconcat,16globalwordorderpermutations seeds13710..25 oforiginalconcatenatedIDs. Wordnullsexactlypreservetokens/typecounts/targetmembership, removeallorder; sentencereorderspreservewithin-sentenceorderbutcreateartificialjoins. Original135sentence-preservedpredictionsasreference. FreezeALLtransformationorders BEFOREstatistics; predictions BEFOREreferences/metrics. Primarycorrected, raw/frequencyfrozencontrolsreportednotselected. 100newviews, allpresenttypes, sameIDs/counts; supportbasedoriginalsentences forreportonly. Null rank/taildescriptiveNOTformalindependentpvalue, overlappingviews notnewdata. Checkbothhardaccuracy/NLL andAUC/distribution ofstatistic byclass; doNOTpickorder/targetcutoff. No suppliedanchors/tags infeatures, no newannotations/reserve/sealedlexicaltest/nuclei/default. Inheritedwordtokenization/catalogue remainprivileges; order-sensitive signalnotlanguageidentification.'))
    contexts={'source':load(ROOT/'iteration118/public.json')};contexts.update({a+'-'+v:load(p) for a,vv in INPUTS.items() for v,p in vv.items()});old=load(ROOT/'iteration135/predictions.json');models=load(ROOT/'iteration135/models.json');cal=load(ROOT/'iteration135/calibrators.json');transforms={};original_ids={};reserved={r['sent_id'] for rr in load('experiments/holdouts/grammar-construction-next.json')['authors'].values() for r in rr}
    for key,public in contexts.items():
        assert not {s['sent_id'] for s in public}&reserved;original_ids[key]=[t['id'] for s in public for t in s['tokens']];transforms[key]={};transforms[key]['concat']=dict(kind='sentence_order',sentence_ids=[s['sent_id'] for s in public])
        for seed in ORDER_SEEDS:transforms[key]['sentence'+str(seed)]=dict(kind='sentence_order',sentence_ids=sorted([s['sent_id'] for s in public],key=lambda sid:hashlib.sha256((str(seed)+'|'+sid).encode()).hexdigest()))
        for seed in NULL_SEEDS:transforms[key]['word'+str(seed)]=dict(kind='word_order',indices=np.random.default_rng(seed).permutation(len(original_ids[key])).tolist())
    save(OUT/'transforms.json',transforms);save(OUT/'transform-freeze.json',dict(inputs={str(OUT/'transforms.json'):digest(OUT/'transforms.json')}));allstats={};predictions={}
    for key,tt in transforms.items():
        byid={s['sent_id']:s for s in contexts[key]};lookup={r['type']:r['opaque'] for r in old[key]['corrected']};reference={r['type']:r for r in old[key]['corrected']};allstats[key]={};predictions[key]={}
        for name,transform in tt.items():
            seq=[t['id'] for sid in transform['sentence_ids'] for t in byid[sid]['tokens']] if transform['kind']=='sentence_order' else [original_ids[key][i] for i in transform['indices']];assert Counter(seq)==Counter(original_ids[key]);public=[dict(tokens=[dict(id=i) for i in seq])];st=statistics(public,set(lookup.values()));allstats[key][name]=st;predictions[key][name]={}
            for arm in ARMS:
                rows=[]
                for w,i in sorted(lookup.items()):
                    r=reference[w];raw=predict_scalar(st[i][arm],models[arm]['final']);rows.append(dict(type=w,opaque=i,n=r['n'],sentences=r['sentences'],supported=r['supported'],statistic=st[i][arm],probabilities=dict(raw=raw,new=float(apply_offset([raw],cal[arm])[0]),prior=.5)))
                predictions[key][name][arm]=rows
        print('predicted',key,flush=True)
    save(OUT/'statistics.json',allstats);save(OUT/'predictions.json',predictions);save(OUT/'predictions-freeze.json',dict(inputs={str(OUT/n):digest(OUT/n) for n in ['statistics.json','predictions.json']}));anchors=load(ROOT/'iteration85/anchor-budgets.json')['195'];summary={};contrast={}
    for key,tt in predictions.items():
        summary[key]={}
        for name,arms in tt.items():summary[key][name]={arm:{a:metrics([dict(r,**{'class':anchors[r['type']]}) for r in rows],a) for a in ['new','raw','prior']} for arm,rows in arms.items()}
        contrast[key]={}
        for arm in ARMS:
            original=metrics([dict(r,**{'class':anchors[r['type']]}) for r in old[key][arm]],'new');actual=summary[key]['concat'][arm]['new'];null=[summary[key]['word'+str(seed)][arm]['new'] for seed in NULL_SEEDS];orders=[summary[key]['sentence'+str(seed)][arm]['new'] for seed in ORDER_SEEDS];contrast[key][arm]=dict(sentence_preserved=original,concat=actual,sentence_orders=orders,null_mean={m:float(np.mean([r[m] for r in null])) for m in ['accuracy','nll','auc']},null_min={m:min(r[m] for r in null) for m in ['accuracy','nll','auc']},null_max={m:max(r[m] for r in null) for m in ['accuracy','nll','auc']},null_auc_at_least_concat=sum(r['auc']>=actual['auc'] for r in null),null_accuracy_at_least_concat=sum(r['accuracy']>=actual['accuracy'] for r in null))
        print('RESULT',key,contrast[key]['corrected'],flush=True)
    save(OUT/'summary.json',summary);save(OUT/'contrasts.json',contrast)
if __name__=='__main__':run()
