"""Catalogue-held-out class model and type-held-out endpoint reliability veto."""
from benchmarks.grammar_evidence_attribution_iteration115 import *
from voynich_smt.masked_anchor_class import masked_type_features,cap_rows
from voynich_smt.endpoint_reliability import profile,pair_margin,veto
OUT=ROOT/'iteration116';CLASSES=['ADP','CCONJ']


def ordered(words,prefix):return sorted(words,key=lambda w:hashlib.sha256((prefix+'|'+w).encode()).hexdigest())


def train_class(public,train,hidden,lookup,anchors,balanced=False):
    rows={w:cap_rows(masked_type_features(public,hidden,lookup[w])) for w in train};xx=[r['features'] for w in train for r in rows[w]];y=[CLASSES.index(anchors[w]) for w in train for r in rows[w]]
    assert len(set(y))==2
    return ag.fit(xx,y,CLASSES),{w:[[r['sid'],r['index']] for r in rs] for w,rs in rows.items()}


def grouped_profile(public,words,lookup,hidden,model):
    masked=[dict(s,tokens=[dict(t,anchor=None,tag='X') if t['id'] in hidden else dict(t) for t in s['tokens']]) for s in public];wanted={lookup[w] for w in words};rows=[r for r in ag.public_features(masked) if r['word'] in wanted];q=ag.predict([r['features'] for r in rows],model);result={}
    for w in words:
        ix=[i for i,r in enumerate(rows) if r['word']==lookup[w]]
        if not ix:continue
        qs=q[ix,1];ns=len({rows[i]['sid'] for i in ix});result[w]=dict(profile=profile(qs,ns),mean=float(qs.mean()),n=len(ix),sentences=ns)
    return result


def apply_models(profiles,models,scaling,lookup):
    words=sorted(profiles);z=(np.array([profiles[w]['profile'] for w in words])-np.array(scaling['mean']))/np.array(scaling['scale']);result={a:{} for a in ['raw','reliability','balanced','prior','shuffle']}
    for a in ['reliability','balanced','shuffle']:
        q=ag.predict([['bias'] for w in words],models[a],soft=z)
        result[a]={lookup[w]:float(p[1]) for w,p in zip(words,q)}
    result['raw']={lookup[w]:profiles[w]['mean'] for w in words};result['prior']={lookup[w]:models['prior'] for w in words};return result


def make_cases(pool,records,literal,baseline,weights):
    allowed=set(pool);rows=[]
    def add(r,view,omit,physical,folder):
        pairs=r['pairs'];ii=[j for j,p in enumerate(pairs) if set(p['pair'])<=allowed and (omit is None or omit not in p['pair'])];z=np.load(folder/(r['case']+'.npz'));features=summarize([pairs[j] for j in ii],z['draws'][:,ii]);z.close();ref=dict(r['reference']);ref['supported']=any(pairs[j]['supported'] and pairs[j]['pair']==ref['pair'] for j in ii);proposed={i:t for p,tags in zip(pairs,r['proposed']) for i,t in zip(p['pair'],tags)};rows.append(dict(case=r['case'],regime=view,physical_view=physical,omitted=omit,features=features,reference=ref,proposed=proposed,base_pair=gate(features,baseline)))
    for r in records:
        if r['reference']['error'] and not set(r['reference']['pair'])<=allowed:continue
        add(r,'complete',None,'full',ROOT/'iteration102/full')
        for opaque in sorted(allowed):add(r,'omission',opaque,'full',ROOT/'iteration102/full')
    for r in literal:
        if r['removed_id'] not in allowed:continue
        if r['reference']['error'] and not set(r['reference']['pair'])<=allowed:continue
        add(r,'literal',None,r['removed_word'],ROOT/'iteration113'/r['removed_word'])
    return rows


def evaluate(rows,arm,cutoff):
    result={}
    for regime in ['complete','omission','literal']:
        rr=[r for r in rows if r['regime']==regime];s=dict(n=len(rr),hit=0,wrong=0,calls=0,clean_wrong=0,unsupported_wrong=0,distinct_hits=0);hitcases=set()
        for r in rr:
            p=r['base_pair'] if arm=='base' else veto(r['base_pair'],r['margins'][arm],cutoff);hit=p is not None and p==r['reference']['pair'];wrong=p is not None and not hit;s['hit']+=hit;s['wrong']+=wrong;s['calls']+=p is not None;s['clean_wrong']+=wrong and not r['reference']['error'];s['unsupported_wrong']+=wrong and r['reference']['error'] and not r['reference']['supported']
            if hit:hitcases.add(r['case'])
        s['distinct_hits']=len(hitcases);result[regime]=s
    return result


