"""Matched plaintext-revealed diagnostic on saved synthetic prefixes."""
from dataclasses import asdict,replace
import hashlib
import json
from pathlib import Path

from benchmarks.frozen_key_holdout import score
from benchmarks.l3_conflict import verify
from voynich_smt.cipher.base import Encoder
from voynich_smt.data.corpus import digest,write_json
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.models.text import Text
from voynich_smt.solver.recovery import _recover

ROOT=Path('experiments/results/predictive-calibration')


def solve(plain,q):
    return _recover(plain,q.ciphertext,q.plaintext_alphabet,q.ciphertext_alphabet,
        q.bounds,q.timeout_ms,representation=q.representation,selection=q.selection,
        codeword_domains='observed')


def run():
    output=ROOT/'known-plaintext-ladder-10000ms.json'
    if output.exists():raise ValueError('Diagnostic already recorded; preserve it')
    m=json.loads((ROOT/'prepared.json').read_text())
    hidden=json.loads((ROOT/'size-ladder-10000ms.json').read_text())
    if digest(m)!=hidden['manifest_sha256']:raise ValueError('Hidden ladder source changed')
    entry=next(e for e in m['cases'] if e['id']=='latin-synthetic')
    public=json.loads(Path(entry['public_input']).read_text());truth=json.loads(Path(entry['truth_path']).read_text())
    held=json.loads(Path(entry['holdout']).read_text())
    for value,key in ((public,'input_sha256'),(truth,'truth_sha256'),(held,'holdout_sha256')):
        if digest(value)!=entry[key]:raise ValueError('Calibration artifact changed')
    base=HiddenRecoveryRequest.from_dict(public['request']);continuation=Text(tuple(map(tuple,held['ciphertext']['words'])))
    held_plain=tuple(map(tuple,truth['plaintext']['words'][30:]))
    report={'manifest_sha256':digest(m),'hidden_ladder_sha256':digest(hidden),
        'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'experiments':[],'timeout_ms':10000,
        'semantics':'Only training plaintext revealed. Key, code lengths, homophone choices and segmentation hidden; full alphabets, H2/L1–3 free model, observed domains and ten-second solver budget unchanged. No dictionary word search. Same original words 31–52 continuation, evaluated only after fitting. Not hidden-plaintext calibration success.'}
    for size in (5,10,15):
        q=replace(base,ciphertext=Text(base.ciphertext.words[:size]),timeout_ms=10000)
        plain=Text(tuple(map(tuple,truth['plaintext']['words'][:size])))
        verify(q,{'status':'SAT','verified':True,'encoder':truth['encoder'],'plaintext':asdict(plain),
            'choices':truth['choices'][:plain.size],'nulls':[]})
        previous=next(e for e in hidden['experiments'] if e['training_words']==size)
        if digest(asdict(q))!=previous['request_sha256']:raise ValueError('Unmatched request')
        print(f'Known plaintext: {size} words; budget=10000ms',flush=True)
        result=asdict(solve(plain,q));verify(q,result)
        row={'training_words':size,'request_sha256':digest(asdict(q)),'revealed_plaintext_sha256':digest(asdict(plain)),
            'hidden_result':previous['result']['status'],'result':result,'evaluation_status':'NOT_EVALUATED_NO_SAT'}
        if result['status']=='SAT':
            if tuple(map(tuple,result['plaintext']['words']))!=plain.words:raise RuntimeError('Known plaintext altered')
            encoder=Encoder({s:tuple(tuple(c) for c in cs) for s,cs in result['encoder']['codebook'].items()})
            prediction=score(continuation,encoder,q.dictionary,q.ciphertext.words)
            seen={s for w in plain.words for s in w};covered=[set(w)<=seen for w in held_plain]
            exact=[w['fully_decoded'] and tuple(w['decoded_prefix'])==expected
                   for w,expected in zip(prediction['word_results'],held_plain)]
            row.update(holdout_score=prediction,exact_generating_plaintext_words=sum(exact),
                holdout_words_with_only_seen_plaintext_symbols=sum(covered),
                exact_words_with_only_seen_plaintext_symbols=sum(ok and cover for ok,cover in zip(exact,covered)),
                evaluation_status='EVALUATED_FROZEN_KEY')
        report['experiments'].append(row);write_json(output,report)
        print(result['status'],f"solver={result['runtime_seconds']:.2f}s",flush=True)
        if result['status']=='UNSAT':raise RuntimeError('Checked known plaintext incorrectly UNSAT')
    report['complete']=True;write_json(output,report)
    return report


if __name__=='__main__':run()
