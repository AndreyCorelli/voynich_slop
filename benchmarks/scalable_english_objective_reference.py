"""Evaluation-only feasible reference: covered truth plus untrained OOV proxies.

No inventory expansion or search input is produced. A reference score is not an
upper bound: a model can prefer incorrect dictionaries to the actual plaintext.
"""
from itertools import islice
import json

from voynich_smt.word_mapping.scalable.data import CipherStream
from voynich_smt.word_mapping.scalable.incremental import full_score
from voynich_smt.word_mapping.scalable.inventory import Inventory
from voynich_smt.word_mapping.scalable.state import DictionaryState
from voynich_smt.word_mapping.scalable.trigram import load_model


def reference(resources,public,truth_path):
    stream=CipherStream.load(public)
    truth=json.loads(truth_path.read_text())
    if truth['public_sha256']!=stream.identity or len(truth['decoding'])!=stream.type_count:
        raise ValueError('Reference truth mismatch')
    inventory=Inventory(resources/'inventory.sqlite')
    try:
        model=load_model(resources/'model.sqlite',inventory)
        key=[]; missing=[]
        for cipher,word in enumerate(truth['decoding']):
            try: key.append(inventory.id(word))
            except KeyError:
                key.append(None); missing.append(cipher)
        used=set(key)-{None}
        first=list(islice((w for w in range(model.size) if not model.counts[w] and w not in used),len(missing)))
        last=list(islice((w for w in reversed(range(model.size)) if not model.counts[w] and w not in used),len(missing)))
        if len(first)<len(missing):
            return {'status':'unavailable; insufficient untrained proxy forms'}
        scores=[]
        for proxies in (first,last):
            assignments=list(key)
            for cipher,word in zip(missing,proxies): assignments[cipher]=word
            scores.append(full_score(model,stream,DictionaryState.create(stream,model,assignments)))
        assert abs(scores[0]-scores[1])<1e-8
        return {'status':'scored','model_sha256':model.identity,'cipher_sha256':stream.identity,
                'source_score':scores[0],'missing_types_proxied':len(missing),
                'proxy_alias_check_difference':scores[1]-scores[0],
                'scope':'Feasible evaluation-only key: covered words correct, missing words use distinct untrained forms.',
                'limits':'Not a recovery result or an objective upper bound; never used by inference.'}
    finally:
        inventory.close()
