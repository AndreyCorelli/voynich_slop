"""Measure hidden recovery at successive vocabulary/cipher-family bounds."""

import argparse
from collections import Counter
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import platform
import random

import z3

from voynich_smt.cipher.base import generate_ciphertext, generate_encoder
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.experiments.staged import REPRESENTATIONS, StagedConfig
from voynich_smt.models.text import Text


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", nargs="?", type=Path, default=Path("experiments/configs/staged-recovery.json"))
    parser.add_argument("--representation", choices=sorted(REPRESENTATIONS))
    parser.add_argument("--stages", nargs="+", help="Run a subset of named stages")
    parser.add_argument("--output", type=Path, default=Path("experiments/results/staged-recovery.json"))
    parser.add_argument("--artifact-dir", type=Path, default=Path("data/generated/staged-recovery"))
    args = parser.parse_args()
    data = json.loads(args.config.read_text())
    if args.representation:
        data["representation"] = args.representation
    config = StagedConfig.from_dict(data)
    names = {s.name for s in config.stages}
    if args.stages and (set(args.stages) - names or len(set(args.stages)) != len(args.stages)):
        parser.error("--stages must be unique stage names in the configuration")
    stages = [s for s in config.stages if not args.stages or s.name in args.stages]
    report = {"environment": {"python": platform.python_version(), "z3": z3.get_version_string(),
                               "platform": platform.platform(), "machine": platform.machine()},
              "configuration": data, "selected_stages": [s.name for s in stages],
              "configuration_sha256": hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest(),
              "experiments": [], "summary": {}, "complete": False}
    for stage in stages:
        for seed in config.seeds:
            rng = random.Random(seed)
            words = tuple(rng.choice(stage.dictionary.words) for _ in range(max(config.sizes)))
            key = generate_encoder(config.plaintext_alphabet, stage.ciphertext_alphabet, stage.bounds, seed)
            for size in config.sizes:
                truth = Text(words[:size])
                ciphertext, choices = generate_ciphertext(truth, key, seed + 1)
                request = HiddenRecoveryRequest(ciphertext, config.plaintext_alphabet,
                                                stage.ciphertext_alphabet, stage.bounds, stage.dictionary,
                                                config.timeout_ms, representation=config.representation)
                stem = f"{stage.name}-seed{seed}-words{size}"
                public_path = args.artifact_dir / "inputs" / f"{stem}.json"
                write_json(public_path, asdict(request))
                write_json(args.artifact_dir / "ground_truth" / f"{stem}.json",
                           {"plaintext": asdict(truth), "encoder": asdict(key), "choices": choices})
                # Solve exclusively through the persisted public input contract.
                public_bytes = public_path.read_bytes()
                result = HiddenRecoveryRequest.from_dict(json.loads(public_bytes)).solve()
                row = asdict(result)
                row.update(stage=stage.name, seed=seed, word_count=size,
                           vocabulary_size=len(stage.dictionary.words), public_request=str(public_path),
                           public_request_sha256=hashlib.sha256(public_bytes).hexdigest(),
                           exact_plaintext_match=result.plaintext == truth if result.plaintext else None)
                report["experiments"].append(row)
                for selected in stages:
                    runs = [r for r in report["experiments"] if r["stage"] == selected.name]
                    report["summary"][selected.name] = {
                        "outcomes": dict(Counter(r["status"] for r in runs)),
                        "completed_runs": len(runs),
                        "expected_runs": len(config.seeds) * len(config.sizes),
                        "validation_passed": (len(runs) == len(config.seeds) * len(config.sizes)
                                              and all(r["status"] == "SAT" and r["verified"] for r in runs))}
                write_json(args.output, report)
                print(f"{stage.name:17} seed={seed:4} words={size:2} {result.status:7} "
                      f"{result.runtime_seconds:.3f}s pruned={result.capacity['pruned_dictionary_candidates']}", flush=True)
                if result.status == "UNSAT":
                    raise RuntimeError("Planted valid sample was UNSAT; inspect recorded inputs and constraints")
    report["complete"] = True
    write_json(args.output, report)
    print(f"Results: {args.output}")


if __name__ == "__main__":
    main()
