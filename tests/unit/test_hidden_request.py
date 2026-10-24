from dataclasses import asdict

import pytest

from voynich_smt.cipher.base import Bounds
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.language.dictionary import WordDictionary
from voynich_smt.models.alphabet import Alphabet
from voynich_smt.models.text import Text


def test_serialized_public_request_round_trip_and_hidden_field_rejection():
    request = HiddenRecoveryRequest(Text.from_string("xy"), Alphabet(tuple("ab")),
                                    Alphabet(tuple("xy")), Bounds("monoalphabetic", 1, 1, 1),
                                    WordDictionary.from_strings(("ab",)))
    public = asdict(request)
    loaded = HiddenRecoveryRequest.from_dict(public)
    assert loaded == request
    assert loaded.solve().verified
    for hidden in ("plaintext", "encoder", "choices", "segmentation"):
        with pytest.raises(ValueError):
            HiddenRecoveryRequest.from_dict({**public, hidden: "secret"})
