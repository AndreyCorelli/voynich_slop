"""Independent exhaustive scoring, oracle bounds and cipher equivariance."""
from pathlib import Path
import hashlib
import numpy as np
from benchmarks.grammar_class_alignment_iteration25 import OUT,PREVIOUS,TREEBANK,RESERVE,load,strings,build_observations,produce,KEY,REKEY
from benchmarks.grammar_class_alignment_iteration25_evaluate import evaluate,confusion,metrics
from benchmarks.scalable_latin_caesar import words
from voynich_smt.class_alignment import tag_class,fit_source,maps,statistics


def independent_scores(source,sequences,m,bijective):
    candidates=maps(m,source['k'],bijective);s=statistics(sequences,m);logs={n:np.log(source[n]) for n in ('unigram','transition','start','end')}
    if bijective:
        inverse=np.argsort(candidates,axis=1)
        u=s['unigram'][inverse];t=s['transition'][inverse[:,:,None],inverse[:,None,:]];starts=s['start'][inverse];ends=s['end'][inverse]
        freq=(u*logs['unigram']).sum(axis=1)/max(1,s['unigram'].sum())
        event=max(1,s['transition'].sum()+s['start'].sum()+s['end'].sum())
        markov=((t*logs['transition']).sum(axis=(1,2))+(starts*logs['start']+ends*logs['end']).sum(axis=1))/event
        return candidates,dict(frequency=freq,markov=markov,joint=.5*freq+.5*markov)
    n=len(candidates);k=source['k'];index=np.arange(n);u=np.zeros((n,k));t=np.zeros((n,k,k));start=np.zeros((n,k));end=np.zeros((n,k))
    for a in range(m):
        u[index,candidates[:,a]]+=s['unigram'][a];start[index,candidates[:,a]]+=s['start'][a];end[index,candidates[:,a]]+=s['end'][a]
        for b in range(m):t[index,candidates[:,a],candidates[:,b]]+=s['transition'][a,b]
    norm=lambda x:(x+.5)/(x.sum(axis=1,keepdims=True)+.5*x.shape[1])
    def neg_js(p,q):
        q=np.asarray(q);r=.5*(p+q)
        return -.5*((p*np.log(p/r)).sum(axis=1)+(q*np.log(q/r)).sum(axis=1))
    freq=neg_js(norm(u),source['unigram']);trans=neg_js(norm(t.reshape(n,-1)),np.asarray(source['joint']).reshape(1,-1))
    boundary=.25*(neg_js(norm(start),source['start'])+neg_js(norm(end),source['end']))
    markov=((t*logs['transition']).sum(axis=(1,2))+(start*logs['start']+end*logs['end']).sum(axis=1))/max(1,s['unigram'].sum())
    return candidates,dict(frequency_fit=freq,joint_fit=freq+trans+boundary,markov=markov)


