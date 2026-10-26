"""Reproduce the complete204 edge-only row/tail comparison for205."""
from benchmarks.grammar_pivot_deletion_iteration205 import OUT,BUNDLE,load,save
from benchmarks.grammar_case_applicability_iteration180_review import close

def run():
    old=load(BUNDLE/'details.json');new=load(OUT/'details.json');count=0
    keys=['word','edges','degree','unique_frames','unique_pivot_occurrences','total_pivot_occurrence_uses','pivot_occurrence_reuse','min_unique_pivot_occurrences_after_edge_deletion','statistic','raw_tail','max_stat_tail','raw_detected','adjusted_detected']
    for a in old:
        for x,y in zip(old[a]['drop_strongest_sum'],new[a]['edge_only'],strict=True):close({k:x[k] for k in keys},{k:y[k] for k in keys});count+=1
    result=dict(passed=True,full_204_edge_only_rows_and_tails_replayed=count)
    if (OUT/'baseline-check.json').exists():assert load(OUT/'baseline-check.json')==result
    else:save(OUT/'baseline-check.json',result)
    print(result)
if __name__=='__main__':run()
