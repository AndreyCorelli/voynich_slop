"""Source-only information test for structural government and nominative Case."""
from benchmarks.grammar_government_context_iteration80 import *
from voynich_smt.government_oracle import bundles
OUT=ROOT/'iteration81';PREVIOUS=ROOT/'iteration80';CASES={'Nom','Acc','Gen','Dat','Abl','Voc','Loc'}
ARMS=('baseline','pp','structure','pp_sham','structure_sham','prior')

def rows81(sentences,pm,lex,morph,seed):
    raw=dataset80(sentences,pm,lex,morph,seed);lookup={(r['sid'],r['index']):r for r in raw};result=[];rng=np.random.default_rng(seed+8100);excluded=0
    for s in sentences:
        ts=s['tokens'];pos=[candidate_pos(t['word'],pm,lex.get(t['word'],[]))[0] for t in ts];eligible=[]
        for i,t in enumerate(ts):
            if t['pos'] not in ('NOUN','PROPN','ADJ'):continue
            case=t['features'].get('Case')
            if case not in CASES:excluded+=1;continue
            r=lookup[s['sent_id'],i];pp,full=bundles(ts,pos,i);eligible.append(dict(sid=s['sent_id'],index=i,word=t['word'],labels={'nominative':case=='Nom'},baseline=r['anchors_features']+['suppliedCenterPOS:'+coarse(t['pos'])],pp_bundle=pp,structure_bundle=full))
        order=rng.permutation(len(eligible))
        for i,r in enumerate(eligible):
            r['pp']=r['baseline']+r['pp_bundle'];r['structure']=r['baseline']+r['structure_bundle'];r['pp_sham']=r['baseline']+eligible[order[i]]['pp_bundle'];r['structure_sham']=r['baseline']+eligible[order[i]]['structure_bundle'];result.append(r)
    return result,excluded

def score81(rows,models,prior):
    probabilities={a:probability([r[a] for r in rows],models[a.split('_sham')[0]]) for a in ARMS if a!='prior'}
    return [dict(sid=r['sid'],index=r['index'],word=r['word'],labels=r['labels'],scores={a:{'nominative':float(prior if a=='prior' else probabilities[a][i])} for a in ARMS}) for i,r in enumerate(rows)]

def run():
    assert not OUT.exists();OUT.mkdir()
    for p,h in load(PREVIOUS/'verification-manifest.json')['inputs'].items():assert digest(p)==h,p
    paths=[Path(__file__),Path('src/voynich_smt/government_oracle.py'),Path('src/voynich_smt/government_context.py'),Path('src/voynich_smt/contextual_nominative.py'),Path('benchmarks/grammar_government_context_iteration80.py'),ROOT/'iteration49/models.json',ROOT/'iteration70/model.json',ROOT/'iteration71/word-pos-model.json',ROOT/'iteration49/manifest.json',ROOT/'iteration44/annotations-truth.json',ROOT/'iteration1/morphology-lattice.json',ROOT/'iteration23/morphology-lattice.json',PREVIOUS/'verification-manifest.json',Path('experiments/holdouts/grammar-construction-next.json')]
    (OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='SOURCE ONLY:49fold0fit2471/cal829/test770declaredCicero/Palladius sentences; noCaesar targetscoring. Evaluate nominalNOUN/PROPN/ADJ withatomicCase in7knownclasses; reportexclusions. BinaryNomvsother. Supply truecentercoarsePOS toALLarms, nominalmembershipsupplied. Baseline80readableanchor/proximityfeatures. PP oracle truecase-linkedADP membership+identity/distance, inheritedonlyviaamod/conj/flat/fixed up to8edges. Structureoracle adds actualunlabeledhead candidatePOS+distance/root. No Case/Number/headmorph orsubject/objectrole supplied; labels whitelistcaseandinheritance only. L2.001/mincount3 logistic eachbaseline/PP/structure trainedsourcefitonly. Sham eval within-sentencepermutes oraclebundles amongeligiblenominals, baselinefixed; sameoracletrainedmodels, independentlysource-calibratedshampolicies. Prior control. SourcecalF1andprecision90samegrid/support. Freeze models/policies before sourceheldoutpredictions. Primarystructure oracle vs baseline andstructure_sham, PPablation. Oracle privilege not deployable restoration/absolute ceiling. Existing readable words/sentenceboundaries; no newtargetqueries/refitsupstream/reserve/sealedtest/search.'))
    pm=load(ROOT/'iteration71/word-pos-model.json');lex=load(ROOT/'iteration23/morphology-lattice.json');lex.update(load(ROOT/'iteration1/morphology-lattice.json'));morph=load(ROOT/'iteration49/models.json')['0']['expanded']['model'];data=load(ROOT/'iteration44/annotations-truth.json');part=load(ROOT/'iteration49/manifest.json')['partitions']['0'];assert all(data[sid]['author'] in ('Cicero','Palladius') for ids in part.values() for sid in ids)
    def prepare(split,seed):return rows81([dict(sent_id=sid,**data[sid]) for sid in part[split]],pm,lex,morph,seed)
    fitrows,fitexcluded=prepare('fit',7901);models={a:nfit([r[a] for r in fitrows],[r['labels']['nominative'] for r in fitrows]) for a in ('baseline','pp','structure')};prior=(sum(r['labels']['nominative'] for r in fitrows)+.5)/(len(fitrows)+1);save(OUT/'models.json',dict(models=models,prior=prior));save(OUT/'model-freeze.json',dict(models=digest(OUT/'models.json')))
    calrows,calexcluded=prepare('calibration',7701);cal=score81(calrows,models,prior);save(OUT/'calibration-predictions.json',cal);pol={'nominative':{a:select_policy(cal,'nominative',a) for a in ARMS}};save(OUT/'policies.json',pol);save(OUT/'calibration-freeze.json',dict(inputs={str(p):digest(p) for p in (OUT/'calibration-predictions.json',OUT/'policies.json')}))
    testrows,testexcluded=prepare('test',8101);test=score81(testrows,models,prior);save(OUT/'predictions.json',test);save(OUT/'prediction-freeze.json',dict(predictions=digest(OUT/'predictions.json')));result=evaluation(test,pol);result['scope']=dict(source_only=True,fit_n=len(fitrows),calibration_n=len(calrows),test_n=len(testrows),excluded_unknown_case=dict(fit=fitexcluded,calibration=calexcluded,test=testexcluded));save(OUT/'evaluation.json',result);print(json.dumps(result,indent=2))
if __name__=='__main__':run()
