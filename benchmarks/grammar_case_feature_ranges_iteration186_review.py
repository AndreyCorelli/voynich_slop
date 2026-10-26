"""Independent scalar range/geometry and all-cohort aggregation replay."""
from benchmarks.grammar_case_applicability_iteration180_review import close
from benchmarks.grammar_case_feature_ranges_iteration186 import *

def run():
    hashes=coordinates=aggregates=0
    for name in ['design-freeze','geometry-freeze']:
        for p,h in load(OUT/(name+'.json'))['inputs'].items():assert digest(p)==h;hashes+=1
    ff=load(ROOT/'iteration180/features.json');scales=load(ROOT/'iteration180/models.json')['rich']['scale'];ranges=load(OUT/'ranges.json');geometry=load(OUT/'geometry.json');summary=load(OUT/'summary.json');details=load(OUT/'target-details.json');cohorts=load(OUT/'cohorts.json');pred=load(ROOT/'iteration185/predictions.json');sel=load(ROOT/'iteration185/selections.json');rr=load(ROOT/'iteration172/details.json')['replication']['original']['all'];labels=[int(r['case_occurrence_pairs']>0) for r in rr]
    for scope,ix in [('full',list(range(52))),('minus21',[i for i in range(52) if i!=21])]:
        expected=[]
        for j,col in enumerate(COLS):
            values=[ff['earlier'][i]['values'][j] for i in ix];lo=min(values);hi=max(values);expected.append(dict(column=col,minimum=lo,maximum=hi,min_source_rows=[i for i in ix if ff['earlier'][i]['values'][j]==lo],max_source_rows=[i for i in ix if ff['earlier'][i]['values'][j]==hi]))
        assert expected==ranges[scope]
        for i,row in enumerate(ff['replication']):
            below=[];above=[];distances=[]
            for j,v in enumerate(row['values']):
                lo,hi=expected[j]['minimum'],expected[j]['maximum'];below.append(v<lo-1e-12);above.append(v>hi+1e-12);distances.append(lo-v if v<lo else v-hi if v>hi else 0.);coordinates+=1
            outside=[a or b for a,b in zip(below,above)];reconstructed=dict(index=i,below=below,above=above,outside=outside,raw_distances=distances,standardized_distances=[v/s for v,s in zip(distances,scales)],any_outside=any(outside),entropy_outside=any(outside[j] for j in [COLS.index('mean_left_entropy'),COLS.index('difference_left_entropy')]))
            close(reconstructed,geometry[scope][i])
    before=sel['0.0']['rich']['top10'];after=sel['1.0']['rich']['top10'];assert cohorts==dict(all=list(range(126)),omitted_top10=before,original_top10=after,departed=sorted(set(before)-set(after)),entered=sorted(set(after)-set(before)))
    def independent_aggregate(ix):
        return dict(n=len(ix),applicable=sum(labels[i] for i in ix),applicability=sum(labels[i] for i in ix)/len(ix) if ix else None,omitted_mean_probability=sum(pred['0.0']['replication']['rich'][i] for i in ix)/len(ix) if ix else None,original_mean_probability=sum(pred['1.0']['replication']['rich'][i] for i in ix)/len(ix) if ix else None)
    for scope,rows in geometry.items():
        for cohort,ix in cohorts.items():
            for measure in ['any_outside','entropy_outside']:
                for state,flag in [('outside',True),('inside',False)]:close(summary[scope][cohort][measure][state],independent_aggregate([i for i in ix if rows[i][measure]==flag]));aggregates+=1
        for j,col in enumerate(COLS):
            for state,flag in [('outside',True),('inside',False)]:close(summary[scope]['per_coordinate'][col][state],independent_aggregate([i for i in range(126) if rows[i]['outside'][j]==flag]));aggregates+=1
    for i,d in enumerate(details):
        assert d==dict(index=i,applicable=labels[i],omitted_probability=pred['0.0']['replication']['rich'][i],original_probability=pred['1.0']['replication']['rich'][i],full_outside=[c for c,v in zip(COLS,geometry['full'][i]['outside']) if v],minus21_outside=[c for c,v in zip(COLS,geometry['minus21'][i]['outside']) if v])
    save(OUT/'audit.json',dict(frozen_hashes_verified=hashes,source_coordinate_range_sets=38,target_coordinate_geometry_verified=coordinates,cohort_coordinate_metric_aggregations=aggregates,all_126_target_details_verified=True,all_masks_extrema_and_distances=True,no_refitting_or_abstention_applied=True))
    print('audit passed',coordinates,aggregates,flush=True)
if __name__=='__main__':run()
