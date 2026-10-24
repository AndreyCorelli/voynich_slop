"""Sentence-held-out morphology probability features, with fixed candidate graphs."""
import copy
import hashlib
from voynich_smt.factor_morphology import probabilities,FEATURES as MORPH_FEATURES
from voynich_smt.source_morphology import group
from voynich_smt.construction_interventions import readings_key
from voynich_smt.multi_link_attachment import vector,STRUCTURAL,LOCAL


def sentence_fold(sid):
    return int(hashlib.sha256(sid.encode()).hexdigest(),16)%5


def inner_plan(fit_ids):
    ids=sorted(set(fit_ids));groups=sorted({sentence_fold(sid) for sid in ids})
    if len(groups)!=3:raise ValueError('Expected exactly three outer-fit sentence folds')
    result={}
    for j,g in enumerate(groups):
        other=groups[(j+1)%len(groups)]
        result[str(g)]=dict(held_ids=[sid for sid in ids if sentence_fold(sid)==g],crossfit_excluded=g,exposed_excluded=other)
    return result


def probability_map(tokens,model,cache):
    result={}
    for i,t in enumerate(tokens):
        if group(t['pos']) is None:continue
        key=readings_key(t)
        if key not in cache:cache[key]={feature:probabilities(model,t['word'],t['pos'],feature) for feature in MORPH_FEATURES}
        result[i]=cache[key]
    return result


def replace_probabilities(frames,tokens,probabilities_by_token):
    result=copy.deepcopy(frames);prefix=len(STRUCTURAL)+len(LOCAL)
    for frame in result:
        revised=[vector(tokens,frame['subject'],v,probabilities_by_token,'local_morph') for v in frame['predicates']]
        for before,after in zip(frame['vectors']['local_morph'],revised):assert before[:prefix]==after[:prefix]
        frame['vectors']['local_morph']=revised
    return result
