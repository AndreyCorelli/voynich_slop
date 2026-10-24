"""Independently verify correct-assignment displacements by complete stream scoring."""
import argparse
from collections import Counter
import gzip
import json
from pathlib import Path

from voynich_smt.word_mapping.scalable.data import CipherStream
from voynich_smt.word_mapping.scalable.inventory import Inventory
from voynich_smt.word_mapping.scalable.trigram import load_model


def validate(resources, root, truth_path, traces, analysis):
    report=json.loads((analysis/'diagnostics.json').read_text())
    inference=json.loads((root/'inference.json').read_text())
    stream=CipherStream.load(root/'public/cipher.json')
    truth=json.loads(truth_path.read_text())
    assert truth['public_sha256']==report['cipher_sha256']==stream.identity
    inventory=Inventory(resources/'inventory.sqlite')
    try:
        model=load_model(resources/'model.sqlite',inventory)
        assert model.identity==report['model_sha256']
        true=[]
        for word in truth['decoding']:
            try:
                true.append(inventory.id(word))
            except KeyError:
                true.append(None)  # Unavailable forms remain unrecoverable, never injected.

        counts=Counter(c for d in stream.documents for c in d)
        def score(key):
            return sum(model.score(key[c] for c in d) for d in stream.documents)
        verified=[]
        for run in inference['runs']:
            expected=report['attribution'][str(run['seed'])]
            assert sum(expected['categories'].values())==stream.type_count
            assert len(expected['rows'])==stream.type_count
            key=None; events=[]
            with gzip.open(traces/f'seed-{run["seed"]}.jsonl.gz','rt',encoding='utf-8') as handle:
                for line in handle:
                    event=json.loads(line)
                    if event['kind']=='initial':key=event['assignments']
                    elif event['kind']=='move' and event['accepted']:
                        losses=[c for c,w in event['changes'] if key[c]==true[c] and w!=true[c]]
                        gains=[c for c,w in event['changes'] if key[c]!=true[c] and w==true[c]]
                        before=score(key) if losses else None
                        for c,w in event['changes']:key[c]=w
                        if losses:
                            actual=score(key)-before
                            assert abs(actual-event['delta'])<1e-7
                            events.extend((event['step'],c) for c in losses)
                            verified.append({'seed':run['seed'],'step':event['step'],
                                'displaced_words':[truth['decoding'][c] for c in losses],
                                'full_score_delta':actual,
                                'lost_correct_token_positions':sum(counts[c] for c in losses),
                                'gained_correct_token_positions':sum(counts[c] for c in gains),
                                'net_correct_token_change':sum(counts[c] for c in gains)-sum(counts[c] for c in losses)})
            assert events==[(e['step'],e['cipher']) for e in expected['displacement_events']]
            assert key==expected['final_trajectory_key']
            assert abs(score(key)-run['current_score'])<1e-7
        result={'status':'validated','independent_full_score_displacements':verified}
        (analysis/'validation.json').write_text(json.dumps(result,indent=2)+'\n')
        return result
    finally:inventory.close()


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--resources',type=Path,default=Path('experiments/results/scalable-english/foundations-ewt-v1'))
    parser.add_argument('--run',type=Path,default=Path('experiments/results/scalable-english/search-ewt-v1'))
    parser.add_argument('--truth',type=Path,default=Path('experiments/results/scalable-english/retrieval-ewt-v2/evaluation-only/truth.json'))
    parser.add_argument('--traces',type=Path,default=Path('experiments/results/scalable-english/search-ewt-diagnostics-v1/traces'))
    parser.add_argument('--analysis',type=Path,default=Path('experiments/results/scalable-english/search-ewt-diagnostics-v1/analysis-v2'))
    args=parser.parse_args()
    print(json.dumps(validate(args.resources,args.run,args.truth,args.traces,args.analysis),indent=2))
