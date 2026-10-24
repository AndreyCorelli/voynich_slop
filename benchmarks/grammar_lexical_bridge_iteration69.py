"""Gated truth-free lexical-score bridge from frozen subject-competition models."""
from pathlib import Path
from collections import Counter
import numpy as np
from benchmarks.grammar_joint_subject_none_iteration65 import OUT as COMP,UNIT,MORPH,SOURCE,RESERVE,load,save,digest,scored
from benchmarks.grammar_conj_competition_evidence_iteration68 import OUT as PREVIOUS
from benchmarks.grammar_multi_link_attachment_iteration52 import make_frames
from benchmarks.grammar_predicate_carriers_iteration56 import OUT as CARRIER
from voynich_smt.joint_subject_none import decode
from voynich_smt.conj_competition_evidence import adjust_contests
from voynich_smt.grammar_lexical_bridge import pos_model,candidate_tokens,objective_value,permutations,structural_lift
OUT=PREVIOUS.parent/'iteration69'
HISTORICAL=PREVIOUS.parent/'iteration1'
OLD_ORACLE=Path('experiments/results/word-mapping/grammar-oracle-calibration')
INVENTORY=Path('experiments/results/latin-large-dictionary/forms-100000.jsonl')
VARIANTS=('competition65','relative68')


class BridgeScorer:
    def __init__(self,pos,lexicon,morph,carrier,policy,probe,weight):
        self.pos=pos;self.lexicon=lexicon;self.morph=morph;self.carrier=carrier;self.policy=policy;self.probe=probe;self.weight=weight;self.morph_cache={};self.frame_cache={};self.score_cache={}

    def frames(self,words):
        key=tuple(words)
        if key not in self.frame_cache:
            tokens,origins=candidate_tokens(words,self.pos,self.lexicon);frames,_=make_frames('candidate',tokens,self.morph,self.morph_cache);frames=scored(frames,self.carrier['model']);self.frame_cache[key]=(tokens,origins,frames)
        return self.frame_cache[key]

    def raw(self,words,variant):
        if not words or variant not in VARIANTS:raise ValueError('Nonempty candidate words and a known variant are required')
        key=(tuple(words),variant)
        if key not in self.score_cache:
            tokens,origins,frames=self.frames(words);cutoff=self.policy['cutoff'];penalty=self.policy['selected']['carrier']['penalty']
            if variant=='relative68':frames=adjust_contests(frames,tokens,self.probe,self.weight,cutoff)
            p,stats=decode(frames,cutoff,penalty);parts=objective_value(frames,p,cutoff,penalty);self.score_cache[key]=dict(**parts,normalized=parts['total']/len(words),origins=origins,nominals=len(frames),tokens=len(words),pos=[t['pos'] for t in tokens],solver=stats)
        return self.score_cache[key]

    def score(self,words,variant):
        original=self.raw(words,variant);shuffled=[self.raw([words[j] for j in permutation],variant)['normalized'] for permutation in permutations(len(words),6)];frequency=float(np.mean([np.log((self.pos['counts'].get(w,0)+.5)/(self.pos['tokens']+.5*100000)) for w in words]))
        return dict(raw=original,shuffles=shuffled[:5],lift=structural_lift(original['normalized'],shuffled[:5]),shuffled_query_lift=structural_lift(shuffled[5],shuffled[:5]),source_frequency=frequency)


def build_scorer():
    data=load(SOURCE);ids=load(MORPH/'manifest.json')['partitions']['0']['fit'];assert all(data[sid]['author']!='Caesar' for sid in ids);pos=pos_model(data[sid]['tokens'] for sid in ids);morph=load(MORPH/'models.json')['0']['expanded'];carrier=load(CARRIER/'models.json')['0']['carrierfit_carriercal'];policy=load(COMP/'policies.json')['0'];record=load(PREVIOUS/'models.json')['0']['context'];lexicon=load(HISTORICAL/'morphology-lattice.json')
    return BridgeScorer(pos,lexicon,morph,carrier,policy,record['model'],record['policy']['selected']['weight'])


