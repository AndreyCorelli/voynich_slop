"""Bounded shared-key gate with exact per-position expanded spellings."""
from dataclasses import asdict
import json
from pathlib import Path

from benchmarks.l3_conflict import verify
from voynich_smt.cipher.base import Bounds
from voynich_smt.data.corpus import digest,write_json
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.language.contractions import tokenizations,expand_units
from voynich_smt.language.dictionary import WordDictionary,CandidateGraph
from voynich_smt.models.alphabet import Alphabet
from voynich_smt.models.text import Text
from voynich_smt.solver.observed_codes import recover_observed_codes

OUT=Path('experiments/results/known-passage-keys')


class PositionedDictionary(WordDictionary):
    """Use existing symbolic solver while restricting every word position."""
    def __init__(self,positions):
        super().__init__(tuple(sorted({w for paths in positions for w in paths})))
        object.__setattr__(self,'positions',tuple(tuple(p) for p in positions))

    def candidate_graph(self,ciphertext,bounds,min_word_length,max_word_length):
        if len(ciphertext.words)!=len(self.positions):raise ValueError('Position count mismatch')
        graph=super().candidate_graph(ciphertext,bounds,min_word_length,max_word_length)
        candidates=tuple(tuple(w for w in allowed if w in graph.candidates[i])
                         for i,allowed in enumerate(self.positions))
        return CandidateGraph(candidates,graph.relations,graph.pruned_candidates)


def solve_case(words,cipher,rules,timeout_ms=10000,cipher_alphabet=None):
    positions=tuple(tokenizations(w,rules) for w in words)
    dictionary=PositionedDictionary(positions)
    alpha=Alphabet(tuple(sorted({s for w in dictionary.words for s in w})))
    cipher_alpha=cipher_alphabet or Alphabet(tuple(sorted({s for w in cipher.words for s in w})))
    request=HiddenRecoveryRequest(cipher,alpha,cipher_alpha,Bounds('verbose',2,1,3),dictionary,
                                  timeout_ms=timeout_ms)
    result=asdict(recover_observed_codes(request));verify(request,result)
    expanded=[]
    if result['status']=='SAT':
        paths=result['plaintext']['words']
        if not all(tuple(w) in positions[i] for i,w in enumerate(paths)):
            raise RuntimeError('Recovered path violates known position')
        expanded=[expand_units(w,rules) for w in paths]
        if expanded!=list(words):raise RuntimeError('Recovered passage differs')
    return {'request':asdict(request),'known_expanded_words':list(words),
            'position_unitizations':positions,'rules':rules,'result':result,'expanded_plaintext':expanded,
            'scope':'Exact positional spellings, all optional unit paths. Codebook covers symbols in candidate paths only; no unused full-language alphabet mappings required. Cipher alphabet contains observed grouped units only. No whole-language conclusion.'}


def run(timeout_ms=10000):
    audit=json.loads(Path('experiments/results/passage-survivor-audit/report.json').read_text())
    selection=json.loads(Path('experiments/results/cross-window-passages/selection.json').read_text())
    if digest(selection)!=audit['selection_sha256']:
        # Historical analysis checksum uses default JSON spacing, not corpus digest.
        from benchmarks.historical_word_lengths import checksum
        if checksum(selection)!=audit['selection_sha256']:raise ValueError('Selection changed')
    inventory=json.loads(Path('experiments/configs/latin-contractions.json').read_text())
    from benchmarks.eva_tokenization import grouped_word
    selected=[m for m in audit['matches'] if m['tokenization']=='grouped' and m['audit_status']=='retained']
    if len(selected)!=3:raise ValueError('Expected three retained grouped cases')
    report={'audit_sha256':digest(audit),'timeout_ms':timeout_ms,'experiments':[],
            'semantics':'Known-passage consistency only, free H2/L1–3 grouped-unit prefix-free encoding. All positionwise unitizations retained; no unknown-word substitutions. Short three-case gate, not an inventory sweep or language identification.'}
    for m in selected:
        window=next(w for w in selection['windows'] if w['id']==m['window_id'])
        cipher=Text(tuple(grouped_word(w) for w in window['atomic_words']))
        rules=[r for r in inventory['rules'] if r['id'] in inventory['profiles'][m['profile']]]
        row=solve_case(m['words'],cipher,rules,timeout_ms)
        report['experiments'].append({'source_id':m['source_id'],'window_id':m['window_id'],
            'source_segment_index':m['segment_index'],'source_start_record':m['start_record'],**row})
        write_json(OUT/f'budget-{timeout_ms}ms.json',report)
        print(m['source_id'],m['window_id'],row['result']['status'],f"{row['result']['runtime_seconds']:.2f}s",flush=True)
    report['complete']=True;write_json(OUT/f'budget-{timeout_ms}ms.json',report)
    return report


if __name__=='__main__':run()
