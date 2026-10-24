"""Replicate frozen context-length/core probe on the separate source-test partition."""
from benchmarks.grammar_anchor_length_curve_iteration99 import *
from voynich_smt.anchor_test_length import test_blocks
OUT=ROOT/'iteration100';PREVIOUS=ROOT/'iteration99'


def summarize100(evaluation):
    groups={}
    for key,arms in evaluation.items():
        block,case=key.split('/');size=block.split('-')[0]
        for arm,row in arms.items():groups.setdefault(size,{}).setdefault(arm,[]).append(row)
    return {n:{arm:aggregate(rows) for arm,rows in arms.items()} for n,arms in groups.items()}


def run():
    assert not OUT.exists();OUT.mkdir();data=load(ROOT/'iteration44/annotations-truth.json');part=load(ROOT/'iteration49/manifest.json')['partitions']['0'];assert len(part['test'])==770;blocks=test_blocks(part['test']);save(OUT/'blocks.json',blocks);core=load(PREVIOUS/'matched-words.json');save(OUT/'core.json',core);(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text());paths=[Path(__file__),Path('src/voynich_smt/anchor_test_length.py'),Path('src/voynich_smt/anchor_length_curve.py'),Path('src/voynich_smt/paired_anchor_class.py'),ROOT/'iteration44/annotations-truth.json',ROOT/'iteration49/manifest.json',ROOT/'iteration85/anchor-budgets.json',ROOT/'iteration93/models.json',ROOT/'iteration93/types.json',ROOT/'iteration95/policies.json',ROOT/'iteration98/calibration-bank.json',PREVIOUS/'verification-manifest.json',PREVIOUS/'matched-words.json',OUT/'blocks.json',OUT/'core.json']
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='SOURCE-TEST770separate49partition, previouslyreuseddevelopmentnotfreshsealedconfirmation. Frozen99core8types EXACT(no recertification/reselection),93classifier,95cut.617467/support5occ3sentences/tieabstain. Samehashcal98SID grouping:4x100,2x200,1x400 allsamefirst400testsentences; extra700prefix/full770endpoints,no invented800. All64crossswaps+3controls per9blocks=603cases. Samearms as99(all64/all16;15coreerrors/all16;15coreerrors/fixed8) evenifcorelosessupport innew100blocks: countunsupportederrors asmisses. SECONDARYevaluation-only common-supportedcoreerrorstratum, determinedfromuncorruptedpubliccounts acrossfour100blocks, NOT changingcorecandidatepool/classifier/cut or skippingANYperturbation; separatestruepartneravailability without reselectingrepaircore. ReportALLcurve, rawrank1, referenceavailability, controls, matched-subsetlimits. Referencesonlyafter publicscores. No retraining/calibration, PPintegration/author/reserve/sealedtest scoring ornewannotation. All195contextanchorssupplied.'))
    anchors=load(ROOT/'iteration85/anchor-budgets.json')['195'];words=load(ROOT/'iteration93/types.json')['candidates'];models=load(ROOT/'iteration93/models.json');bank=load(ROOT/'iteration98/calibration-bank.json');cut=load(ROOT/'iteration95/policies.json')['joint_context']['threshold'];hundreds=[[dict(sent_id=sid,**data[sid]) for sid in blocks['100-'+str(i)]] for i in range(4)];common=sorted(set(core)&set.intersection(*(supported_words(ss,words) for ss in hundreds)));save(OUT/'secondary-common-support.json',dict(words=common,not_reselected_candidates=True));evaluation={};availability={}
    for block,ids in blocks.items():
        folder=OUT/block;folder.mkdir();sentences=[dict(sent_id=sid,**data[sid]) for sid in ids];public=ag.public_sentences(sentences,anchors,'testlength100-'+block);core_ids={t['id'] for s in public for t in s['tokens'] if t['anchor'] in core};availability[block]=dict(core_supported=sorted(set(core)&supported_words(sentences,words)),n_sentences=len(ids));cache={}
        for case,replacements in bank.items():
            changed=perturb(public,replacements,anchors);sig=signature(changed)
            if sig not in cache:cache[sig]=pair_scores(changed,independent_records(changed,words,models),models)['joint_context']
            scores=cache[sig];path=folder/(case+'.json');save(path,dict(scores=scores));save(folder/(case+'.freeze.json'),dict(inputs={str(path):digest(path)}));ref=reference_for(public,replacements,case.startswith('swap_'),scores,words);arms={'all':curve_metrics(scores,ref,cut)}
            if not ref['error'] or set(replacements)<=set(core):
                restricted=[r for r in scores if set(r['pair'])<=core_ids];arms['core_errors_all_candidates']=curve_metrics(scores,ref,cut);arms['core_errors_fixed_candidates']=curve_metrics(restricted,ref,cut)
                if not ref['error'] or set(replacements)<=set(common):arms['common_support_errors_fixed_core']=curve_metrics(restricted,ref,cut)
            evaluation[block+'/'+case]=arms
        print('completed test block',block,'supported core',availability[block]['core_supported'],flush=True)
    save(OUT/'availability.json',availability);save(OUT/'evaluation.json',evaluation);save(OUT/'summary.json',summarize100(evaluation));print(json.dumps(load(OUT/'summary.json'),indent=2))
if __name__=='__main__':run()
