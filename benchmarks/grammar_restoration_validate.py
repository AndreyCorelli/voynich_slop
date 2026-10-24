"""Replay first-iteration structural scores from saved morphology only."""
from dataclasses import asdict
import hashlib
import json
import math
from pathlib import Path
from statistics import mean
from voynich_smt.data.corpus import digest,write_json
from voynich_smt.grammar_diagnostic import LatinAdapter,MorphAnalysis,BoundaryModel,GrammarScorer
from benchmarks.grammar_restoration_iteration1 import OUT,GATE
from benchmarks.word_mapping_first_corruption import PARENT,ORACLE


class FrozenLatinAdapter(LatinAdapter):
    def __init__(self,lattice):self.lattice=lattice
    def analyze(self,word):
        return tuple(MorphAnalysis(a['pos'],tuple(map(tuple,a['features']))) for a in self.lattice[word])


def run():
    load=lambda name:json.loads((OUT/name).read_text())
    manifest=load('manifest.json');report=load('report.json');lattice=load('morphology-lattice.json')
    assert manifest['gate']==GATE and report['manifest_sha256']==digest(manifest)
    for p,h in {**manifest['source_sha256'],**manifest['code_sha256']}.items():
        assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h
    scorer=GrammarScorer(FrozenLatinAdapter(lattice),BoundaryModel(manifest['mean_boundary_length']))
    passages={p['id']:p for p in load('passages.json')}
    def checked(actual,saved):
        assert math.isclose(actual.total,saved['total'],abs_tol=1e-10)
        assert actual.components==saved['components']
        assert list(actual.boundaries)==saved['boundaries']
        assert actual.known_tokens==saved['known_tokens']
    for p in passages.values():
        checked(scorer.score(p['tokens']),p['reference'])
        checked(scorer.score(p['tokens'],latent=False),p['unsegmented_reference'])
    mutations=load('mutations.json')
    assert len(mutations)==144
    for row in mutations:
        tokens=passages[row['passage']]['tokens'];mapping=row['mapping']
        changed=[mapping.get(w,w) for w in tokens]
        assert len(set(mapping.values()))==len(mapping) and not (set(mapping.values())&set(tokens))
        score=scorer.score(changed);checked(score,row['corrupted'])
        assert math.isclose(score.total-row['reference']['total'],row['delta'],abs_tol=1e-10)
        fixed=scorer.score(changed,latent=False)
        assert math.isclose(fixed.total-passages[row['passage']]['unsegmented_reference']['total'],row['unsegmented_delta'],abs_tol=1e-10)
        for a,b in mapping.items():
            old,new=scorer.adapter.analyze(a),scorer.adapter.analyze(b)
            if row['stratum']=='incompatible':assert not ({r.pos for r in old}&{r.pos for r in new})
            if row['stratum']=='compatible':assert set(old)&set(new)
    audit=load('first-corruptions.json');assert len(audit)==10
    original_inputs={}
    forms=json.loads((PARENT/'candidates-oracle.json').read_text())['forms']
    original_inputs[str(PARENT/'candidates-oracle.json')]=hashlib.sha256((PARENT/'candidates-oracle.json').read_bytes()).hexdigest()
    for row in audit:
        tp=PARENT/f"truth/fit-{row['target']}.json"
        cp=PARENT/f"public/fit-{row['target']}.json"
        rp=ORACLE/f"runs/{row['target']}/greedy/seed-{row['seed']}/report.json"
        for p in [tp,cp,rp]:original_inputs[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
        truth,public,saved=[json.loads(p.read_text()) for p in [tp,cp,rp]]
        plain=[w for seg in truth['plaintext'] for w in seg]
        cipher=[w for seg in public['segments'] for w in seg]
        changes=saved['first_departure']['changes']
        assert row['changes']==[{'old':truth['decoding'][c],'new':forms[f]} for c,f in changes.items()]
        for crop in row['crops']:
            lo,hi=crop['start'],crop['end']
            assert crop['before_tokens']==plain[lo:hi]
            assert crop['after_tokens']==[forms[changes[c]] if c in changes else w for c,w in zip(cipher[lo:hi],plain[lo:hi])]
            old,new=[scorer.score(crop[k]) for k in ['before_tokens','after_tokens']]
            checked(old,crop['reference']);checked(new,crop['corrupted'])
            assert math.isclose(new.total-old.total,crop['delta'],abs_tol=1e-10)
        assert math.isclose(sum(c['delta'] for c in row['crops']),row['delta'],abs_tol=1e-10)
    for row in report['summary']:
        selected=[r for r in mutations if r['author']==row['author'] and r['stratum']==row['stratum']]
        assert len(selected)==row['n'] and mean(r['delta']< -1e-9 for r in selected)==row['rate']
    assert report['first_corruptions_preferred']==sum(r['delta']< -1e-9 for r in audit)
    incompatible={r['author']:r for r in report['summary'] if r['stratum']=='incompatible'}
    dev=report['first_corruptions_preferred']>=GATE['first_corruptions'] and incompatible['Cicero']['rate']>=GATE['dev_incompatible_rate']
    confirm=all(incompatible[a]['rate']>=GATE['heldout_incompatible_rate'] and incompatible[a]['passage_cluster_95_interval'][0]>GATE['heldout_cluster_lower_bound'] for a in ['Sallust','Suetonius'])
    assert report['development_pass']==dev and report['confirmation_pass']==confirm
    assert report['gate_pass']==(dev and confirm)
    write_json(OUT/'validation.json',{'validated':True,'passages':18,'mutations':144,'first_corruptions':10,
        'original_audit_inputs_sha256':original_inputs,'report_sha256':digest(report),'artifact_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest()
            for p in OUT.glob('*.json') if p.name!='validation.json'},
        'validator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'checks':['all saved scores replayed without raw annotations or live analyzer','mutation injectivity and stratum checks',
                  'component totals, boundary paths, coverage and score deltas','input/code/report identities','summary rates']})
    print('Validated 18 passages, 144 substitutions and all ten first-corruption context audits.')


if __name__=='__main__':run()
