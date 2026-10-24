import copy
import json
from pathlib import Path

import pytest

from voynich_smt.experiments.staged import StagedConfig


def specification():
    return json.loads((Path(__file__).parents[2] / "experiments/configs/staged-recovery.json").read_text())


def test_checked_in_staged_config():
    config = StagedConfig.from_dict(specification())
    assert len(config.plaintext_alphabet.symbols) == 24
    assert len(config.stages) == 6
    assert config.sizes == (5, 10, 25)


@pytest.mark.parametrize("field,value", [
    ("seeds", []), ("seeds", [7, 7]), ("seeds", [True]), ("sizes", [0]),
    ("sizes", []), ("timeout_ms", False), ("timeout_ms", -1),
    ("representation", "invalid"), ("stages", []),
    ("representation", []), ("plaintext_alphabet", "abc"), ("plaintext_alphabet", [True]),
])
def test_invalid_root_settings(field, value):
    data = specification()
    data[field] = value
    with pytest.raises(ValueError):
        StagedConfig.from_dict(data)


@pytest.mark.parametrize("field,value", [
    ("name", "../escape"), ("vocabulary_size", 36), ("vocabulary_size", 0),
    ("ciphertext_alphabet", ["x"]),
    ("ciphertext_alphabet", [False]),
    ("bounds", {"family": "verbose", "max_homophones": False, "min_code_length": 1, "max_code_length": 3}),
])
def test_invalid_stage_settings(field, value):
    data = specification()
    data["stages"][0][field] = value
    with pytest.raises(ValueError):
        StagedConfig.from_dict(data)


def test_duplicate_stage_and_unknown_field():
    data = specification()
    data["stages"].append(copy.deepcopy(data["stages"][0]))
    with pytest.raises(ValueError):
        StagedConfig.from_dict(data)
    data = specification()
    data["unknown"] = 123
    with pytest.raises(ValueError):
        StagedConfig.from_dict(data)
