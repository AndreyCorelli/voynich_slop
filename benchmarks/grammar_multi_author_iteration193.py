"""Frozen development-only leave-one-author-out applicability transfer."""
import re,unicodedata,itertools
from collections import defaultdict
from benchmarks.grammar_case_applicability_iteration180 import *
from benchmarks.inventory_latin_grammar_expansion import attribution
from benchmarks.grammar_case_subfamilies_iteration172 import score
OUT=ROOT/'iteration193'
DATA=Path('experiments/datasets/latin-grammar-expansion/v1')
AUTHORS=['Aquinas','Caesar','Cicero','Jerome','Palladius','Tacitus']
POLICY='Development only: six named authors; explicit new-development allowlist, legacy PROIEL corrected metadata; exclude original200 reserved sids. Never open UDante/LLCT/Perseus/Seneca rows. FORM-only admission: reject MWT sentences, normalize lowercase NFD diacritics j/i v/u; keep ASCII-letter forms, punctuation/nonletters create internal boundaries, no cross-sentence frames. Exact normalized lexical-sentence dedup: discard cross-author duplicates in all authors, retain first within-author. Sorted work round robin whole sentences, cap30000 lexical tokens/work and30000/author. floor5 endpoint types, >=2 distinct lexical-neighbor frames. Same180 nineteen features and .1 ridge; equal total training weight per author; source-only weighted standardization. Six LOAO models rich19/control3/prior, fixed .5 and top10/20 including ties. No entropy abstention or hyperparameter tuning. Freeze FORM admission/features before projecting Case; freeze all fold models/predictions before target metrics. Any single recognized Case in inventory, otherwise missing. Report applicability, conditional equality, distinct type coverage, calibration and no-prediction costs. Development transfer not unseen-author confirmatory evidence; tokenization differs from180. Reserved author FORM/labels remain unopened; reserve overlap check deferred to separate protocol.'

def norm(s):
    s=''.join(c for c in unicodedata.normalize('NFD',s.lower()) if unicodedata.category(c)!='Mn').replace('j','i').replace('v','u')
    return s if re.fullmatch('[a-z]+',s) else None

def blocks(path):
    meta={};lines=[]
    with path.open() as f:
        for line in itertools.chain(f,['\n']):
            if not line.strip():
                if lines:yield meta,lines
                meta={};lines=[]
            elif line.startswith('# '):
                if ' = ' in line:k,v=line[2:].rstrip().split(' = ',1);meta[k]=v
            else:lines.append(line.rstrip())

def admission():
    allow={(r['path'],r['sent_id']):(r['author'],r['work']) for r in load(DATA/'development-sentences.json')}
    reserve=load(Path('experiments/holdouts/grammar-construction-next.json'))
    protected={r['sent_id'] for rows in reserve['authors'].values() for r in rows}
    paths=sorted({p for p,s in allow}|{str(p) for p in Path('data/latin-grammar-benchmark/proiel-r2.17').glob('*.conllu')})
    groups=defaultdict(list);loss=Counter();owner=defaultdict(set)
    for path in paths:
        slug='proiel' if '/proiel-' in path else ('ittb' if '/ittb-' in path else 'circse')
        for meta,lines in blocks(Path(path)):
            sid=meta['sent_id']
            if slug=='proiel':
                a,w,_=attribution(slug,meta)
                if a not in AUTHORS or sid in protected:continue
            else:
                if (path,sid) not in allow:continue
                a,w=allow[path,sid]
            cells=[line.split('\t',2) for line in lines]
            if any('-' in c[0] for c in cells):loss['mwt_sentences']+=1;continue
            tokens=[dict(row=int(c[0]),word=norm(c[1])) for c in cells if c[0].isdigit()]
            lexical=[t['word'] for t in tokens if t['word']]
            if not lexical:continue
            key=hashlib.sha256(' '.join(lexical).encode()).hexdigest();owner[key].add(a)
            groups[(a,w)].append(dict(path=path,sent_id=sid,author=a,work=w,key=key,tokens=tokens,n=len(lexical)))
    selected={a:[] for a in AUTHORS}
    for a in AUTHORS:
        seen=set();works={w:iter(rows) for (aa,w),rows in sorted(groups.items()) if aa==a};used=Counter();total=0
        while works:
            for w in list(works):
                r=next(works[w],None)
                if r is None:del works[w];continue
                if len(owner[r['key']])>1:loss['cross_author_duplicate_sentences']+=1;continue
                if r['key'] in seen:loss['within_author_duplicate_sentences']+=1;continue
                seen.add(r['key'])
                if used[w]+r['n']>30000 or total+r['n']>30000:loss['budget_sentences']+=1;continue
                selected[a].append(r);used[w]+=r['n'];total+=r['n']
    return selected,dict(loss),paths

def graph(rows,a):
    ids=[];positions=[];boundary=hashlib.sha256((a+'|BOUNDARY').encode()).hexdigest()
    for r in rows:
        ids.append(boundary);positions.append(None)
        for t in r['tokens']:
            ids.append(hashlib.sha256((a+'|'+t['word']).encode()).hexdigest() if t['word'] else boundary)
            positions.append([r['path'],r['sent_id'],t['row']] if t['word'] else None)
    ids.append(boundary);positions.append(None);counts=Counter(ids)
    frames=defaultdict(lambda:defaultdict(list))
    for i in range(1,len(ids)-1):
        if positions[i] and counts[ids[i]]>=5 and ids[i-1]!=boundary and ids[i+1]!=boundary:frames[(ids[i-1],ids[i+1])][ids[i]].append(i)
    pairs=defaultdict(list)
    for frame,centers in sorted(frames.items()):
        for x,y in itertools.combinations(sorted(centers),2):pairs[(x,y)].append(dict(frame=list(frame),a_positions=centers[x],b_positions=centers[y]))
    dd=[dict(a=x,b=y,shared_frames=len(ff),frames=ff) for (x,y),ff in sorted(pairs.items()) if len(ff)>=2]
    return ids,positions,dd

