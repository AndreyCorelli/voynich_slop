"""Matched grammar predictor for POS, case and number rather than full states."""
import argparse
import hashlib
import json
from pathlib import Path
from benchmarks import word_mapping_grammar_inference as b
from voynich_smt.structural_oracle import StructuralOracle
from voynich_smt.data.corpus import write_json

OUT=Path('experiments/results/word-mapping/grammar-inference-coarse-calibration')
class CoarseOracle(StructuralOracle):
    def __init__(self,entries,decoding):
        super().__init__(entries,decoding)
        self.profiles={w:frozenset((pos,None,tuple((k,v) for k,v in features if k in ('Case','Number'))) for pos,enclitic,features in profile) for w,profile in self.profiles.items()}

def run(steps,validate):
    supplemental={'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'projection':['POS','Case','Number'],'steps':steps,
        'scope':'coarse plausible dictionary analysis; supplementary compatibility uses projected profiles, not the strict full-profile oracle'}
    path=OUT/'projection-manifest.json'
    if validate:assert json.loads(path.read_text())==supplemental
    else:
        if path.exists():raise ValueError('Existing experiment')
        write_json(path,supplemental)
    b.OUT=OUT;b.StructuralOracle=CoarseOracle;b.run(steps,validate)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--steps',type=int,default=1000);p.add_argument('--validate',action='store_true');a=p.parse_args();run(a.steps,a.validate)
