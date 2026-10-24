"""Hidden-plaintext validation and full-alphabet known-plaintext scaling."""

import argparse
from collections import Counter
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import platform
import random

import z3

from voynich_smt.cipher.base import Bounds, generate_ciphertext, generate_encoder
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.language.dictionary import WordDictionary
from voynich_smt.models.alphabet import Alphabet
from voynich_smt.models.text import Text
from voynich_smt.solver.recovery import recover
from voynich_smt.experiments.fixtures import SMALL, LATIN


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, nargs="+", default=[7, 17, 1729])
    parser.add_argument("--sizes", type=int, nargs="+", default=[10, 25, 50])
    parser.add_argument("--timeout-ms", type=int, default=10_000)
    parser.add_argument("--representation", choices=["ite", "array", "interval", "chunk", "finite"], default="finite")
    parser.add_argument("--profiles", nargs="+", choices=["small-hidden", "latin-known", "latin-hidden"],
                        default=["small-hidden", "latin-known", "latin-hidden"])
    parser.add_argument("--output", type=Path, default=Path("experiments/results/hidden-recovery.json"))
    parser.add_argument("--artifact-dir", type=Path, default=Path("data/generated/hidden-recovery"))
    parser.add_argument("--request", type=Path, help="Replay one public request without loading ground truth")
    args = parser.parse_args()
    if args.timeout_ms <= 0 or any(s <= 0 for s in args.sizes):
        parser.error("Timeout and sample sizes must be positive")
    if args.request:
        request = HiddenRecoveryRequest.from_dict(json.loads(args.request.read_text()))
        write_json(args.output, asdict(request.solve()))
        print(f"Replay result: {args.output}")
        return
    environment = {"python": platform.python_version(), "z3": z3.get_version_string(),
                   "platform": platform.platform(), "machine": platform.machine()}
    report = {"environment": environment, "experiments": [], "summary": {}}
    bounds = Bounds("verbose", 2, 1, 3)
    ca = Alphabet(tuple("abcdefgh"))
    for profile in args.profiles:
        vocabulary = WordDictionary.from_strings(SMALL if profile == "small-hidden" else LATIN)
        pa = Alphabet(tuple("amor" if profile == "small-hidden" else "abcdefghiklmnopqrstuvxyz"))
        for seed in args.seeds:
            rng = random.Random(seed)
            words = tuple(rng.choice(vocabulary.words) for _ in range(max(args.sizes)))
            key = generate_encoder(pa, ca, bounds, seed)
            for count in args.sizes:
                truth = Text(words[:count])
                ciphertext, original_choices = generate_ciphertext(truth, key, seed + 1)
                stem = f"{profile}-seed{seed}-words{count}"
                public_path = args.artifact_dir / "inputs" / f"{stem}.json"
                private_path = args.artifact_dir / "ground_truth" / f"{stem}.json"
                request = HiddenRecoveryRequest(ciphertext, pa, ca, bounds, vocabulary, args.timeout_ms,
                                                representation=args.representation)
                # Persist and reload the public request, enforcing the truth-free boundary.
                if profile != "latin-known":
                    write_json(public_path, asdict(request))
                    request = HiddenRecoveryRequest.from_dict(json.loads(public_path.read_text()))
                write_json(private_path, {"plaintext": asdict(truth), "encoder": asdict(key),
                                          "choices": original_choices})
                result = (recover(truth, ciphertext, pa, ca, bounds, args.timeout_ms,
                                  representation=args.representation)
                          if profile == "latin-known" else request.solve())
                row = asdict(result)
                row.update(profile=profile, seed=seed, word_count=count,
                           timeout_ms=args.timeout_ms, bounds=asdict(bounds),
                           ciphertext_tokens=ciphertext.size,
                           exact_plaintext_match=(result.plaintext == truth if result.plaintext is not None else None),
                           sample={"source": "hand-authored vocabulary v1", "dictionary": vocabulary.words,
                                   "ciphertext": ciphertext.words,
                                   "ciphertext_sha256": hashlib.sha256(json.dumps(ciphertext.words).encode()).hexdigest()},
                           assumptions={"known_plaintext": profile == "latin-known", "prefix_free": True,
                                        "preserve_word_boundaries": True, "plaintext_alphabet": pa.symbols,
                                        "ciphertext_alphabet": ca.symbols,
                                        "min_word_length": 1,
                                        "max_word_length": max(map(len, vocabulary.words)),
                                        "language_model": "finite dictionary; no grammar or frequencies"},
                           public_request=str(public_path) if profile != "latin-known" else None)
                report["experiments"].append(row)
                report["summary"] = {p: dict(Counter(r["status"] for r in report["experiments"]
                                                       if r["profile"] == p)) for p in args.profiles}
                # Checkpoint every experiment so timeouts or interruptions retain evidence.
                write_json(args.output, report)
                print(f"{profile:13} seed={seed:4} words={count:2} {result.status:7} "
                      f"{result.runtime_seconds:.3f}s verified={result.verified}", flush=True)
    print(f"Summary: {report['summary']}")
    print(f"Results: {args.output}")


if __name__ == "__main__":
    main()
