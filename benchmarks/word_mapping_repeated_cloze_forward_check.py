"""Independent full-vocabulary forward check for each candidate piece length."""
import hashlib
import json
import math
from pathlib import Path
import numpy as np
import torch
from benchmarks import word_mapping_repeated_cloze as b
from voynich_smt.neural_cloze import ClozeCandidateBank,RepeatedCloze
from voynich_smt.neural_scoring import WholeWordScorer
from voynich_smt.data.corpus import digest,write_json


def run():
    public,anchors,selected,_,forms,_=b.prepare()
    manifest=json.loads((b.OUT/'manifest.json').read_text())
    scorer=WholeWordScorer.load(b.DEFAULT_MODEL/'inference',batch_size=16,threads=4)
    bank=ClozeCandidateBank(scorer.tokenizer,forms);cloze=RepeatedCloze(scorer,bank,radius=12)
    cipher=selected[0]
    occurrences=[(s,i) for s in public['segments'] for i,c in enumerate(s) if c==cipher]
    with np.load(b.OUT/'scores'/f'{cipher}.npz') as stored:reference=stored['function_only/pooled'].copy()
    checks=[]
    for length,(indices,pieces) in bank.groups.items():
        index=int(indices[0]);labels=pieces[0]
        values=[]
        for segment,center in occurrences:
            ids,positions=cloze.job(segment,cipher,center,anchors,length)
            inputs=torch.tensor([ids],dtype=torch.long)
            with torch.inference_mode():
                # Use the model's public full-forward logits, rather than the
                # optimized roberta/head-at-target implementation under test.
                logits=scorer.model(input_ids=inputs,attention_mask=torch.ones_like(inputs)).logits[0]
                full=torch.log_softmax(logits,dim=-1)
                values.append(float(full[list(positions),torch.tensor(labels)].mean()))
        expected=math.fsum(values)/len(values)
        difference=abs(expected-reference[index])
        assert difference<1e-4,(forms[index],difference)
        checks.append({'candidate':forms[index],'pieces':length,'occurrences':len(values),
                       'full_forward_score':expected,'optimized_score':float(reference[index]),'absolute_error':difference})
    report={'manifest_sha256':manifest['sha256'],'cipher':cipher,'checks':checks,'tolerance':1e-4,
            'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    write_json(b.OUT/'full-forward-validation.json',report)
    print('Full-forward checks matched for',len(checks),'piece lengths; max error',max(x['absolute_error'] for x in checks))


if __name__=='__main__':run()