def run():
    assert not OUT.exists();OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    anchors=load(ROOT/'iteration85/anchor-budgets.json')['195'];types=load(ROOT/'iteration93/types.json');targets=types['candidates'];train=sorted(set(types['training'])-set(targets));cal=[];test=[]
    for tag in CLASSES:
        ws=ordered([w for w in targets if anchors[w]==tag],'reliability116');assert len(ws)==8;cal+=ws[:4];test+=ws[4:]
    folds={}
    for tag in CLASSES:
        for j,w in enumerate(ordered([w for w in train if anchors[w]==tag],'oof116')):folds[w]=j%3
    save(OUT/'type-split.json',dict(training=train,calibration=cal,evaluation=test,oof_folds=folds))
    paths=[Path(__file__),Path('src/voynich_smt/endpoint_reliability.py'),ROOT/'iteration49/manifest.json',ROOT/'iteration44/annotations-truth.json',ROOT/'iteration93/types.json',ROOT/'iteration85/anchor-budgets.json',ROOT/'iteration102/verification-manifest.json',ROOT/'iteration113/verification-manifest.json',ROOT/'iteration111/policies.json',OUT/'type-split.json']
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='SOURCE-ONLY strict typeheldout diagnostic, NOT default integration/independentfreshtext. Catalogue16 NEVERclass-model/reliabilitytraining labels or visibleidentities. Trainoutsidecatalogue13(10ADP3CCONJ) on49sourcefit words only; hideALL16catalogueIDs in ALLclassmodelinputs and hideowntype, OOF additionallyhideheld13types. Deterministicclass-stratified3fold13OOF, max20occpertype same92cap/L2solver. Finalclassmodelon13; reliabilityclasscalibrator on13OOF pooledprofiles: meanlogit, variance, fractionq>.5,meanentropy,log1pn,log1psentences; standardizeon13only. Naturaltypeequalweight andclassbalanced(eachclass30rows) calibrators, deterministictype-labelshuffle seed11677 and13typeclassprior controls; rawfinalclassmeancontrol. No identities/proposedclass in learnedfeatures. Catalogue16 split4ADP4CCONJcal vs4+4eval byfixedSHAseed, no labeloverlap. Beforeanyheldevalprediction, freezeperarmveto cutoff fromcal8ONLY. Pairproposals STILLfixed93cached102/113+111threshold; restrictcandidatepool8 andresummarizejointbootstrap, ALL16crossswaps+3controls perfull+8catalogueomissions+8literaldeletions=323conditionspersplit. Controls includeoriginalsameclassswaps regardlesspool. Endpointmodel predictsclassindependentcorruption sinceall16hidden; veto usesMINopposite/proposedlogmargin atselectedpair, no candidatechange. Gridallattainablecalminmargins plus0 and-inf(noaddedveto); eachregime>=90percentprecision, zeroclean/unsupportedwrong, >=80percentbasecorrect retained EACHregime, >=4completehits, >=4distinctomission/literalhitcases; maximizecompletehits,totalhits,minwrong,highercutoff. OFFifnone. Compareunchanged8poolbaseline, doNOTclaim16cataloguereliability. Reportcleanheldtypeaccuracy/NLL vscontrols; small13training andhidingcontextconfound explicit. Noauthor/PP/newannotations/reserve/sealedtest/cleanoracle subtraction/wordexception/targettuning/nuclei.'))
    data=load(ROOT/'iteration44/annotations-truth.json');part=load(ROOT/'iteration49/manifest.json')['partitions']['0'];sent=lambda key:[dict(sent_id=i,**data[i]) for i in part[key]];fit=ag.public_sentences(sent('fit'),anchors,'fit116');lookup={t['anchor']:t['id'] for s in fit for t in s['tokens'] if t['anchor'] is not None};hidden={lookup[w] for w in targets};oof={};provenance={};first={}
    for f in range(3):
        held=[w for w in train if folds[w]==f];tr=[w for w in train if folds[w]!=f];hid=hidden|{lookup[w] for w in held};m,prov=train_class(fit,tr,hid,lookup,anchors);first[str(f)]=m;provenance[str(f)]=dict(train=tr,held=held,sampled_rows=prov);oof.update(grouped_profile(fit,held,lookup,hid,m))
    final,prov=train_class(fit,train,hidden,lookup,anchors);provenance['final']=prov;first['final']=final;save(OUT/'class-models.json',first);save(OUT/'training-provenance.json',provenance);save(OUT/'oof-profiles.json',oof)
    x=np.array([oof[w]['profile'] for w in train]);mean=x.mean(0);scale=x.std(0);scale[scale<1e-12]=1.;z=(x-mean)/scale;y=np.array([CLASSES.index(anchors[w]) for w in train]);models={};models['reliability']=ag.fit([['bias'] for w in train],y,CLASSES,soft=z);ix=np.concatenate([np.tile(np.flatnonzero(y==c),30//int((y==c).sum())) for c in [0,1]]);models['balanced']=ag.fit([['bias'] for j in ix],y[ix],CLASSES,soft=z[ix]);yp=np.random.default_rng(11677).permutation(y);models['shuffle']=ag.fit([['bias'] for w in train],yp,CLASSES,soft=z);models['prior']=float(y.mean());scaling=dict(mean=mean.tolist(),scale=scale.tolist());save(OUT/'reliability-models.json',models);save(OUT/'scaling.json',scaling);save(OUT/'model-freeze.json',dict(inputs={str(p):digest(p) for p in [OUT/'class-models.json',OUT/'reliability-models.json',OUT/'scaling.json',OUT/'training-provenance.json',OUT/'oof-profiles.json']}))
    full=ag.public_sentences([dict(sent_id=i,**data[i]) for i in load(ROOT/'iteration98/blocks.json')['scored']['full']],anchors,'cal98-full');lookup={t['anchor']:t['id'] for s in full for t in s['tokens'] if t['anchor'] is not None};hidden={lookup[w] for w in targets};records=[r for r in load(ROOT/'iteration102/calibration-cases.json') if r['block']=='full'];literal=[dict(r,removed_id=lookup[r['removed_word']]) for r in load(ROOT/'iteration113/cases.json')];baseline=load(ROOT/'iteration111/policies.json')['full'];weights=None
    def prepare(words):
        cases=make_cases([lookup[w] for w in words],records,literal,baseline,weights);profiles={};probs={}
        for view in ['full']+words:
            public=full if view=='full' else load(ROOT/'iteration113'/('public-'+view+'.json'));profiles[view]=grouped_profile(public,words,lookup,hidden,final);probs[view]=apply_models(profiles[view],models,scaling,lookup)
        for r in cases:r['margins']={a:pair_margin(r['base_pair'],r['proposed'],probs[r['physical_view']][a]) for a in ['raw','reliability','balanced','prior','shuffle']}
        return cases,profiles,probs
    calibration,calprofiles,calprobs=prepare(cal);save(OUT/'calibration-cases.json',calibration);save(OUT/'calibration-profiles.json',calprofiles);save(OUT/'calibration-probabilities.json',calprobs);base_stats=evaluate(calibration,'base',None);chosen={};curves={}
    for arm in ['raw','reliability','balanced','prior','shuffle']:
        cuts=sorted({0.,float('-inf')}|{r['margins'][arm] for r in calibration if r['margins'][arm] is not None});curve=[]
        for cut in cuts:
            s=evaluate(calibration,arm,cut);ok=all(v['calls'] and v['hit']/v['calls']>=.9 and not v['clean_wrong'] and not v['unsupported_wrong'] and v['hit']>=math.ceil(.8*base_stats[g]['hit']) for g,v in s.items()) and s['complete']['hit']>=4 and s['omission']['distinct_hits']>=4 and s['literal']['distinct_hits']>=4;curve.append(dict(cutoff=cut,stats=s,qualified=ok))
        eligible=[r for r in curve if r['qualified']];chosen[arm]=max(eligible,key=lambda r:(r['stats']['complete']['hit'],sum(s['hit'] for s in r['stats'].values()),-sum(s['wrong'] for s in r['stats'].values()),r['cutoff'])) if eligible else dict(cutoff=None,qualified=False);curves[arm]=curve
    save(OUT/'calibration-baseline.json',base_stats);save(OUT/'chosen.json',chosen);save(OUT/'calibration-curves.json',curves);save(OUT/'policy-freeze.json',dict(inputs={str(p):digest(p) for p in [OUT/'chosen.json',OUT/'calibration-curves.json',OUT/'calibration-cases.json']}));print('CHOSEN',chosen,flush=True)
    evaluation,profiles,probs=prepare(test);save(OUT/'evaluation-cases.json',evaluation);save(OUT/'evaluation-profiles.json',profiles);save(OUT/'evaluation-probabilities.json',probs);save(OUT/'predictions-freeze.json',dict(inputs={str(p):digest(p) for p in [OUT/'evaluation-cases.json',OUT/'evaluation-profiles.json',OUT/'evaluation-probabilities.json']}));summary={'base':evaluate(evaluation,'base',None),**{a:evaluate(evaluation,a,r['cutoff']) for a,r in chosen.items()}};save(OUT/'evaluation-summary.json',summary);print('EVALUATION',summary,flush=True)
if __name__=='__main__':run()
