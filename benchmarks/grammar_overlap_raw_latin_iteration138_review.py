"""Audit inspected-work provenance, opaque projection, nulls and reference metrics."""
from benchmarks.grammar_overlap_raw_latin_iteration138 import *
from benchmarks.grammar_context_overlap_iteration135_review import independent_stats,equal_stats

def run():
    hashes=0
    for name in ['design-freeze','input-freeze','predictions-freeze']:
        for p,h in load(OUT/(name+'.json'))['inputs'].items():assert digest(p)==h,p;hashes+=1
    assert load('experiments/results/scalable-latin-trigram/v1/confirmation-design.json')['fixture']=='livy-1';assert Path('experiments/results/scalable-latin-trigram/v1/confirmation-comparison.json').is_file();streams=load(OUT/'streams.json');selection=load(OUT/'selection.json');transforms=load(OUT/'transforms.json');saved=load(OUT/'statistics.json');pred=load(OUT/'predictions.json');summary=load(OUT/'summary.json');contrast=load(OUT/'contrasts.json');models=load(ROOT/'iteration135/models.json');cal=load(ROOT/'iteration135/calibrators.json');anchors=load(ROOT/'iteration85/anchor-budgets.json')['195'];words=load(ROOT/'iteration93/types.json')['candidates'];statchecks=probchecks=metricchecks=0
    assert set(streams)==set(WORKS)
    for work in WORKS:
        tokens=(CORPUS/(work+'.txt')).read_text().split();meta=load(CORPUS/(work+'.json'));assert digest(CORPUS/(work+'.txt'))==meta['normalized_sha256'];assert len(tokens)==meta['tokens'];lookup={w:hashlib.sha256(('raw138-'+work+'|'+w).encode()).hexdigest() for w in words};seq=[hashlib.sha256(('raw138-'+work+'|'+w).encode()).hexdigest() for w in tokens];assert seq==streams[work];s=selection[work];assert s['lookup']==lookup and s['candidate_counts']=={w:tokens.count(w) for w in words};assert s['missing_types']==sorted(w for w in words if w not in tokens);assert not s['sentence_support_available'];assert len(transforms[work])==17 and transforms[work]['original'] is None
        for name,indices in transforms[work].items():
            if name=='original':stream=seq
            else:
                seed=int(name[4:]);assert seed in NULL_SEEDS;assert indices==np.random.default_rng(seed).permutation(len(seq)).tolist();assert sorted(indices)==list(range(len(seq)));stream=[seq[i] for i in indices]
            assert Counter(stream)==Counter(seq);stats=independent_stats([dict(tokens=[dict(id=i) for i in stream])],set(lookup.values()));equal_stats(stats,saved[work][name]);statchecks+=len(stats)
            for arm,rows in pred[work][name].items():
                assert {r['opaque'] for r in rows}==set(stats)
                for r in rows:
                    assert r['n']==stats[r['opaque']]['n'] and r['supported']==(r['n']>=5) and r['support_kind']=='occurrence_only';value=stats[r['opaque']][arm];assert abs(value-r['statistic'])<1e-11;raw=predict_scalar(value,models[arm]['final']);assert abs(raw-r['probabilities']['raw'])<1e-10;assert abs(float(apply_offset([raw],cal[arm])[0])-r['probabilities']['new'])<1e-10;probchecks+=1
                for p,m in summary[work][name][arm].items():
                    q=np.array([r['probabilities'][p] for r in rows]);y=np.array([anchors[r['type']]=='CCONJ' for r in rows]);assert m['correct']==int(((q>.5)==y).sum());assert abs(m['nll']-float(-np.log(np.where(y,q,1-q)).mean()))<1e-12;assert m['auc']==float(np.mean((q[y,None]>q[~y][None,:])+.5*(q[y,None]==q[~y][None,:])));metricchecks+=1
        for arm,c in contrast[work].items():
            actual=summary[work]['original'][arm]['new'];assert actual==c['actual'];null=[summary[work]['word'+str(seed)][arm]['new'] for seed in NULL_SEEDS]
            for m in ['accuracy','nll','auc']:assert abs(c['null_mean'][m]-np.mean([r[m] for r in null]))<1e-12
            assert c['null_auc_range']==[min(r['auc'] for r in null),max(r['auc'] for r in null)];assert c['null_auc_at_least_actual']==sum(r['auc']>=actual['auc'] for r in null);assert c['null_accuracy_at_least_actual']==sum(r['accuracy']>=actual['accuracy'] for r in null)
        assert all(summary[work][name]['frequency']['new']==summary[work]['original']['frequency']['new'] for name in transforms[work]);print('audited',work,flush=True)
    four=load(OUT/'four-text-summary.json');previous=load(ROOT/'iteration137/contrasts.json');assert four=={'Caesar':previous['Caesar-expanded']['corrected']['concat'],'Jerome':previous['Jerome-expanded']['corrected']['concat'],**{w:contrast[w]['corrected']['actual'] for w in WORKS}}
    save(OUT/'audit.json',dict(input_hashes_verified=hashes,inspected_livy_provenance_verified=True,work_streams_and_34_transformations_reconstructed=True,independent_combinatorial_type_statistics=statchecks,probabilities_replayed=probchecks,metric_groups=metricchecks,exact_frequency_preservation_checked=True,four_text_table_replayed=True,no_fit_or_new_annotations=True));print(load(OUT/'audit.json'))
if __name__=='__main__':run()