def candidate_audit():
    # Explicitly privileged, previously explored retrieval ceiling. No scorer or
    # search receives the original word's profile from this function.
    from benchmarks.word_mapping_anchor_recovery import resource_entries,PARENT,OUT as ANCHORS
    from voynich_smt.structural_oracle import StructuralOracle
    from voynich_smt.word_mapping.corpora import WordStream
    entries,records=resource_entries();forms=[r['surface'] for r in records];oracle=StructuralOracle(entries,{})
    reserved=set(load(ANCHORS/'runs/2000/anchors-1.0/seed-101/report.json')['supplied_anchors'].values());frequencies=Counter(w for segment in WordStream.load(PARENT/'splits/train.json').segments() for w in segment);eligible=[w for w in forms if w not in reserved and oracle.kind(w)=='content'];ranked=sorted(enumerate(eligible),key=lambda x:(-frequencies[x[1]],x[0]));ranked=[w for _,w in ranked];reference=load(OLD_ORACLE/'cases.json');targets=[r for r in reference if r['lexical'] and r['stage']=='full_analysis'];cases=[]
    for target in targets:
        gold=target['gold'];profile=oracle.profiles.get(gold,frozenset());pool=[w for w in ranked if profile&oracle.profiles.get(w,frozenset())];rank=pool.index(gold)+1 if gold in pool else None;rawrank=ranked.index(gold)+1 if gold in ranked else None
        assert len(pool)==target['candidates'] and rank==target['rankings']['frequency']['gold_rank']
        cases.append(dict(cipher=target['cipher'],gold=gold,available=gold in forms,unfiltered_rank=rawrank,full_analysis_candidates=len(pool),full_analysis_rank=rank))
    return dict(scope='Previously explored22known lexical types in2022-token Caesar excerpt; supplied function mappings; oracle full dictionary analysis, not inferred token grammar. Frequency uses original disjoint Caesar training books, separate from source69 structural-fit frequencies.',inventory_forms=len(forms),eligible=len(eligible),cases=cases,summary=dict(n=len(cases),available=sum(r['available'] for r in cases),unfiltered_top1=sum(r['unfiltered_rank']==1 for r in cases),unfiltered_top10=sum(r['unfiltered_rank'] is not None and r['unfiltered_rank']<=10 for r in cases),oracle_top1=sum(r['full_analysis_rank']==1 for r in cases),oracle_top10=sum(r['full_analysis_rank'] is not None and r['full_analysis_rank']<=10 for r in cases))),set(forms)


def summarize(rows):
    result={}
    for variant in VARIANTS:
        counts=Counter()
        for r in rows:
            for metric in ('lift','shuffled_query_lift','raw','source_frequency'):
                difference=r['aggregate'][variant][metric+'_intact_minus_corrupted'];counts[metric+('/intact' if difference>1e-10 else '/corrupted' if difference< -1e-10 else '/tied')]+=1
        result[variant]=dict(counts)
    primary=result['relative68'];passed=primary.get('lift/intact',0)>=8 and primary.get('lift/intact',0)>=primary.get('shuffled_query_lift/intact',0)+2
    return dict(moves=len(rows),crops=sum(len(r['crops']) for r in rows),comparison=result,primary='relative68/lift',gate_passed=passed,gate='At least8/10strictly prefer intact and at least2more wins than matched shuffled-query control; ties fail. Engineering falsification gate on reused historical corruptions, not statistical confirmation.',recovery_run_authorized_by_gate=passed,scope='Correct-dictionary local diagnostic over saved64-token crops, targets500to32000, no target sentence/POS/morph labels; no blind recovery or nucleus measured.')


