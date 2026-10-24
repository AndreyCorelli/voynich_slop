"""Matched-clean attribution for diagnostics, never a repair selector."""
import math


def endpoint(clean_probability, corrupt_probability, clean_tag, proposed_tag):
    def margin(p, tag):
        return math.log((p + 1e-12) / (1 - p + 1e-12)) * (1 if tag == 'ADP' else -1)
    clean = margin(clean_probability, clean_tag)
    changed = clean_tag != proposed_tag
    counterfactual = -clean if changed else clean
    observed = margin(corrupt_probability, proposed_tag)
    return dict(class_changed=changed, clean_flip_margin=clean,
                clean_context_proposed_margin=counterfactual,
                corrupt_flip_margin=observed, context_delta=observed-counterfactual,
                preexisting_false_flip=not changed and clean > 1e-12,
                observed_false_flip=not changed and observed > 1e-12,
                context_invariant=abs(observed-counterfactual) <= 1e-10)
