"""Compare feasibility, lexicographic and weighted recovery on identical null samples."""

import argparse
from dataclasses import asdict, replace
import hashlib
import json
from pathlib import Path
import platform

import z3

from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.experiments.synthetic import generate
from voynich_smt.models.settings import Optimization


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("experiments/configs/nulls-demo.json"))
    parser.add_argument("--seeds", type=int, nargs="+", default=[7, 17, 1729])
    parser.add_argument("--sizes", type=int, nargs="+", default=[5, 10, 25])
    parser.add_argument("--output", type=Path, default=Path("experiments/results/nulls-optimization.json"))
    parser.add_argument("--artifact-dir", type=Path, default=Path("data/generated/nulls-optimization"))
    args = parser.parse_args()
    if not args.seeds or any(s <= 0 for s in args.sizes):
        parser.error("Seeds must be nonempty and sizes must be positive")
    template = HiddenRecoveryRequest.from_dict(json.loads(args.config.read_text()))
    report = {"environment": {"python": platform.python_version(), "z3": z3.get_version_string(),
                               "platform": platform.platform(), "machine": platform.machine()},
              "experiments": [], "complete": False}
    for seed in args.seeds:
        for size in args.sizes:
            request, truth = generate(template, size, seed)
            stem = f"seed{seed}-words{size}"
            write_json(args.artifact_dir / "ground_truth" / f"{stem}.json", truth)
            for mode in ("feasibility", "lexicographic", "weighted"):
                public = replace(request, optimization=Optimization(mode != "feasibility",
                                                                     "lexicographic" if mode == "feasibility" else mode,
                                                                     template.optimization.weights))
                path = args.artifact_dir / "inputs" / f"{stem}-{mode}.json"
                write_json(path, asdict(public))
                public = HiddenRecoveryRequest.from_dict(json.loads(path.read_text()))
                result = public.solve()
                row = asdict(result)
                row.update(mode=mode, seed=seed, word_count=size, request=asdict(public),
                           public_request=str(path), actual_generated_nulls=len(truth["nulls"]),
                           ciphertext_sha256=hashlib.sha256(json.dumps(asdict(public.ciphertext)).encode()).hexdigest())
                report["experiments"].append(row)
                write_json(args.output, report)
                print(f"{mode:13} seed={seed:4} words={size:2} {result.status:7} "
                      f"{result.runtime_seconds:.3f}s optimal={result.optimization.get('optimality_proven', False)}", flush=True)
                if result.status == "UNSAT":
                    raise RuntimeError("Valid generated null example returned UNSAT")
    report["complete"] = True
    write_json(args.output, report)
    print(f"Results: {args.output}")


if __name__ == "__main__":
    main()
