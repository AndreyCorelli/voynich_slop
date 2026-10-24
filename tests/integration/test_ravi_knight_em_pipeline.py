"""A small end-to-end diagnostic with independent evidence recomputation."""
import math
from itertools import product

import pytest

from benchmarks.ravi_knight_em import run
from voynich_smt.word_mapping.ravi_knight.reference import BigramHMM, viterbi


def test_generated_pipeline_outputs_are_recomputable():
    result = run(max_iterations=2)
    public = result['public_input']
    source = public['source']
    for fitted in result['runs']:
        model = BigramHMM(source['initial'], source['transition'], source['final'], fitted['channel'])
        assert len(fitted['log_likelihoods']) == 3
        assert all(b >= a - 1e-8 for a, b in zip(fitted['log_likelihoods'], fitted['log_likelihoods'][1:]))
        assert fitted['decoded'] == tuple(viterbi(model, s, channel_exponent=3)[0] for s in public['cipher'])
        # Enumerate one short segment independently of forward-backward.
        obs = public['cipher'][0]
        probability = 0.
        for path in product(range(len(model.initial)), repeat=len(obs)):
            p = model.initial[path[0]] * model.final[path[-1]]
            for s, c in zip(path, obs):
                p *= model.channel[s][c]
            for a, b in zip(path, path[1:]):
                p *= model.transition[a][b]
            probability += p
        from voynich_smt.word_mapping.ravi_knight.em import expectation
        actual, _ = expectation(model, [obs])
        assert actual == pytest.approx(math.log(probability))
    assert 'plaintext' not in public and 'encryption' not in public
