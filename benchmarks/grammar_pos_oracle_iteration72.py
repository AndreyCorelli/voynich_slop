"""Privileged POS attribution on frozen lexical pairs; never a search score."""
from benchmarks.grammar_weighted_readings_iteration71 import weighted_mass
from benchmarks.grammar_role_compatibility_iteration70 import *
PREVIOUS=ROOT/'iteration71';OUT=ROOT/'iteration72'
def condition_pos(model,p,pos):
    q=np.array([v if label[1][0]==pos else 0. for label,v in zip(model['labels'],p)])
    return q/q.sum() if q.sum() else q

def within_weights(rr,pos):
    n=sum(r[0]==pos for r in rr)
    return [1/n if r[0]==pos else 0. for r in rr] if n else [0.]*len(rr)

def scores(model,r):
    pos=r['gold_profile'][0];rr=r['readings'];ww=r['weights'];within=[within_weights(a,pos) for a in rr];out={}
    for name,p in [('context',posterior(model,r['context'])),('shuffle',posterior(model,r['shuffled_context'])),('prior',model['prior'])]:
        q=condition_pos(model,p,pos)
        out['pos_oracle_weighted_'+name]=[weighted_mass(model,q,a,w) for a,w in zip(rr,ww)]
        out['pos_oracle_within_'+name]=[weighted_mass(model,q,a,w) for a,w in zip(rr,within)]
        out['pos_oracle_union_'+name]=[mass(model,q,a) for a in rr]
    out['pos_only_word_weight']=[sum(w for a,w in zip(aa,bb) if a[0]==pos) for aa,bb in zip(rr,ww)]
    out['pos_only_union']=[int(any(a[0]==pos for a in aa)) for aa in rr]
    out['oracle_morph']=r['scores']['oracle_morph'] if 'oracle_morph' in r['scores'] else [int(any(compatible(r['gold_profile'],a) for a in aa)) for aa in rr]
    out['baseline_weighted_context']=r['scores']['weighted_context']
    return out

def summarize(rows):
    arms={}
    for name in rows[0]['scores']:
        ds=[r['scores'][name][0]-r['scores'][name][1] for r in rows]
        arms[name]=dict(win=sum(d>1e-10 for d in ds),loss=sum(d< -1e-10 for d in ds),tie=sum(abs(d)<=1e-10 for d in ds));arms[name]['strict_accuracy']=arms[name]['win']/len(rows)
    return dict(n=len(rows),arms=arms)

def run():
    assert not OUT.exists();OUT.mkdir()
    for p,h in load(PREVIOUS/'verification-manifest.json')['inputs'].items():assert digest(p)==h,p
    paths=[Path(__file__),Path('benchmarks/grammar_weighted_readings_iteration71.py'),Path('benchmarks/grammar_role_compatibility_iteration70.py'),PREVIOUS/'predictions.json',ROOT/'iteration70/model.json',PREVIOUS/'verification-manifest.json',Path('experiments/holdouts/grammar-construction-next.json')]
    (OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='Fixed1273pairs and71weights; no refit. Supply gold coarse POS by zeroing otherPOS posterior labels and normalizing; zero if unsupported. Compare weighted context/prior/shuffle; union controls; uniform within-correctPOS readings removes candidatewordPOS prior to isolate Case/Number. POS-only supportedwordweight and binarysupport controls; full goldmorphology compatibility from70. Allarms privileged, no recovery/search authorized by oracle gains. Primary attribution: contextual versus prior/shuffle AFTER fixingPOS and versus POS-onlywordweight; report whole sample and analysis-covered subset without dropping failures fromprimary. No tuned parameters, no reserve scoring.'))
    m=load(ROOT/'iteration70/model.json');old=load(PREVIOUS/'predictions.json');rows=[dict(sid=r['sid'],index=r['index'],word=r['word'],other=r['other'],gold_profile=r['gold_profile'],scores=scores(m,r)) for r in old]
    save(OUT/'predictions.json',rows);save(OUT/'prediction-freeze.json',dict(predictions=digest(OUT/'predictions.json')))
    covered=[r for r in rows if r['scores']['oracle_morph'][0]==1];result=dict(all=summarize(rows),original_gold_analysis_present=summarize(covered),search_run=False,nuclei_measured=False,scope='Supplied referencePOS diagnostic on reused privileged pairs; cannot establish blind restoration.')
    save(OUT/'evaluation.json',result);print(json.dumps(result,indent=2))
if __name__=='__main__':run()
