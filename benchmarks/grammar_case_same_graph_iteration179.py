"""Frozen support10 versus random size-ten bundles from the same graphs."""
from benchmarks.grammar_case_pair_selection_iteration178 import *
OUT=ROOT/'iteration179'
SUBSET_SEEDS=list(range(179000,179999))
COMPARE=METRICS+['case_edges','case_types_involved','types_involved']

def run():
    assert not OUT.exists();OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),Path('benchmarks/grammar_case_pair_selection_iteration178.py'),ROOT/'iteration178/verification-manifest.json',ROOT/'iteration178/features.json',ROOT/'iteration178/selections.json',ROOT/'iteration178/summary.json',ROOT/'iteration172/details.json']
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},seeds=SUBSET_SEEDS,design='Candidate support10 frozen from178 fixed control (hypothesis observed on same development outcomes, NOT fresh validation), frequency10 fixed comparator, all-pair reference. Two SAME original primary graphs, no graph or label permutations. 999 random sizeTEN unique-edge subsets without replacement: numpy default_rng(seed).choice(N,10,replace=False), sorted; seeds179000..179998 independently initialized per pool. Freeze all sampled indices and fixed candidate lists BEFORE cached case scores. All exact178 tie-inclusive candidate support10/frequency10 lists must have ten edges; no truncation/tuning. Preserve each bundles172 within-frame then edge-macro score. Primary support10 ALL-POS edge_joint_yield versus999 random controls, corrected rank tail(1+>=actual)/1000 only all controls defined. All five172 strata, applicability/consistency/pair counts/type diversity and frequency10 comparisons secondary descriptive; retain empty-case subsets, conditional None never0, count nonempty controls explicitly, corrected conditional tail only all999 nonempty and actual defined. Save all per-subset summaries before contrasts; verify exact178 fixed baselines and independent subset/metric reconstruction. No new annotations/reserves/sealed data, POS/case inference or lexical nuclei. Random-list overlap/correlation and same-author development reuse explicit.'))
    old=load(ROOT/'iteration178/selections.json');features=load(ROOT/'iteration178/features.json');selections={}
    for pool in POOLS:
        n=len(features[pool]['original']);assert len(old[pool]['original']['support10'])==len(old[pool]['original']['frequency10'])==10
        selections[pool]={'support10':old[pool]['original']['support10'],'frequency10':old[pool]['original']['frequency10'],'all':list(range(n)),**{'random'+str(seed):sorted(np.random.default_rng(seed).choice(n,10,replace=False).tolist()) for seed in SUBSET_SEEDS}}
    save(OUT/'selections.json',selections);save(OUT/'selection-freeze.json',dict(inputs={str(OUT/'selections.json'):digest(OUT/'selections.json')}))
    cached=load(ROOT/'iteration172/details.json');summary={}
    for pool,nn in selections.items():
        gg=cached[pool]['original'];assert len(gg['all'])==len(features[pool]['original']);summary[pool]={name:{g:metrics([rr[i] for i in ix],588 if pool=='earlier' else 857) for g,rr in gg.items()} for name,ix in nn.items()}
    save(OUT/'summary.json',summary);contrasts={};inventory={}
    for pool,nn in summary.items():
        contrasts[pool]={};inventory[pool]={g:dict(Counter(str(nn['random'+str(seed)][g]['case_edges']) for seed in SUBSET_SEEDS)) for g in GROUPS}
        for candidate in ['support10','frequency10']:
            contrasts[pool][candidate]={}
            for g in GROUPS:
                contrasts[pool][candidate][g]={}
                for metric in COMPARE:
                    actual=nn[candidate][g][metric];values=[nn['random'+str(seed)][g][metric] for seed in SUBSET_SEEDS if nn['random'+str(seed)][g][metric] is not None];tail=sum(x>=actual for x in values) if actual is not None else None
                    contrasts[pool][candidate][g][metric]=dict(actual=actual,nonempty=len(values),mean=sum(values)/len(values) if values else None,min=min(values) if values else None,max=max(values) if values else None,at_least_actual=tail,descriptive_corrected_tail=(1+tail)/(1+len(SUBSET_SEEDS)) if actual is not None and len(values)==len(SUBSET_SEEDS) else None)
        print(pool,json.dumps(contrasts[pool]['support10']['all']),flush=True)
    save(OUT/'contrasts.json',contrasts);save(OUT/'random-case-edge-inventory.json',inventory)
if __name__=='__main__':run()
