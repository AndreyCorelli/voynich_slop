"""Plaintext-revealed diagnostic on the unchanged full-vocabulary H1 positive."""
from dataclasses import asdict
import json
from pathlib import Path

from benchmarks.frozen_key_holdout import score
from benchmarks.l3_conflict import verify
from voynich_smt.cipher.base import Encoder
from voynich_smt.data.corpus import digest,write_json
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.models.text import Text
from voynich_smt.solver.recovery import _recover

SOURCE=Path('experiments/results/full-vocabulary-h1')
OUT=Path('experiments/results/full-vocabulary-h1-known')


def solve(plain,q):
    return _recover(plain,q.ciphertext,q.plaintext_alphabet,q.ciphertext_alphabet,
        q.bounds,q.timeout_ms,representation=q.representation,selection=q.selection,
        codeword_domains='observed')


def run():
    if (OUT/'protocol.json').exists():raise ValueError('Fixed diagnostic already started; preserve it')
    p=json.loads((SOURCE/'prepared.json').read_text());hidden=json.loads((SOURCE/'report.json').read_text())
    if not hidden['complete'] or hidden['prepared_sha256']!=digest(p):raise ValueError('Mismatched hidden diagnostic')
    q=HiddenRecoveryRequest.from_dict(p['requests']['full'])
    plain=Text(tuple(tuple(w) for w in p['truth']['plaintext']['words']))
    verify(q,p['truth'])
    previous=next(a for a in hidden['arms'] if a['id']=='full')
    if previous['request_sha256']!=digest(asdict(q)):raise ValueError('Unmatched full request')
    protocol={'source_sha256':digest(p),'hidden_report_sha256':digest(hidden),
        'request_sha256':digest(asdict(q)),'revealed_plaintext':asdict(plain),
        'timeout_ms':q.timeout_ms,'fits':1,
        'semantics':'Same training ciphertext, full alphabets, H1/L1-3, free selection, observed codeword domains and budget. Only training plaintext revealed, including its token counts. Key, lengths and segmentation hidden; no continuation/truth key passed to solver. Dictionary search removed; full dictionary retained for independent verification/scoring. This is a diagnostic, not hidden recovery success.',
        'code_sha256':{str(path):digest(path.read_text()) for path in
            (Path(__file__),Path('src/voynich_smt/solver/recovery.py'),Path('benchmarks/frozen_key_holdout.py'))}}
    write_json(OUT/'protocol.json',protocol)
    print(f'Known plaintext: {len(plain.words)} training words; budget={q.timeout_ms}ms',flush=True)
    result=asdict(solve(plain,q));verify(q,result)
    if result['status']=='UNSAT':raise RuntimeError('Independently checked known positive incorrectly UNSAT')
    report={'protocol':protocol,'hidden_status':previous['result']['status'],
            'result':result,'evaluation_status':'NOT_EVALUATED_NO_SAT','complete':True}
    if result['status']=='SAT':
        if tuple(tuple(w) for w in result['plaintext']['words'])!=plain.words:raise RuntimeError('Revealed plaintext changed')
        encoder=Encoder({s:tuple(tuple(c) for c in cs) for s,cs in result['encoder']['codebook'].items()})
        held=Text(tuple(tuple(w) for w in p['holdout']['words']))
        prediction=score(held,encoder,q.dictionary,q.ciphertext.words)
        exact=[w['fully_decoded'] and tuple(w['decoded_prefix'])==tuple(t)
               for w,t in zip(prediction['word_results'],p['holdout_plaintext']['words'])]
        if prediction['seen_ciphertext_words']!=0:raise RuntimeError('Continuation contains training repeats')
        report.update(prediction=prediction,exact_words=sum(exact),novel_exact_words=sum(exact),evaluation_status='EVALUATED_FROZEN_KEY')
    write_json(OUT/'report.json',report)
    print(result['status'],f"solver={result['runtime_seconds']:.2f}s",'exact='+str(report.get('exact_words')),flush=True)
    return report


if __name__=='__main__':run()
