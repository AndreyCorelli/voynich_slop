"""Check the 25%-context difference against broken IDs and new permutations."""
import hashlib
import json
from pathlib import Path
import numpy as np
from safetensors.torch import load_file
from benchmarks import word_mapping_repeat_identity as b
from benchmarks.word_mapping_repeat_identity_enriched import OUT
from voynich_smt.data.corpus import digest,write_json

def run():
    public,anchors,targets,entries,forms,_=b.old.base.prepare()
    truth=json.loads((b.old.base.anchor.PARENT/'truth/fit-2000.json').read_text())
    report=json.loads((OUT/'report.json').read_text());training=json.loads((OUT/'repeat/training.json').read_text())
    assert b.old.file_hashes(OUT/'repeat/model')==training['model_sha256']
    protocol={'parent_report_sha256':digest(report),'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'fraction':.25,'conditions':[('broken',941),('repeat',942),('repeat',943)],'targets':targets}
    destination=OUT/'ablation';write_json(destination/'manifest.json',{'protocol':protocol,'sha256':digest(protocol)})
    summary=[]
    for mode,seed in protocol['conditions']:
        scorer,adapter,cloze=b.setup(mode,seed=seed,path=OUT/'repeat/model')
        adapter.load_state_dict(load_file(str(OUT/'repeat/adapter.safetensors')));adapter.eval()
        rows=[]
        for number,target in enumerate(targets,1):
            visible=b.old.scaffold(truth['decoding'],anchors,target,.25)
            result=cloze.rank_scores(public['segments'],target,visible)['pooled']
            reserved=set(visible.values());excluded=set(cloze.bank.excluded)
            eligible=[i for i,w in enumerate(forms) if i not in excluded and w not in reserved]
            row=b.old.base.evaluate_case({'cipher':target,'model':mode,'seed':seed,'fraction':.25},{'neural':result},forms,eligible,entries,truth)
            write_json(destination/'cases'/f'{mode}-{seed}-{target}.json',row)
            (destination/'scores').mkdir(parents=True,exist_ok=True);np.savez_compressed(destination/'scores'/f'{mode}-{seed}-{target}.npz',pooled=result)
            rows.append(row)
            print(mode,seed,number,'/',len(targets),flush=True)
        selected=[r for r in rows if r['gold_kind']=='content' and r['gold'] not in b.old.GLUE]
        summary.append({'mode':mode,'seed':seed,'types':len(selected),**{key:sum(r['rankings']['neural']['content_candidates'][key] for r in selected) for key in ('compatible_top1','compatible_top10','exact_top1','exact_top10')},'cases_sha256':digest(rows)})
        del scorer,adapter,cloze
    write_json(destination/'report.json',{'protocol_sha256':digest(protocol),'lexical_summary':summary})
    print(json.dumps(summary,indent=2),flush=True)
if __name__=='__main__':run()
