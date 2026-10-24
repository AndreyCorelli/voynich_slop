"""Replay coherent grammar scores and independently validate attachment witnesses."""
from dataclasses import asdict
from pathlib import Path
import hashlib
import json
from collections import Counter

from voynich_smt.data.corpus import digest,write_json
from voynich_smt.coherent_grammar import CoherentGrammar,ClauseResult,CoherentLatinAdapter,validate_clause
from voynich_smt.grammar_diagnostic import MorphAnalysis
from benchmarks.grammar_restoration_iteration2 import OUT,FIXTURES,ITER1


class FrozenAdapter:
    def __init__(self,lattice,manifest):
        self.lattice=lattice;self.config=manifest['model']
    def analyze(self,word):
        return tuple(MorphAnalysis(r['pos'],tuple(map(tuple,r['features']))) for r in self.lattice[word])
    def government(self,word):return tuple(self.config['government'].get(word,()))
    def frame(self,word):return 'intransitive' if word in self.config['intransitive_forms'] else 'optional-object'


def run():
    load=lambda name:json.loads((OUT/name).read_text())
    manifest=load('manifest.json');report=load('report.json');fixtures=json.loads(FIXTURES.read_text())
    assert report['manifest_sha256']==digest(manifest)
    assert hashlib.sha256(FIXTURES.read_bytes()).hexdigest()==manifest['fixtures_sha256']
    for path,expected in manifest['code_sha256'].items():assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==expected
    grammar=CoherentGrammar(FrozenAdapter(load('morphology-lattice.json'),manifest))
    checked=0;witnesses=0
    def verify(saved,tokens,boundaries=None):
        nonlocal checked,witnesses
        result=grammar.score(tokens,supplied_boundaries=boundaries)
        assert (result.status,result.score,list(result.boundaries),result.covered_tokens)==(
            saved['status'],saved['score'],saved['boundaries'],saved['covered_tokens'])
        assert result.components==saved['components']
        if saved['status']=='supported':
            flat=[];ends=[]
            for c in saved['clauses']:
                clause=ClauseResult(c['status'],tuple(c['tokens']),tuple(c['analyses']),c['alternative_found'],c['reason'])
                validate_clause(clause,grammar.adapter);flat.extend(c['tokens']);ends.append(len(flat));witnesses+=1
            assert flat==list(tokens) and ends==saved['boundaries']
            assert saved['covered_tokens']==len(tokens)
            assert saved['score']==-len(saved['clauses'])
        checked+=1
    pairs=load('pairs.json');controls=load('controls.json');streams=load('streams.json')
    for r,fixture in zip(pairs,fixtures['pairs']):
        assert {k:v for k,v in r.items() if k!='results'}==fixture
        for mode in ['supplied','latent']:
            for version in ['reference','corrupted']:
                tokens=r[version].split();verify(r['results'][f'{mode}_{version}'],tokens,[len(tokens)] if mode=='supplied' else None)
    for r,fixture in zip(controls,fixtures['controls']):
        assert {k:v for k,v in r.items() if k!='results'}==fixture
        tokens=r['tokens'].split()
        for mode in ['supplied','latent']:verify(r['results'][mode],tokens,[len(tokens)] if mode=='supplied' else None)
    for r,fixture in zip(streams,fixtures['streams']):
        assert {k:v for k,v in r.items() if k!='results'}==fixture
        for mode in ['supplied','latent']:
            for version in ['reference','corrupted']:
                verify(r['results'][f'{mode}_{version}'],r[version].split(),r['boundaries'] if mode=='supplied' else None)
    for summary in report['summary']:
        split,mode=summary['split'],summary['mode']
        group=[r for r in pairs if r['split']==split];valid=[r for r in controls if r['split']==split];multi=[r for r in streams if r['split']==split]
        assert len(group)==summary['pairs']==8
        assert sum(r['results'][f'{mode}_reference']['status']=='supported' for r in group)==summary['references_supported']
        assert sum(r['results'][f'{mode}_corrupted']['status']=='no_parse' for r in group)==summary['corruptions_no_parse']
        assert sum(r['results'][mode]['status']=='supported' for r in valid)==summary['valid_controls_supported']==len(valid)
        assert sum(r['results'][f'{mode}_reference']['status']=='supported' and r['results'][f'{mode}_corrupted']['status']=='no_parse' for r in multi)==summary['multi_clause_correct']==len(multi)
    gate=all(s['references_supported']==8 and s['corruptions_no_parse']==8 and s['valid_controls_supported']==s['valid_controls'] and s['multi_clause_correct']==s['multi_clause_pairs'] for s in report['summary'])
    assert gate==report['controlled_gate_pass']
    provenance={}
    if gate:
        natural=load('natural-transfer.json');original=json.loads((ITER1/'passages.json').read_text())
        assert len(natural)==len(original)==report['natural_passages']
        for r,old in zip(natural,original):
            assert r['id']==old['id'] and r['tokens']==old['tokens']
            for mode in ['supplied','latent']:
                bounds=sorted(set(old['reference_boundaries_eval_only']+[len(r['tokens'])]))
                verify(r['results'][mode],r['tokens'],bounds if mode=='supplied' else None)
        for mode in ['supplied','latent']:
            assert dict(Counter(r['results'][mode]['status'] for r in natural))==report['natural_statuses'][mode]
        history=load('historical-transfer.json');original_history=json.loads((ITER1/'first-corruptions.json').read_text())
        assert len(history)==len(original_history)==report['historical_moves']
        for r,old in zip(history,original_history):
            assert (r['target'],r['seed'],r['changes'])==(old['target'],old['seed'],old['changes'])
            assert len(r['crops'])==len(old['crops'])
            for crop,old_crop in zip(r['crops'],old['crops']):
                assert (crop['start'],crop['end'])==(old_crop['start'],old_crop['end'])
                for version in ['before','after']:verify(crop['results'][version],old_crop[f'{version}_tokens'])
        provenance={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [ITER1/'passages.json',ITER1/'first-corruptions.json']}
    write_json(OUT/'validation.json',{'validated':True,'score_replays':checked,'clause_witnesses_verified_without_solver':witnesses,
        'controlled_gate_pass':gate,'source_transfer_sha256':provenance,'report_sha256':digest(report),
        'artifact_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.glob('*.json') if p.name!='validation.json'},
        'validator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})
    print(f'Validated {checked} score replays and {witnesses} complete clause witnesses; gate and transfer summaries agree.')


if __name__=='__main__':run()
