"""Oracle-vocabulary lexical ranking utility of a fixed coarse soft prior."""
from benchmarks.grammar_broad_author_iteration158 import *
OUT=ROOT/'iteration161';POSITIVE={'ADP','AUX','CCONJ','DET','PART','PRON','SCONJ'}

def rank_metrics(scores,index):
    value=scores[index];lo=1+sum(x>value for x in scores);hi=sum(x>=value for x in scores);return dict(best_rank=lo,worst_rank=hi,midrank=(lo+hi)/2,reciprocal_midrank=2/(lo+hi),top1_guaranteed=hi<=1,top1_possible=lo<=1,top5_guaranteed=hi<=5,top5_possible=lo<=5)

def run():
    assert not OUT.exists();OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),ROOT/'iteration160/verification-manifest.json',ROOT/'iteration160/word-views.json',ROOT/'iteration160/references.json',ROOT/'iteration157/summary.json',ROOT/'iteration44/annotations-truth.json',ROOT/'iteration49/manifest.json',Path('experiments/holdouts/grammar-construction-next.json')]
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='ControlledORACLEexactplaintextvocabulary suppliedperauthor/view, allwordtypes inclrare candidates, correctcandidatealwaysavailable but optimizer/ranker sees no queryidentity. Original+joined1604authors=8views allreported. Queries frequency>=10thlargest supported(n>=5)count, INCLUDEALLboundaryties toavoidplaintexttieprivilege; nominaltop10may>10. Fixedq=.8fromsource157top10finding, nottargetselected; ALLqueriespositivecoarseprior nooutsidequeries/negativeevidence. SOURCE44partition0fit only unigramcounts/modePOS .8purity for candidatelexicon sevenPOSunion; ambiguity/OOVunknown gets0logLR, neverfiltered. Frequencybaseline Poisson countmatch logscore n*log(rate)-Ntarget*rate, rate=(source_count+.5)/(sourceN+.5*(sourceV+1)), samefixedunknownrate, no targetfrequencyperplaintextcandidate used. Prioradds log(2q) ifsourceclasspositive/log(2(1-q)) negative/0unknown, fixedweight1. Sourcelexicon frozenbeforetargetinput, wordviews/candidatevocab/queryopaqueIDs/counts frozenbeforeallscorearrays; allscores frozenBEFOREcorrectmapping/targetreferences evaluation. Candidatelexiconplaintextnames allowedoracle, cipherquerywordmeaning neverinputto scoring. Report perquerytruecandidatebest/worst/midrank, reciprocalMIDrank(notexpectedMRR), top1/5guaranteed/possible bounds, improved/tied/worsened andsourcelexiconcoverage/mismatch. No candidatepruning/fullassignment/retrievalclaim/default/nuclei/generalPOS. Reuseddevelopmenttexts, frequencyderivedprior notindependentcontext evidence; testincrementalutility notassumesuccess. No newannotations/reserve/sealedworks.'))
    data=load(ROOT/'iteration44/annotations-truth.json');fit=load(ROOT/'iteration49/manifest.json')['partitions']['0']['fit'];reserved={r['sent_id'] for rr in load('experiments/holdouts/grammar-construction-next.json')['authors'].values() for r in rr};assert not set(fit)&reserved;counts=Counter();tags={}
    for sid in fit:
        for t in data[sid]['tokens']:counts[t['word']]+=1;tags.setdefault(t['word'],Counter())[t['pos']]+=1
    lexicon={}
    for w,c in tags.items():
        tag,n=sorted(c.items(),key=lambda x:(-x[1],x[0]))[0]
        if n/counts[w]>=.8:lexicon[w]=dict(modal=tag,label=int(tag in POSITIVE),count=counts[w],purity=n/counts[w])
    source=dict(counts=dict(counts),lexicon=lexicon,N=sum(counts.values()),V=len(counts),alpha=.5,q=.8);save(OUT/'source.json',source);save(OUT/'source-freeze.json',dict(inputs={str(OUT/'source.json'):digest(OUT/'source.json')}));views=load(ROOT/'iteration160/word-views.json');inputs={};identity={}
    for author,vv in views.items():
        for view,ss in vv.items():
            key=author+'/'+view;tokens=[w for s in ss for w in s['words']];cc=Counter(tokens);supported=[n for n in cc.values() if n>=5];cut=sorted(supported,reverse=True)[min(10,len(supported))-1];candidates=sorted(cc);querywords=sorted(w for w,n in cc.items() if n>=cut);lookup={w:hashlib.sha256(('utility161|'+key+'|'+w).encode()).hexdigest() for w in querywords};inputs[key]=dict(N=len(tokens),candidates=candidates,cutoff_count=cut,queries=[dict(opaque=lookup[w],n=cc[w]) for w in querywords]);identity[key]={i:w for w,i in lookup.items()}
    save(OUT/'inputs.json',inputs);save(OUT/'input-freeze.json',dict(inputs={str(OUT/'inputs.json'):digest(OUT/'inputs.json')}));scores={};den=source['N']+.5*(source['V']+1)
    for key,r in inputs.items():
        rates=np.array([(counts[w]+.5)/den for w in r['candidates']]);adjust=np.array([0. if w not in lexicon else math.log(1.6 if lexicon[w]['label'] else .4) for w in r['candidates']]);scores[key]={}
        for query in r['queries']:
            base=query['n']*np.log(rates)-r['N']*rates;scores[key][query['opaque']]=dict(baseline=base.tolist(),prior=(base+adjust).tolist())
    save(OUT/'scores.json',scores);save(OUT/'scores-freeze.json',dict(inputs={str(OUT/'scores.json'):digest(OUT/'scores.json')}));refs=load(ROOT/'iteration160/references.json');evaluation={};summary={}
    for key,rows in scores.items():
        author,view=key.split('/');r=inputs[key];evaluation[key]=[]
        for opaque,arms in rows.items():
            word=identity[key][opaque];index=r['candidates'].index(word);klass=lexicon.get(word);evaluation[key].append(dict(opaque=opaque,true_word=word,source_class=None if klass is None else klass['label'],target_host_class=refs[author][view]['host'][word],source_class_agrees=None if klass is None else klass['label']==refs[author][view]['host'][word],metrics={arm:rank_metrics(ss,index) for arm,ss in arms.items()}))
        rr=evaluation[key];summary[key]=dict(queries=len(rr),candidates=len(r['candidates']),source_class_known=sum(x['source_class'] is not None for x in rr),source_class_mismatches=sum(x['source_class_agrees'] is False for x in rr),improved=sum(x['metrics']['prior']['midrank']<x['metrics']['baseline']['midrank'] for x in rr),tied=sum(x['metrics']['prior']['midrank']==x['metrics']['baseline']['midrank'] for x in rr),worsened=sum(x['metrics']['prior']['midrank']>x['metrics']['baseline']['midrank'] for x in rr),metrics={arm:dict(mean_midrank=float(np.mean([x['metrics'][arm]['midrank'] for x in rr])),mean_reciprocal_midrank=float(np.mean([x['metrics'][arm]['reciprocal_midrank'] for x in rr])),**{k:sum(x['metrics'][arm][k] for x in rr) for k in ['top1_guaranteed','top1_possible','top5_guaranteed','top5_possible']}) for arm in ['baseline','prior']});print(key,summary[key],flush=True)
    save(OUT/'evaluation.json',evaluation);save(OUT/'summary.json',summary)
if __name__=='__main__':run()
