"""Reduce glyph evidence while preserving every latent word and its cycle position."""
import argparse
from dataclasses import asdict, replace
import json
from pathlib import Path
from time import perf_counter
from voynich_smt.data.corpus import digest, write_json
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.models.text import Text
from voynich_smt.solver.diagnostics import recover_observations

SEMANTICS='Selected word glyphs; all original word lengths, dictionary constraints and cycle context retained'


def run(source, output, artifacts, budget=10000):
    boundary=json.loads(source.read_text())
    scaling=json.loads(Path(boundary['source_report']).read_text())
    original=HiddenRecoveryRequest.from_dict(json.loads(Path(scaling['experiments'][-1]['public_input']).read_text()))
    size=boundary['prefix']['smallest_proved_unsat']
    request=replace(original,ciphertext=Text(original.ciphertext.words[:size]),timeout_ms=budget)
    report={'schema_version':1,'source_report':str(source),'source_sha256':digest(boundary),
            'boundary_snapshot':boundary['prefix'],'fixed_model':boundary['fixed_model'],
            'semantics':SEMANTICS,'prefix_words':size,'experiments':[],'complete':False}
    retained=list(range(size));unknown=[]
    def solve(mask):
        path=artifacts/f'mask-{len(report["experiments"])}.json'
        payload={'request':asdict(request),'observed_word_indices':mask,'semantics':SEMANTICS}
        write_json(path,payload)
        print(f'Observed words: {mask}',flush=True)
        start=perf_counter();result=recover_observations(request,mask)
        row={'mask_input':str(path),'observed_word_indices':mask,'result':asdict(result),
             'wall_seconds':perf_counter()-start}
        report['experiments'].append(row)
        write_json(output,report)
        print(f'  {result.status} check={result.runtime_seconds:.3f}s',flush=True)
        return result
    initial=solve(retained)
    if initial.status!='UNSAT':
        report['reason']='Baseline mask was not proved UNSAT within the diagnostic budget'
        write_json(output,report);return report
    for index in range(size):
        mask=[i for i in retained if i!=index]
        result=solve(mask)
        if result.status=='UNSAT':retained=mask
        elif result.status=='UNKNOWN':unknown.append(index)
    report.update(complete=True,retained_word_indices=retained,
        retained_words=[''.join(request.ciphertext.words[i]) for i in retained],
        source_record_indices=[scaling['maximum_sample']['record_indices'][i] for i in retained],
        deletion_minimal_proven=not unknown,unresolved_deletions=unknown)
    write_json(output,report)
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,default=Path('experiments/results/unsat-boundary.json'))
    parser.add_argument('--output',type=Path,default=Path('experiments/results/observation-core.json'))
    parser.add_argument('--artifact-dir',type=Path,default=Path('data/generated/observation-core'))
    parser.add_argument('--timeout-ms',type=int,default=10000)
    parser.add_argument('--replay',type=Path)
    args=parser.parse_args()
    if args.replay:
        payload=json.loads(args.replay.read_text())
        result=recover_observations(HiddenRecoveryRequest.from_dict(payload['request']),payload['observed_word_indices'])
        print(json.dumps(asdict(result),indent=2))
    else:run(args.source,args.output,args.artifact_dir,args.timeout_ms)


if __name__=='__main__':main()
