"""Audit the frozen 23-word witness and test its used mappings on word 24."""
from dataclasses import asdict, replace
import json
from pathlib import Path
from time import perf_counter

from benchmarks.l3_conflict import verify
from voynich_smt.cipher.base import Encoder
from voynich_smt.data.corpus import digest, write_json
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.models.text import Text
from voynich_smt.solver.guided import recover_guided
from voynich_smt.solver.observed_codes import substrings


def main():
    path=Path('experiments/results/voynich-observed-codes-23-30min.json')
    saved=json.loads(path.read_text())
    request=HiddenRecoveryRequest.from_dict(saved['request'])
    result=saved['result']
    verify(request,result)
    prepared=json.loads(Path(saved['source_input']).read_text())
    payload={'request':asdict(request),'codeword_domains':saved['codeword_domains']}
    if digest(payload)!=saved['input_sha256'] or digest(prepared)!=digest(payload):
        raise ValueError('Prepared input or saved request checksum mismatch')
    encoder=Encoder({s:tuple(tuple(c) for c in cs) for s,cs in result['encoder']['codebook'].items()})
    plain=Text(tuple(tuple(w) for w in result['plaintext']['words']))
    used=sorted({s for w in plain.words for s in w})
    observed=set(substrings(request.ciphertext,request.bounds))
    emitted=[encoder.codebook[s][k] for s,k in zip((s for w in plain.words for s in w),result['choices'])]
    if any(c not in observed for c in emitted):
        raise ValueError('Emitted code absent from observed domains')
    offsets=[]
    cursor=0
    for word in plain.words:
        row=[0]
        for symbol in word:
            row.append(row[-1]+len(encoder.codebook[symbol][result['choices'][cursor]]))
            cursor+=1
        offsets.append(row)
    if offsets!=result['segmentation']:
        raise ValueError('Saved segmentation disagrees with emitted code lengths')
    scaling=json.loads(Path('experiments/results/sample-scaling.json').read_text())
    full=HiddenRecoveryRequest.from_dict(json.loads(Path(scaling['experiments'][-1]['public_input']).read_text()))
    if full.ciphertext.words[:23]!=request.ciphertext.words or len(plain.words)!=23:
        raise ValueError('Not the expected contiguous prefix')
    extension=replace(request,ciphertext=Text(full.ciphertext.words[:24]),timeout_ms=30000)
    guide={'encoder':asdict(encoder),'pinned_symbols':used,'rotate':False,
           'hint_symbols':[],'word_hints':{},'minimize_core':False}
    input_path=Path('data/generated/voynich-witness-extension/inputs/words-24-used-mappings.json')
    explicit={'request':asdict(extension),'guidance':guide}
    write_json(input_path,explicit)
    begin=perf_counter()
    extended=recover_guided(extension,encoder,pinned_symbols=used)
    verify(extension,asdict(extended))
    report={'schema_version':1,'source_report':str(path),'source_sha256':digest(saved),
            'independently_verified':True,'plaintext':[''.join(w) for w in plain.words],
            'ordered_codebook':{s:[''.join(c) for c in cs] for s,cs in encoder.codebook.items()},
            'used_symbols':used,'dictionary_caveat':'Frozen 5665-entry vocabulary includes English Gutenberg footer tokens by/of and Roman numerals; SAT is not a pure Latin text finding.',
            'extension':{'public_input':str(input_path),'input_sha256':digest(explicit),
                         'next_word':''.join(full.ciphertext.words[23]),'wall_seconds':perf_counter()-begin,
                         'result':asdict(extended),
                         'scope':'Conditional model: exact ordered homophone lists and counts for all used letters, including initial phase; unused completion letters free. UNSAT does not imply unrestricted 24-word UNSAT.'},
            'complete':True}
    write_json(Path('experiments/results/voynich-witness-extension.json'),report)
    print('Plaintext:', ' '.join(report['plaintext']))
    print('Extension:',extended.status,'solver seconds:',extended.runtime_seconds)
    print('Pinned core:',extended.capacity.get('pinned_unsat_core'))


if __name__=='__main__':
    main()
