"""Preserve frozen v1 results; convert oracle length lists to required offsets."""
from copy import deepcopy
from itertools import accumulate
from pathlib import Path

from benchmarks import contraction_hidden_calibration as base
from voynich_smt.data.corpus import digest, write_json

ORIGINAL_FIT = base.fit


def oracle_case(case):
    corrected = deepcopy(case)
    corrected['oracle_segmentation'] = [list(accumulate(row, initial=0))
                                       for row in case['oracle_segmentation']]
    return corrected


def fit(p, stage, name, case, control=False, oracle=False):
    if not oracle:
        return ORIGINAL_FIT(p, stage, name, case, control, oracle)
    corrected = oracle_case(case)
    row = ORIGINAL_FIT(p, stage, name+'-offsets', corrected, control, oracle)
    row['oracle_adapter'] = {'original_case_sha256': digest(case),
        'rule': 'Cumulative offsets starting at zero from frozen generating code lengths'}
    return row


def run():
    p = base.prepare()
    adapter = {'prepared_sha256': digest(p), 'code_sha256': digest(Path(__file__).read_text()),
        'reason': 'Oracle API expects offsets, original fixture stores lengths. No model/budget/selection changes; rejected pre-solver input preserved. Only iteration5 receives corrected offsets; never used as hidden evidence.'}
    path = base.OUT/'oracle-adapter.json'
    if path.exists():
        import json
        assert __import__('json').loads(path.read_text()) == adapter
    else:
        write_json(path, adapter)
    base.fit = fit
    try:
        return base.run()
    finally:
        base.fit = ORIGINAL_FIT


if __name__ == '__main__':
    run()
