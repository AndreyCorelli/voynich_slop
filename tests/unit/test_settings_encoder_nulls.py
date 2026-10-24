from dataclasses import asdict
import json
from pathlib import Path

import pytest

from voynich_smt.cipher.base import Encoder, NullInsertion
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.experiments.synthetic import generate
from voynich_smt.models.settings import NullBounds, Optimization, ComplexityWeights
from voynich_smt.models.text import Text


@pytest.mark.parametrize("kwargs", [
    {"enabled": 1}, {"max_occurrences": -1}, {"max_distinct_symbols": True},
    {"max_consecutive": 1.5}, {"enabled": False, "max_occurrences": 1},
])
def test_invalid_null_settings(kwargs):
    with pytest.raises(ValueError):
        NullBounds(**kwargs)


@pytest.mark.parametrize("kwargs", [{"mappings": -1}, {"null_occurrences": 0.5}, {"extra_code_glyphs": True}])
def test_invalid_weights(kwargs):
    with pytest.raises(ValueError):
        ComplexityWeights(**kwargs)


def test_invalid_optimization():
    with pytest.raises(ValueError):
        Optimization(method="arbitrary")


def test_encoder_rejects_ambiguous_null_ownership_and_bad_positions():
    with pytest.raises(ValueError):
        Encoder({"a": (("x",),)}, ("x",))
    encoder = Encoder({"a": (("x", "y"),)}, ("n",))
    plaintext = Text.from_string("a")
    for insertion in (NullInsertion(0, 1, "n"), NullInsertion(0, 9, "n"),
                      NullInsertion(1, 0, "n"), NullInsertion(0, 0, "z")):
        with pytest.raises(ValueError):
            encoder.encode(plaintext, (0,), (insertion,))
    with pytest.raises(ValueError):
        encoder.encode(plaintext, (0,), (NullInsertion(0, 0, "n"), NullInsertion(0, 0, "n")))
    assert encoder.encode(plaintext, (0,), (NullInsertion(0, 0, "n"), NullInsertion(0, 3, "n"))) == Text.from_string("nxyn")


def test_seeded_generator_round_trip_and_public_contract():
    config = Path(__file__).parents[2] / "experiments/configs/nulls-demo.json"
    request = HiddenRecoveryRequest.from_dict(json.loads(config.read_text()))
    first = generate(request, 5, 7)
    assert first == generate(request, 5, 7)
    public, truth = first
    assert "plaintext" not in asdict(public)
    assert len(truth["nulls"]) == public.nulls.max_occurrences
    encoder = Encoder({s: tuple(tuple(code) for code in codes) for s, codes in truth["encoder"]["codebook"].items()},
                      tuple(truth["encoder"]["null_symbols"]))
    plaintext = Text(tuple(tuple(w) for w in truth["plaintext"]["words"]))
    insertions = tuple(NullInsertion(**n) for n in truth["nulls"])
    assert encoder.encode(plaintext, truth["choices"], insertions) == public.ciphertext
    assert encoder.decode(public.ciphertext) == plaintext
    reloaded = HiddenRecoveryRequest.from_dict(json.loads(json.dumps(asdict(public))))
    assert reloaded == public and reloaded.solve().verified


def test_nested_settings_reject_unknown_keys():
    config = Path(__file__).parents[2] / "experiments/configs/nulls-demo.json"
    data = json.loads(config.read_text())
    data["nulls"]["hidden_positions"] = [1]
    with pytest.raises(ValueError):
        HiddenRecoveryRequest.from_dict(data)


@pytest.mark.parametrize("field,value", [
    ("optimization", []), ("ciphertext", {"words": ["implicit characters"]}),
    ("ciphertext_alphabet", {"symbols": [True]}), ("dictionary", {"words": [123]}),
])
def test_malformed_public_requests_are_rejected(field, value):
    config = Path(__file__).parents[2] / "experiments/configs/nulls-demo.json"
    data = json.loads(config.read_text())
    data[field] = value
    with pytest.raises(ValueError):
        HiddenRecoveryRequest.from_dict(data)
