"""All-coordinate source-range coverage audit of frozen target predictions."""
from benchmarks.grammar_case_weight_path_iteration185 import *
OUT=ROOT/'iteration186'

def run():
    assert not OUT.exists();OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),ROOT/'iteration185/verification-manifest.json',ROOT/'iteration185/predictions.json',ROOT/'iteration185/selections.json',ROOT/'iteration180/features.json',ROOT/'iteration180/models.json',ROOT/'iteration172/details.json']
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='Diagnostic ranges, NO refit/abstention/model selection. Exact180 raw19feature coordinates, all52 source rows versus source excluding21; all126 target rows. Coordinate min/max closed intervals, outside if rawvalue<min-1e-12 or>max+1e-12, tolerance fixedabsolute1e-12. Record source min/max and extreme row IDs for each coordinate; target below/above indicators, raw excursions and distances in ORIGINAL180 rich scales. Full and minus21 any-coordinate violations and fixed entropy-only union coordinates mean_left_entropy/difference_left_entropy declared from185. Freeze ranges/all target geometry and masks before target labels. Fixed cohorts alltargets, original1.0top10, omitted0.0top10, and setdifference departed/entered from185; retain every row not merely four errors. Descriptive case-applicability rates and original/omitted probabilities by in/out mask, all-row details; no proposed coverage threshold chosen from labels or excluding targets to improve score. Per-coordinate violation applicability breakdown all19, no winner selection. Fixed1.0 and0.0 predictions only, not new confidence calibration. Sameauthor development/featurecorrelation/unseenregime not proof of wrong label; no new annotations/reserves/sealeddata or case/POS/nuclei recovery. Independent extrema/geometry/masks/count/probability replay required.'))
    ff=load(ROOT/'iteration180/features.json');raw=np.array([r['values'] for r in ff['earlier']]);target=np.array([r['values'] for r in ff['replication']]);scales=load(ROOT/'iteration180/models.json')['rich']['scale'];ranges={};geometry={}
    for name,ix in [('full',list(range(52))),('minus21',[i for i in range(52) if i!=21])]:
        source=raw[ix];lo=source.min(0);hi=source.max(0);ranges[name]=[dict(column=col,minimum=float(lo[j]),maximum=float(hi[j]),min_source_rows=[i for i in ix if raw[i,j]==lo[j]],max_source_rows=[i for i in ix if raw[i,j]==hi[j]]) for j,col in enumerate(COLS)];geometry[name]=[]
        for i,row in enumerate(target):
            below=row<lo-1e-12;above=row>hi+1e-12;distance=np.maximum(lo-row,0)+np.maximum(row-hi,0);geometry[name].append(dict(index=i,below=below.tolist(),above=above.tolist(),outside=(below|above).tolist(),raw_distances=distance.tolist(),standardized_distances=(distance/scales).tolist(),any_outside=bool(any(below|above)),entropy_outside=bool((below|above)[COLS.index('mean_left_entropy')] or (below|above)[COLS.index('difference_left_entropy')])))
    for n,obj in [('ranges',ranges),('geometry',geometry)]:save(OUT/(n+'.json'),obj)
    save(OUT/'geometry-freeze.json',dict(inputs={str(OUT/(n+'.json')):digest(OUT/(n+'.json')) for n in ['ranges','geometry']}))
    pred=load(ROOT/'iteration185/predictions.json');sel=load(ROOT/'iteration185/selections.json');before=sel['0.0']['rich']['top10'];after=sel['1.0']['rich']['top10'];cohorts={'all':list(range(126)),'omitted_top10':before,'original_top10':after,'departed':sorted(set(before)-set(after)),'entered':sorted(set(after)-set(before))};rr=load(ROOT/'iteration172/details.json')['replication']['original']['all'];labels=[int(r['case_occurrence_pairs']>0) for r in rr];summary={};details=[]
    def aggregate(ix):
        return dict(n=len(ix),applicable=sum(labels[i] for i in ix),applicability=sum(labels[i] for i in ix)/len(ix) if ix else None,omitted_mean_probability=sum(pred['0.0']['replication']['rich'][i] for i in ix)/len(ix) if ix else None,original_mean_probability=sum(pred['1.0']['replication']['rich'][i] for i in ix)/len(ix) if ix else None)
    for scope,rows in geometry.items():
        summary[scope]={}
        for cohort,ix in cohorts.items():
            summary[scope][cohort]={}
            for measure in ['any_outside','entropy_outside']:
                summary[scope][cohort][measure]={state:aggregate([i for i in ix if rows[i][measure]==flag]) for state,flag in [('outside',True),('inside',False)]}
        summary[scope]['per_coordinate']={col:{state:aggregate([i for i in range(126) if rows[i]['outside'][j]==flag]) for state,flag in [('outside',True),('inside',False)]} for j,col in enumerate(COLS)}
    for i in range(126):details.append(dict(index=i,applicable=labels[i],omitted_probability=pred['0.0']['replication']['rich'][i],original_probability=pred['1.0']['replication']['rich'][i],full_outside=[COLS[j] for j,v in enumerate(geometry['full'][i]['outside']) if v],minus21_outside=[COLS[j] for j,v in enumerate(geometry['minus21'][i]['outside']) if v]))
    save(OUT/'cohorts.json',cohorts);save(OUT/'summary.json',summary);save(OUT/'target-details.json',details)
    print(json.dumps({s:{k:v for k,v in cc.items() if k!='per_coordinate'} for s,cc in summary.items()}),flush=True)
if __name__=='__main__':run()