def run():
    assert not OUT.exists()
    for p,h in load(PREVIOUS/'verification-manifest.json')['inputs'].items():assert digest(p)==h,p
    OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    from benchmarks.word_mapping_anchor_recovery import PARENT as WORD_PARENT,OUT as ANCHORS
    paths=[Path(__file__),Path('benchmarks/grammar_lexical_bridge_iteration69_audit.py'),Path('src/voynich_smt/grammar_lexical_bridge.py'),Path('tests/test_grammar_lexical_bridge.py'),Path('src/voynich_smt/joint_subject_none.py'),Path('src/voynich_smt/conj_competition_evidence.py'),Path('src/voynich_smt/conj_subject_evidence.py'),SOURCE,RESERVE,MORPH/'manifest.json',MORPH/'models.json',CARRIER/'models.json',COMP/'policies.json',PREVIOUS/'models.json',PREVIOUS/'verification-manifest.json',HISTORICAL/'first-corruptions.json',HISTORICAL/'morphology-lattice.json',OLD_ORACLE/'cases.json',INVENTORY,WORD_PARENT/'morphology.json',WORD_PARENT/'splits/train.json',ANCHORS/'runs/2000/anchors-1.0/seed-101/report.json',OUT/'proposal-design.md']
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},score='Truth-free hypothesis, not a validated word likelihood: optional carrier utility sum(score-cutoff)-lambda*extra-subject-count, normalized bytokens. Primary68relative correction vs65control. Grammatical lift subtracts mean5fixed position shuffles preserving wordmultiset. Sixth independent permutation is shuffledquery control. Sourceunigram meanlogfreq separate control, not combined withgrammar. No F1 or referenceparse enters score.',access='Fixed sourcefold0fit wordPOS counts, dictionary POS possibilities mappedtoUD withsourcepriorMAP fallback, unknownX. Candidate-word lookup only; no targetPOS/morphology/lemmas/dependencies/sentence boundaries. Predicted morphology49 and frozen56/65/67/68 model0. No target-based model/weightselection. Saved64token crops supply artificialflatwindows, not true sentenceboundaries. Common position permutations before/after; seed6901.',gate='Primary relative68lift must prefer intact in>=8of10historicalfirstcorruptions and beat shuffledquery winsby>=2. Ties fail. Evaluate all10moves/12crops, no removalforunknown words. If fail, stop dictionarysearch/nucleus attempt underthisscore. Ifpass, runmatchedretrieval/recovery as separatelyfrozen phase. Report raw65/68 scores and frequency sign controls; no postresultcombinationweights.',oracle='Separately replay existing22knownlexical Caesar retrieval cases and originalfullanalysis oracle filtering/ranks with originaldisjointtrainingfrequencies and suppliedfunctionmappings. Candidateavailability for100000forms. This is a privilegedresource ceiling on previously explored2022token excerpt, distinctfromhistoricalfirstcorruptioncontexts500to32000 and from grammar-score inputs. No oracleprofile is fed togrammar scorer.',reserve='Grammar200sentence reserve and any sealed lexicalfinaltest remainunscored; no new Caesar/Jerome grammar priorqueries.'))
    scorer=build_scorer();save(OUT/'pos-source-model.json',scorer.pos);audit,forms=candidate_audit();save(OUT/'candidate-audit.json',audit);moves=load(HISTORICAL/'first-corruptions.json');rows=[]
    for i,move in enumerate(moves):
        crops=[]
        for crop in move['crops']:
            records={variant:{version:scorer.score(crop[version+'_tokens'],variant) for version in ('before','after')} for variant in VARIANTS};crops.append(dict(start=crop['start'],end=crop['end'],before_tokens=crop['before_tokens'],after_tokens=crop['after_tokens'],scores=records))
        aggregate={}
        for variant in VARIANTS:
            total=sum(len(c['before_tokens']) for c in crops);metrics={}
            for metric in ('lift','shuffled_query_lift','raw','source_frequency'):
                def value(row):return row['raw']['normalized'] if metric=='raw' else row[metric]
                metrics[metric+'_intact_minus_corrupted']=sum(len(c['before_tokens'])*(value(c['scores'][variant]['before'])-value(c['scores'][variant]['after'])) for c in crops)/total
            aggregate[variant]=metrics
        rows.append(dict(target=move['target'],seed=move['seed'],changes=move['changes'],availability=[dict(**r,old_in100k=r['old'] in forms,new_in100k=r['new'] in forms) for r in move['changes']],crops=crops,aggregate=aggregate));print('Scored move',i,aggregate,flush=True)
    save(OUT/'first-corruption-scores.json',rows);save(OUT/'prediction-freeze.json',dict(inputs={str(p):digest(p) for p in OUT.glob('*.json')}));result=summarize(rows);save(OUT/'evaluation.json',result);save(OUT/'validation.json',dict(no_target_grammar_access=True,oracle_candidates_kept_separate=True,models_refitted=0,reserve_unscored=200,prior_queries_scored=0));print(result,flush=True)
if __name__=='__main__':run()
