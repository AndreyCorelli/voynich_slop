"""Evaluation-only cost of correcting frequent-word assignments in saved keys.

These are oracle diagnostic moves, never proposals supplied to inference. A swap
can displace another row, so its sign is not a pure word-level language judgment.
"""
import json
from collections import Counter
from pathlib import Path

from voynich_smt.word_mapping.scalable.data import CipherStream
from voynich_smt.word_mapping.scalable.inventory import Inventory
from voynich_smt.word_mapping.scalable.trigram import load_model
from voynich_smt.word_mapping.scalable.state import DictionaryState
from voynich_smt.word_mapping.scalable.incremental import DictionaryScorer, EventIndex, full_score
from benchmarks.scalable_latin_caesar import ROOT as ORIGINAL, write


def audit(resources,root,truth_path):
    stream=CipherStream.load(root/'public/cipher.json')
    truth=json.loads(truth_path.read_text()); inference=json.loads((root/'inference.json').read_text())
    assert truth['public_sha256']==stream.identity==inference['protocol']['cipher_sha256']
    counts=Counter(c for doc in stream.documents for c in doc)
    inventory=Inventory(resources/'inventory.sqlite')
    try:
        model=load_model(resources/'model.sqlite',inventory)
        assert model.identity==inference['protocol']['model_sha256']
        index=EventIndex.build(stream)
        results={}
        for run in inference['runs']:
            state=DictionaryState.create(stream,model,run['joint_archive'][0]['assignments'])
            scorer=DictionaryScorer(model,stream,state,event_index=index)
            rows=[]
            for c in sorted(counts,key=lambda c:(-counts[c],c)):
                if counts[c]<100: continue
                try: word=inventory.id(truth['decoding'][c])
                except KeyError:
                    rows.append({'cipher':c,'count':counts[c],'original':truth['decoding'][c],'available':False}); continue
                move=scorer.assign_or_swap(c,word)
                key=list(state.assignments)
                for cipher,target in move.changes: key[cipher]=target
                delta=full_score(model,stream,DictionaryState.create(stream,model,key))-scorer.score
                assert abs(delta-move.log_delta)<1e-7
                rows.append({'cipher':c,'count':counts[c],'original':truth['decoding'][c],
                             'decoded':inventory.word(state.assignments[c]),'available':True,
                             'already_correct':state.assignments[c]==word,'corrective_delta':delta,
                             'changed_rows':len(move.changes)})
            wrong=[r for r in rows if r['available'] and not r['already_correct']]
            results[str(run['seed'])]={'frequent_rows':rows,'wrong_available_types':len(wrong),
                'score_improving_corrections':sum(r['corrective_delta']>1e-7 for r in wrong),
                'score_worsening_corrections':sum(r['corrective_delta'] < -1e-7 for r in wrong),
                'score_neutral_corrections':sum(abs(r['corrective_delta'])<=1e-7 for r in wrong)}
        result={'scope':'Oracle evaluation only; no moves applied or passed to inference.',
                'limits':'Each correction uses a feasible replacement or swap in the saved key; sign can include other-row displacement. Local move signs do not establish the best full dictionary.',
                'runs':results,'independent_full_score_checks':True}
        write(root/'corrective-audit.json',result)
        return result
    finally:inventory.close()


if __name__=='__main__':
    for mode in ('random','frequency'):
        result=audit(ORIGINAL/'resources',ORIGINAL/mode,ORIGINAL/'fixture/evaluation-only/truth.json')
        print(mode,json.dumps({s:{k:v for k,v in r.items() if k!='frequent_rows'} for s,r in result['runs'].items()}))
