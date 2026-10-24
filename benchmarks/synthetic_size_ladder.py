"""Fixed 5/10/15-word ladder on the saved Latin synthetic case."""
from dataclasses import asdict,replace
import json
from pathlib import Path
import hashlib

from benchmarks.frozen_key_holdout import score
from benchmarks.l3_conflict import verify
from voynich_smt.data.corpus import digest,write_json
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.cipher.base import Encoder
from voynich_smt.models.text import Text
from voynich_smt.solver.observed_codes import recover_observed_codes


def run():
    root=Path('experiments/results/predictive-calibration')
    manifest=json.loads((root/'prepared.json').read_text())
    entry=next(e for e in manifest['cases'] if e['id']=='latin-synthetic')
    payload=json.loads(Path(entry['public_input']).read_text())
    truth=json.loads(Path(entry['truth_path']).read_text())
    hold=json.loads(Path(entry['holdout']).read_text())
    for value,key in ((payload,'input_sha256'),(truth,'truth_sha256'),(hold,'holdout_sha256')):
        if digest(value)!=entry[key]:raise ValueError('Saved calibration input changed')
    base=HiddenRecoveryRequest.from_dict(payload['request'])
    continuation=Text(tuple(map(tuple,hold['ciphertext']['words'])))
    report={'manifest_sha256':digest(manifest),'sizes':[5,10,15],'timeout_ms':10000,
        'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'continuation':'Original words 31–52, identical across sizes; words after each short fitting prefix through word 30 are not fitted or evaluated.',
        'semantics':'One fixed seed/key/source, full dictionary and alphabet unchanged. UNKNOWN not failed prediction. A recovered short-prefix key may be ambiguous; no key repairs, retries or Voynich solves.',
        'experiments':[]}
    output=root/'size-ladder-10000ms.json'
    if output.exists():raise ValueError('Ladder already recorded; do not overwrite')
    for size in report['sizes']:
        q=replace(base,ciphertext=Text(base.ciphertext.words[:size]),timeout_ms=10000)
        plain=Text(tuple(tuple(w) for w in truth['plaintext']['words'][:size]))
        known={'status':'SAT','verified':True,'encoder':truth['encoder'],'plaintext':asdict(plain),
               'choices':truth['choices'][:plain.size],'nulls':[]}
        verify(q,known)
        print(f'Latin synthetic: {size} training words; budget=10000ms',flush=True)
        result=asdict(recover_observed_codes(q));verify(q,result)
        row={'training_words':size,'request_sha256':digest(asdict(q)),'result':result,
             'evaluation_status':'NOT_EVALUATED_NO_SAT'}
        if result['status']=='SAT':
            encoder=Encoder({s:tuple(tuple(c) for c in cs) for s,cs in result['encoder']['codebook'].items()})
            row['holdout_score']=score(continuation,encoder,q.dictionary,q.ciphertext.words)
            row['evaluation_status']='EVALUATED_FROZEN_KEY'
        report['experiments'].append(row);write_json(output,report)
        print(result['status'],f"solver={result['runtime_seconds']:.2f}s",flush=True)
        if result['status']=='UNSAT':raise RuntimeError('Checked positive reported UNSAT')
    report['complete']=True;write_json(output,report)
    return report


if __name__=='__main__':run()