def weighted_fit(raw,y,weights,cols):
    xx=np.array(raw)[:,cols];w=np.array(weights);w=w/w.sum();mean=w@xx;scale=np.sqrt(w@((xx-mean)**2));scale[scale<1e-12]=1
    x=np.column_stack([np.ones(len(xx)),(xx-mean)/scale]);y=np.array(y)
    def objective(b):
        z=x@b;pen=b.copy();pen[0]=0
        return float(w@(np.logaddexp(0,z)-y*z)+.05*(pen@pen)), x.T@(w*(expit(z)-y))+.1*pen
    result=minimize(objective,np.zeros(x.shape[1]),jac=True,method='L-BFGS-B',options=dict(maxiter=2000,ftol=1e-14,gtol=1e-9))
    grad=float(max(abs(objective(result.x)[1])));assert grad<1e-6,(result.message,grad)
    return dict(columns=cols,mean=mean.tolist(),scale=scale.tolist(),beta=result.x.tolist(),gradient_max=grad,strength=.1)

def run():
    assert not OUT.exists();OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    inputs=[Path(__file__),DATA/'verification-manifest.json',Path('experiments/holdouts/grammar-construction-next.json'),Path('benchmarks/grammar_case_applicability_iteration180.py')]
    save(OUT/'design-freeze.json',dict(policy=POLICY,authors=AUTHORS,inputs={str(p):digest(p) for p in inputs}))
    selected,loss,paths=admission();save(OUT/'admission.json',selected);save(OUT/'admission-audit.json',dict(losses=loss,raw_hashes={p:digest(Path(p)) for p in paths}))
    graphs={};ff={};refs={};sizes={}
    for a in AUTHORS:
        ids,pos,dd=graph(selected[a],a);graphs[a]=dict(ids=ids,positions=pos,descriptors=dd);ff[a]=features_for(ids,dd);sizes[a]=dict(sentences=len(selected[a]),lexical_tokens=sum(r['n'] for r in selected[a]),pairs=len(dd),types=len({e[k] for e in dd for k in ['a','b']}))
    save(OUT/'graphs.json',graphs);save(OUT/'features.json',ff);save(OUT/'feature-freeze.json',{n:digest(OUT/n) for n in ['graphs.json','features.json','admission.json']})
    # Decode Case only for selected development sentences, never other author roles.
    wanted={(r['path'],r['sent_id']) for rows in selected.values() for r in rows};cases={}
    for path in paths:
        for meta,lines in blocks(Path(path)):
            if (path,meta['sent_id']) not in wanted:continue
            for line in lines:
                c=line.split('\t')
                if c[0].isdigit():
                    feats=dict(p.split('=',1) for p in c[5].split('|') if '=' in p);case=feats.get('Case','');cases[(path,meta['sent_id'],int(c[0]))]=case if case in CASES else ''
    for a,g in graphs.items():
        cc=[cases[tuple(p)] if p else '' for p in g['positions']];refs[a]=score(g['descriptors'],cc,['X']*len(cc))['all'];sizes[a]['applicable_pairs']=sum(r['case_occurrence_pairs']>0 for r in refs[a])
    save(OUT/'development-references.json',refs)
    models={};pred={}
    for target in AUTHORS:
        train=[a for a in AUTHORS if a!=target and ff[a]];raw=[r['values'] for a in train for r in ff[a]];y=[int(r['case_occurrence_pairs']>0) for a in train for r in refs[a]];weights=[1/len(ff[a]) for a in train for r in ff[a]]
        models[target]={name:weighted_fit(raw,y,weights,cols) for name,cols in [('rich',list(range(19))),('frequency_support',CONTROL)]}
        prior=sum(w*t for w,t in zip(weights,y))/sum(weights);models[target]['prior']=dict(probability=prior)
        pred[target]={n:(predict(ff[target],m) if ff[target] else []) if n!='prior' else [prior]*len(ff[target]) for n,m in models[target].items()}
    save(OUT/'models.json',models);save(OUT/'predictions.json',pred);save(OUT/'prediction-freeze.json',{n:digest(OUT/n) for n in ['models.json','predictions.json']})
    summary={};selections={}
    for a,mm in pred.items():
        summary[a]={};selections[a]={};rr=refs[a];y=[int(r['case_occurrence_pairs']>0) for r in rr]
        for name,pp in mm.items():
            lists={'threshold':[i for i,p in enumerate(pp) if p>=.5]}
            for k in [10,20]:
                cut=sorted(pp,reverse=True)[min(k,len(pp))-1] if pp else None;lists['top'+str(k)]=[i for i,p in enumerate(pp) if p>=cut]
            selections[a][name]=lists;summary[a][name]=dict(classification=evaluate(y,pp) if pp else None,lists={n:metrics([rr[i] for i in ix],sizes[a]['types']) for n,ix in lists.items()})
    save(OUT/'sizes.json',sizes);save(OUT/'selections.json',selections);save(OUT/'summary.json',summary)
    print(json.dumps(sizes),flush=True)
    for a in AUTHORS:print(a,json.dumps({n:dict(auc=v['classification']['auc'] if v['classification'] else None,top10=v['lists']['top10']) for n,v in summary[a].items()}),flush=True)
if __name__=='__main__':run()