def validate():
    manifest=load(OUT/'manifest.json')
    for p,h in {**manifest['inputs'],**manifest['prior_declarations'],**load(OUT/'fit-freeze.json')['inputs']}.items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h,p
    data=load(OUT/'datasets.json');models=load(OUT/'models.json');observations=load(OUT/'observations.json');truth=load(OUT/'observation-truth.json');predictions=load(OUT/'predictions.json')
    prior=set().union(*(set(strings(load(Path(p)))) for p in manifest['prior_declarations']))
    reserved={r['sent_id'] for ss in load(RESERVE)['authors'].values() for r in ss};assert len(reserved)==200
    groups=[{s['sent_id'] for s in ss} for ss in data.values()]
    assert all(not a&b for i,a in enumerate(groups) for j,b in enumerate(groups) if i<j) and all(not g&reserved for g in groups)
    assert all(s['sent_id'] not in prior for split,ss in data.items() if split!='train' for s in ss)
    original={s['sent_id']:s for s in load(PREVIOUS/'datasets.json')['train']}
    assert all(s['tokens']==original[s['sent_id']]['tokens'] and s['upos']==original[s['sent_id']]['properties']['upos'] for s in data['train'])
    lookup={s['sent_id']:s for ss in data.values() for s in ss};found=set()
    for block in TREEBANK.read_text().split('\n\n'):
        lines=block.splitlines();sid=next((l.split(' = ',1)[1] for l in lines if l.startswith('# sent_id = ')),None)
        if sid not in lookup:continue
        kept=[l.split('\t') for l in lines if l and not l.startswith('#') and l.split('\t')[0].isdigit() and l.split('\t')[3]!='PUNCT']
        assert [words(r[1])[0] for r in kept]==lookup[sid]['tokens'] and [r[3] for r in kept]==lookup[sid]['upos'];found.add(sid)
    assert found==set(lookup)
    for name,selection in [('pooled',data['train']),('jerome',[s for s in data['train'] if s['author']=='Jerome']),('palladius',[s for s in data['train'] if s['author']=='Palladius'])]:
        for family,k in [('coarse',3),('fine',8)]:assert fit_source([[tag_class(t,family) for t in s['upos']] for s in selection],k)==models[name][family]
    assert build_observations(data,KEY)==(observations,truth)
    rekey,rekeytruth=build_observations(data,REKEY);assert rekey==load(OUT/'rekey-observations.json') and rekeytruth==load(OUT/'rekey-truth.json')
    assert produce(models,observations)==predictions;new=produce(models,rekey)
    obsindex={o['id']:o for o in observations};newindex={o['id']:o for o in rekey}
    checked=0
    for pred,other in zip(predictions,new):
        obs=obsindex[pred['id']];source=models[pred['template']]['coarse' if obs['family']=='frequency_proxy' else obs['family']]
        candidates,all_scores=independent_scores(source,obs['sequences'],obs['observed'],obs['bijective'])
        for method,result in pred['methods'].items():
            values=all_scores[method];best=values.max();optimal=candidates[values>=best-1e-10]
            assert abs(best-result['score'])<1e-10 and len(optimal)==result['optimal_maps']
            options=[sorted(set(int(v) for v in optimal[:,j])) for j in range(obs['observed'])];assert options==result['options']
            assert [x[0] if len(x)==1 else None for x in options]==result['mapping']
            oldseq=[[result['mapping'][x] for x in seq] for seq in obs['query_sequences']]
            newseq=[[other['methods'][method]['mapping'][x] for x in seq] for seq in newindex[obs['id']]['query_sequences']]
            assert oldseq==newseq;checked+=len(candidates)
    evaluation=evaluate(predictions,observations,truth,models);assert evaluation==load(OUT/'evaluation.json')
    gold={r['id']:r for r in truth}
    for row in evaluation:
        obs=obsindex[row['id']];table=confusion(obs['query_sequences'],gold[row['id']]['labels'],obs['observed'],obs['k']);candidates=maps(obs['observed'],obs['k'],obs['bijective'])
        best_accuracy=max(sum(table[j,candidates[:,j]] for j in range(len(table))))/table.sum()
        weights=table/np.maximum(1,table.sum(axis=0))[None,:]
        best_balanced=max(sum(weights[j,candidates[:,j]] for j in range(len(table))))/np.count_nonzero(table.sum(axis=0))
        assert abs(best_balanced-row['oracle']['balanced_accuracy']['metrics']['balanced_accuracy'])<1e-12
        assert abs(best_accuracy-row['oracle']['accuracy']['metrics']['accuracy'])<1e-12
        for method,result in row['methods'].items():
            assert result['accuracy']<=best_accuracy+1e-12
            assert result['balanced_accuracy']<=row['oracle']['balanced_accuracy']['metrics']['balanced_accuracy']+1e-12
    print(f'36 alignment problems replayed; {checked} objective/map scores independently checked; oracle ceilings and new-key equivariance verified; 200 reserved sentences unscored')

if __name__=='__main__':validate()
