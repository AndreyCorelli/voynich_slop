"""Run from the repository root: uv run python benchmarks/recovery.py."""

import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import platform
import random

import z3

from voynich_smt.cipher.base import Bounds, generate_ciphertext, generate_encoder
from voynich_smt.models.alphabet import Alphabet
from voynich_smt.models.text import Text
from voynich_smt.solver.recovery import recover


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=1729)
    parser.add_argument("--timeout-ms", type=int, default=10_000)
    parser.add_argument("--output", type=Path, default=Path("experiments/results/milestone1.json"))
    args = parser.parse_args()
    if args.timeout_ms <= 0:
        parser.error("--timeout-ms must be positive")
    # A deliberately tiny hand-authored Latin fixture, not a language model or corpus.
    vocabulary = ("amo", "amor", "ora", "oro", "mora")
    rng = random.Random(args.seed)
    words = tuple(tuple(rng.choice(vocabulary)) for _ in range(50))
    plain = Alphabet(tuple("amor"))
    rows = []
    for family, bounds in [
        ("monoalphabetic", Bounds("monoalphabetic", 1, 1, 1)),
        ("homophonic", Bounds("homophonic", 2, 1, 1)),
        ("verbose", Bounds("verbose", 2, 1, 3)),
    ]:
        ca = Alphabet(tuple("abcdefgh"))
        encoder = generate_encoder(plain, ca, bounds, args.seed)
        for count in (10, 25, 50):
            text = Text(words[:count])
            ciphertext, _ = generate_ciphertext(text, encoder, args.seed + 1)
            result = recover(text, ciphertext, plain, ca, bounds, args.timeout_ms)
            row = asdict(result)
            row.update(family=family, word_count=count, plaintext_tokens=text.size,
                       ciphertext_tokens=ciphertext.size, bounds=asdict(bounds),
                       seed=args.seed, timeout_ms=args.timeout_ms,
                       sample={"source": "hand-authored Latin fixture v1", "vocabulary": vocabulary,
                               "plaintext": text.words, "ciphertext": ciphertext.words,
                               "ciphertext_sha256": hashlib.sha256(json.dumps(ciphertext.words).encode()).hexdigest()},
                       assumptions={"known_plaintext": True, "prefix_free": True,
                                    "preserve_word_boundaries": True,
                                    "plaintext_alphabet": plain.symbols, "ciphertext_alphabet": ca.symbols})
            rows.append(row)
            print(f"{family:15} {count:2} words {result.status:7} "
                  f"{result.runtime_seconds:.3f}s verified={result.verified}", flush=True)
    report = {"environment": {"python": platform.python_version(), "z3": z3.get_version_string(),
                               "platform": platform.platform(), "machine": platform.machine()},
              "experiments": rows}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(f"Results: {args.output}")


if __name__ == "__main__":
    main()
