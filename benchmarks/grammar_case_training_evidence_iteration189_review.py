"""Independent source evidence, scalar geometry and cohort audit."""
from benchmarks.grammar_case_applicability_iteration180_review import close
from benchmarks.grammar_case_training_evidence_iteration189 import *

def run():
    hashes=targets=aggregates=0
    for name in ['design-freeze','source-freeze','geometry-freeze']:
        for p,h in load(OUT/(name+'.json'))['inputs'].items():assert digest(p)==h;hashes+=1
    ff=load(ROOT/'iteration180/features.json');y=load(ROOT/'iteration180/source-labels.json');om=load(ROOT/'iteration188/omissions.json');sel=load(ROOT/'iteration188/selections.json');pred=load(ROOT/'iteration188/predictions.json');prior=load(ROOT/'iteration188/summary.json');evidence=load(OUT/'source-evidence.json');bounds=load(OUT/'source-bounds.json');geometry=gzload(OUT/'selected-geometry.json.gz');rows=load(OUT/'rows.json');cohorts=load(OUT/'cohorts.json');summary=load(OUT/'summary.json');scales=load(ROOT/'iteration180/models.json')['rich']['scale'];truth=[int(r['case_occurrence_pairs']>0) for r in load(ROOT/'iteration172/details.json')['replication']['original']['all']]
    parent=load(ROOT/'iteration188/design-freeze.json')['inputs'];assert digest(ROOT/'iteration180/models.json')==parent[str(ROOT/'iteration180/models.json')]
    for v,o in om.items():
        ix=o['training'];pos=[i for i in ix if y[i]];neg=[i for i in ix if not y[i]];counts=Counter(w for i in pos for w in [ff['earlier'][i]['a'],ff['earlier'][i]['b']]);assert evidence[v]==dict(training=len(ix),positives=len(pos),negatives=len(neg),positive_prevalence=len(pos)/len(ix),lost_positives=sum(y)-len(pos),positive_endpoint_types=len(counts),positive_incidence=dict(counts))
        for label,indices in [('positive',pos),('negative',neg),('all',ix)]:
            expected=dict(minimum=[min(ff['earlier'][i]['values'][j] for i in indices) for j in range(19)],maximum=[max(ff['earlier'][i]['values'][j] for i in indices) for j in range(19)]) if indices else None;assert bounds[v][label]==expected
        indices=sel[v]['left_entropy']['rich']['refill_top10'];assert [r['index'] for r in geometry[v]]==indices
        for record in geometry[v]:
            i=record['index'];point=ff['replication'][i]['values'];inside={label:[lo-1e-12<=x<=hi+1e-12 for x,lo,hi in zip(point,b['minimum'],b['maximum'])] if b else None for label,b in bounds[v].items()};dist={}
            for label,indices in [('positive',pos),('negative',neg)]:dist[label]=min(math.sqrt(sum(((ff['earlier'][j]['values'][k]-point[k])/scales[k])**2 for k in range(19))) for j in indices) if indices else None
            close(record,dict(index=i,prediction=pred[v]['rich'][i],inside=inside,positive_distance=dist['positive'],negative_distance=dist['negative']));targets+=1
        gg=geometry[v];non=[r for r in gg if not truth[r['index']]];app=[r for r in gg if truth[r['index']]];assert rows[v]==dict(**evidence[v],applicable=prior[v]['left_entropy']['arms']['rich']['lists']['refill_top10']['case_edges'],without_abstention=prior[v]['none']['arms']['rich']['lists']['refill_top10']['case_edges'],applicable_lost=prior[v]['left_entropy']['coverage']['applicable_lost'],noncase=len(non),noncase_probability_at_least_half=sum(r['prediction']>=.5 for r in non),noncase_inside_all_coordinates=sum(all(r['inside']['all']) for r in non),noncase_inside_positive_box=sum(all(r['inside']['positive']) for r in non),noncase_nearer_positive=sum(r['positive_distance']<r['negative_distance'] for r in non),applicable_inside_positive_box=sum(all(r['inside']['positive']) for r in app))
    allviews=[v for v in rows if v!='original'];expected_cohorts={'all':allviews}
    for name,lo,hi in [('positive_le9',0,9),('positive_10_12',10,12),('positive_13_15',13,15),('positive_ge16',16,52)]:expected_cohorts[name]=[v for v in allviews if lo<=rows[v]['positives']<=hi]
    for name,lo,hi in [('weak_le7',0,7),('applicable8',8,8),('applicable9',9,9)]:expected_cohorts[name]=[v for v in allviews if lo<=rows[v]['applicable']<=hi]
    assert cohorts==expected_cohorts
    for name,views in cohorts.items():
        r=summary[name];assert r['n']==len(views);assert r['distinct_training_masks']==len({tuple(om[v]['training']) for v in views});assert r['positive_count_histogram']==dict(Counter(str(rows[v]['positives']) for v in views))
        for field,s in r['fields'].items():
            vals=[rows[v][field] for v in views];assert s==dict(min=min(vals) if vals else None,max=max(vals) if vals else None,mean=sum(vals)/len(vals) if vals else None);aggregates+=1
    save(OUT/'audit.json',dict(frozen_hashes_verified=hashes,source_evidence_masks_verified=len(om),all_source_class_bounds_and_incidence=True,selected_target_geometry_records=targets,cohort_field_aggregates=aggregates,all_target_outcomes_and_partitions=True,full_source_scaling_hash_verified_from_frozen_parent=True,no_model_or_filter_changed=True))
    print('audit passed',targets,aggregates,flush=True)
if __name__=='__main__':run()
