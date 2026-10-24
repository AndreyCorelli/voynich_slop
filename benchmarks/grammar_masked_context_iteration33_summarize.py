"""Perturbation summaries of fixed contextual probes; no model selection."""
from benchmarks.grammar_masked_context_iteration33 import OUT,RATES,EPSILONS,load,save
from benchmarks.grammar_noisy_support_iteration30_evaluate import spread


def run():
    if (OUT/'summary.json').exists():raise ValueError('Preserve summary')
    results=load(OUT/'evaluation.json');out={}
    for arm in ('word','ending'):
        out[arm]={}
        for rate in RATES:
            out[arm][str(rate)]={}
            for epsilon in EPSILONS:
                rows=[r for r in results if r['arm']==arm and r['rate']==rate and r['epsilon']==epsilon];assert len(rows)==5;s={}
                for cohort in ('all_query','excluded_query','covered_query'):
                    s[cohort]={}
                    for mode in rows[0]['metrics']:
                        s[cohort][mode]={metric:spread([r['metrics'][mode][cohort][metric] for r in rows]) for metric in ('accuracy','balanced_accuracy','top2','top3','gold_probability','log_loss')}
                    s[cohort]['tokens']=spread([r['neighbor_audit'][cohort]['tokens'] for r in rows]);s[cohort]['neighbors_correct_fraction']=spread([r['neighbor_audit'][cohort]['neighbors_correct_fraction'] for r in rows])
                    for condition in ('correct_neighbors','wrong_neighbors'):
                        s[cohort][condition]={mode:dict(accuracy=spread([r['neighbor_audit'][cohort][condition][mode]['accuracy'] for r in rows]),tokens=spread([r['neighbor_audit'][cohort][condition][mode]['tokens'] for r in rows])) for mode in ('oracle_context','masked_neighbors','masked_hmm')}
                    s[cohort]['paired_vs_oracle']={mode:{key:spread([r['neighbor_audit'][cohort][mode+'_versus_oracle'][key] for r in rows]) for key in ('oracle_only_correct','mode_only_correct')} for mode in ('masked_neighbors','masked_hmm','oracle_context_with_emission','ordinary_hmm')}
                out[arm][str(rate)][str(epsilon)]=s
    save(OUT/'summary.json',out)
    for arm,rr in out.items():
        for rate,ee in rr.items():
            for epsilon,s in ee.items():
                print(arm,rate,epsilon,'neighbors',s['excluded_query']['neighbors_correct_fraction']['mean'])
                for mode in ('oracle_context','masked_neighbors','masked_hmm','oracle_context_with_emission','ordinary_hmm','class_frequency'):
                    m=s['excluded_query'][mode];print(mode,'accuracy',round(100*m['accuracy']['mean'],2),'balanced',round(100*m['balanced_accuracy']['mean'],2),'top2',round(100*m['top2']['mean'],2),'top3',round(100*m['top3']['mean'],2),'goldprob',round(m['gold_probability']['mean'],3))

if __name__=='__main__':run()
