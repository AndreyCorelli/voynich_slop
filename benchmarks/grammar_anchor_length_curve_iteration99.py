"""Frozen source-only length curve, with and without matched candidate availability."""
from benchmarks.grammar_repair_abstention_iteration98 import *
from voynich_smt.anchor_length_curve import supported_words,length_blocks,curve_metrics,aggregate
OUT=ROOT/'iteration99';PREVIOUS=ROOT/'iteration98'


def summarize99(evaluation):
    groups={}
    for key,arms in evaluation.items():
        block,case=key.split('/');size=block.split('-')[0]
        for arm,row in arms.items():groups.setdefault(size,{}).setdefault(arm,[]).append(row)
    return {size:{arm:aggregate(rows) for arm,rows in arms.items()} for size,arms in groups.items()}


def run():
    assert not OUT.exists();OUT.mkdir();data=load(ROOT/'iteration44/annotations-truth.json');words=load(ROOT/'iteration93/types.json')['candidates'];anchors=load(ROOT/'iteration85/anchor-budgets.json')['195'];oldblocks=load(PREVIOUS/'blocks.json');blocks=length_blocks(oldblocks);hundred=[[dict(sent_id=sid,**data[sid]) for sid in oldblocks['scored']['sparse'+str(i)]] for i in range(8)];matched=sorted(set.intersection(*(supported_words(ss,words) for ss in hundred)));assert any(anchors[w]=='ADP' for w in matched) and any(anchors[w]=='CCONJ' for w in matched);save(OUT/'blocks.json',blocks);save(OUT/'matched-words.json',matched);(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text());paths=[Path(__file__),Path('src/voynich_smt/anchor_length_curve.py'),Path('src/voynich_smt/paired_anchor_class.py'),ROOT/'iteration44/annotations-truth.json',ROOT/'iteration49/manifest.json',ROOT/'iteration85/anchor-budgets.json',ROOT/'iteration93/models.json',ROOT/'iteration93/types.json',ROOT/'iteration95/policies.json',PREVIOUS/'verification-manifest.json',PREVIOUS/'blocks.json',PREVIOUS/'calibration-bank.json',OUT/'blocks.json',OUT/'matched-words.json']
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='SOURCECALONLY fixed93contextmodel,95jointcut.617467/support5occ3sentences/tieabstain. Nestedsourceblocksfrom98hashedfirst800:8x100,4x200,2x400,1x800; existing829fullasextraendpoint. Same800sentencesatprimary4levels, disjointwithinlevel/correlatedacrosslevels. Reuse98scoresat100/829, compute7newmergedblocks all64swaps+3controls=469newscenarios,1072total. Matchedtypeintersection acrossall8uncorrupted100blocks usingONLYpublicwordcount/sentencepresence, no classprediction/erroroutcomes; 8types/15crosspairs. Threearms:ALL64errors/allavailable16candidatepairs; SAME15matchederrors/allavailable16pairs; SAME15errors/fixed8candidatepairs. Matchedcontrolsad/de,que/sed+clean. Otheranchorsremainvisiblecontext evenwhenremovedascandidates. ReferenceattachedAFTERscores/selection. No threshold/size/modelselection; reportfullcurve hit/wrong/abstention/truepairsupport, rawunique-top1rankwithoutgaincut asdiagnostic, falsecontrolpairs. No PPintegration or author/sourceTEST/reserve/sealedtest evaluation, no newtraining/annotations. ReusedsourceCAL notfreshconfirmation, restricted singlebijectiveclassswap only.'))
    models=load(ROOT/'iteration93/models.json');bank=load(PREVIOUS/'calibration-bank.json');cut=load(ROOT/'iteration95/policies.json')['joint_context']['threshold'];evaluation={}
    for block,ids in blocks.items():
        folder=OUT/block;folder.mkdir();size,index=block.split('-');reuse=PREVIOUS/('sparse'+index if size=='100' else 'full') if size in ('100','829') else None;salt=('cal98-sparse'+index if size=='100' else 'cal98-full') if reuse else 'length99-'+block;sentences=[dict(sent_id=sid,**data[sid]) for sid in ids];public=ag.public_sentences(sentences,anchors,salt);matched_ids={t['id'] for s in public for t in s['tokens'] if t['anchor'] in matched};cache={}
        for j,(case,replacements) in enumerate(bank.items()):
            if reuse:scores=load(reuse/(case+'.json'))['scores'];origin=dict(reused=str(reuse/(case+'.json')))
            else:
                changed=perturb(public,replacements,anchors);sig=signature(changed)
                if sig not in cache:cache[sig]=pair_scores(changed,independent_records(changed,words,models),models)['joint_context']
                scores=cache[sig];origin=dict(computed=True)
            path=folder/(case+'.json');save(path,dict(scores=scores,origin=origin));save(folder/(case+'.freeze.json'),dict(inputs={str(path):digest(path)}));ref=reference_for(public,replacements,case.startswith('swap_'),scores,words);arms={'all':curve_metrics(scores,ref,cut)}
            if not ref['error'] or set(replacements)<=set(matched):
                arms['matched_errors_all_candidates']=curve_metrics(scores,ref,cut);restricted=[r for r in scores if set(r['pair'])<=matched_ids];arms['matched_errors_fixed_candidates']=curve_metrics(restricted,ref,cut)
                if ref['error']:assert arms['matched_errors_fixed_candidates']['reference_supported']
            evaluation[block+'/'+case]=arms
        print('completed size block',block,'sentences',len(ids),'reused' if reuse else 'computed',flush=True)
    save(OUT/'evaluation.json',evaluation);save(OUT/'summary.json',summarize99(evaluation));print(json.dumps(load(OUT/'summary.json'),indent=2))
if __name__=='__main__':run()
