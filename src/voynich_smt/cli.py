"""Command-line generation, solving, sweeps, comparison, and dataset inspection."""

import argparse
from dataclasses import asdict, replace
import hashlib
import json
from pathlib import Path
import platform

import z3

from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.experiments.synthetic import generate
from voynich_smt.models.settings import NullBounds


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n")


def load_request(path):
    return HiddenRecoveryRequest.from_dict(json.loads(path.read_text()))


def solve_document(request, input_data):
    result = request.solve()
    document = {
        "schema_version": 1,
        "request": asdict(request),
        "request_sha256": hashlib.sha256(json.dumps(asdict(request), sort_keys=True).encode()).hexdigest(),
        "input_sha256": hashlib.sha256(input_data).hexdigest(),
        "environment": {"python": platform.python_version(), "z3": z3.get_version_string(),
                        "platform": platform.platform(), "machine": platform.machine()},
        "result": asdict(result),
    }
    return document


def print_result(document):
    result = document["result"]
    message = f"{result['status']} in {result['runtime_seconds']:.3f}s"
    if result["status"] == "SAT":
        message += f"; verified={result['verified']}; score={result['complexity']['weighted_score']}"
        if result["optimization"].get("enabled"):
            message += f"; optimality_proven={result['optimization']['optimality_proven']}"
    elif result["status"] == "UNKNOWN":
        message += f"; reason={result['reason_unknown']}"
    print(message)


def comparison_rows(document, context=(), gate=None):
    """Read both flat benchmark reports and nested frontier stage/policy reports."""
    label = document.get("name") or document.get("dataset")
    if "experiments" in document and "selection" in document:
        policy = document["selection"]
        label = f"{policy['mode']}-{policy['reset']}"
    if label:
        context = context + (label,)
    gate = document.get("synthetic_gate_passed", gate)
    result = document.get("result", document)
    if "status" in result:
        yield document, result, "/".join(context) or "-", gate
    else:
        for key in ("stages", "policies", "experiments"):
            for child in document.get(key, ()):
                yield from comparison_rows(child, context, gate)


def main(argv=None):
    parser = argparse.ArgumentParser(prog="voynich-smt", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    synthetic = commands.add_parser("synthetic", help="Generate seeded synthetic experiments")
    actions = synthetic.add_subparsers(dest="action", required=True)
    generation = actions.add_parser("generate")
    generation.add_argument("--config", type=Path, required=True)
    generation.add_argument("--words", type=int, default=10)
    generation.add_argument("--seed", type=int, default=1729)
    generation.add_argument("--output", type=Path, required=True, help="Public solver input")
    generation.add_argument("--ground-truth", type=Path, required=True, help="Separate private generation record")
    solve = commands.add_parser("solve", help="Solve or replay a public JSON request")
    solve.add_argument("config", type=Path)
    solve.add_argument("--output", type=Path, required=True)
    solve.add_argument("--timeout-ms", type=int)
    solve.add_argument("--optimize", choices=["lexicographic", "weighted"])
    sweep = commands.add_parser("sweep", help="Sweep the maximum distinct null-symbol budget")
    sweep.add_argument("config", type=Path)
    sweep.add_argument("--null-symbols", nargs="+", type=int, required=True)
    sweep.add_argument("--output", type=Path, required=True)
    compare = commands.add_parser("compare", help="Compare saved result summaries")
    compare.add_argument("paths", nargs="+", type=Path)
    corpus = commands.add_parser("corpus", help="Inspect tokenized data in a request")
    corpus_commands = corpus.add_subparsers(dest="action", required=True)
    info = corpus_commands.add_parser("info")
    info.add_argument("config", type=Path)
    fetch = corpus_commands.add_parser("fetch", help="Acquire an immutable catalogued raw source")
    fetch.add_argument("source", choices=["zl-eva", "caesar-latin"])
    fetch.add_argument("--raw-dir", type=Path, default=Path("data/raw"))
    fetch.add_argument("--local", type=Path, help="Import previously downloaded original bytes")
    normalization = corpus_commands.add_parser("normalize")
    normalization.add_argument("manifest", type=Path)
    normalization.add_argument("--output", type=Path, required=True)
    normalization.add_argument("--uncertain-spaces", choices=["split", "join", "exclude-line"], default="split")
    normalization.add_argument("--annotated-words", choices=["exclude", "preserve"], default="exclude")
    normalization.add_argument("--uv", choices=["preserve", "v_to_u", "u_to_v"], default="preserve")
    normalization.add_argument("--keep-j", action="store_true")
    normalization.add_argument("--alphabet", default="abcdefghiklmnopqrstuvxyz")
    normalization.add_argument("--remove-spaces", action="store_true")
    sampling = corpus_commands.add_parser("sample")
    sampling.add_argument("config", type=Path)
    sampling.add_argument("--words", type=int, default=5)
    sampling.add_argument("--offset", type=int, default=0)
    sampling.add_argument("--seed", type=int)
    sampling.add_argument("--folio")
    sampling.add_argument("--section")
    sampling.add_argument("--line")
    sampling.add_argument("--max-tokens", type=int)
    sampling.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "corpus":
            from voynich_smt.data.acquisition import acquire, read_source
            from voynich_smt.data.corpus import Corpus, statistics
            if args.action == "fetch":
                source, _ = acquire(args.source, args.raw_dir, local=args.local)
                print(json.dumps(source, indent=2))
                return 0
            if args.action == "normalize":
                source, raw = read_source(args.manifest)
                raw_path = args.manifest.parent / source["raw_filename"]
                if args.output.resolve() in {args.manifest.resolve(), raw_path.resolve()}:
                    raise ValueError("Processed output must differ from raw source and manifest")
                if source["id"] == "zl-eva":
                    from voynich_smt.data.voynich import EvaNormalization, normalize
                    if args.keep_j or args.remove_spaces or args.uv != "preserve" or args.alphabet != "abcdefghiklmnopqrstuvxyz":
                        raise ValueError("Latin normalization switches cannot be applied to EVA")
                    corpus_data = normalize(source, raw, EvaNormalization(args.uncertain_spaces, args.annotated_words))
                else:
                    from voynich_smt.data.latin import LatinNormalization, normalize
                    if args.uncertain_spaces != "split" or args.annotated_words != "exclude":
                        raise ValueError("EVA normalization switches cannot be applied to Latin")
                    corpus_data = normalize(source, raw, LatinNormalization(j_to_i=not args.keep_j, uv=args.uv,
                                             alphabet=args.alphabet, preserve_spaces=not args.remove_spaces))
                corpus_data.save(args.output)
                print(f"Processed corpus: {args.output}; identity={corpus_data.identity}")
                return 0
            data = json.loads(args.config.read_text())
            if "records" in data:
                corpus_data = Corpus.load(args.config)
                if args.action == "sample":
                    if args.output.resolve() == args.config.resolve():
                        raise ValueError("Sample output must differ from processed corpus")
                    _, metadata = corpus_data.sample(args.words, offset=args.offset, seed=args.seed, folio=args.folio,
                                  section=args.section, line=args.line, max_tokens=args.max_tokens)
                    write_json(args.output, metadata)
                    print(f"Sample: {args.output}; identity={metadata['sample_sha256']}")
                else:
                    from voynich_smt.models.text import Text
                    text = Text(tuple(tuple(r["tokens"]) for r in corpus_data.records if r["tokens"]))
                    print(json.dumps({"kind": corpus_data.kind, "corpus_sha256": corpus_data.identity,
                                      "source": corpus_data.source, "normalization": corpus_data.normalization,
                                      "excluded_records": sum(not r["tokens"] for r in corpus_data.records),
                                      "statistics": statistics(text)}, indent=2))
                return 0
            if args.action == "sample":
                raise ValueError("Sampling requires a processed corpus")
        if args.command == "synthetic":
            if args.output.resolve() == args.ground_truth.resolve():
                raise ValueError("Public input and ground truth must use different paths")
            if args.config.resolve() in {args.output.resolve(), args.ground_truth.resolve()}:
                raise ValueError("Generation outputs must differ from the source configuration")
            request, truth = generate(load_request(args.config), args.words, args.seed)
            write_json(args.output, asdict(request))
            write_json(args.ground_truth, truth)
            print(f"Public input: {args.output}\nGround truth: {args.ground_truth}")
            return 0
        if args.command == "compare":
            print("file\tstatus\tseconds\tscore\tmappings\tnulls\tweights_id\toptimality_proven\tcase\tsynthetic_gate\tknown_feasible")
            for path in args.paths:
                files = sorted(path.glob("*.json")) if path.is_dir() else [path]
                for file in files:
                    data = json.loads(file.read_text())
                    rows = list(comparison_rows(data))
                    if not rows:
                        raise ValueError(f"No solver result in {file}")
                    for document, result, case, gate in rows:
                        complexity = result.get("complexity", {})
                        raw = complexity.get("raw", {})
                        weights = complexity.get("weights")
                        weights_id = hashlib.sha256(json.dumps(weights, sort_keys=True).encode()).hexdigest()[:12] if weights else "-"
                        print(f"{file}\t{result['status']}\t{result['runtime_seconds']:.3f}\t"
                              f"{complexity.get('weighted_score', '-')}\t{raw.get('mappings', '-')}\t"
                              f"{raw.get('null_occurrences', '-')}\t{weights_id}\t"
                              f"{result.get('optimization', {}).get('optimality_proven', False)}\t{case}\t"
                              f"{gate if gate is not None else '-'}\t"
                              f"{bool(result.get('verified') or document.get('inherited_feasibility', {}).get('verified'))}")
            return 0
        request = load_request(args.config)
        if args.command == "corpus":
            print(json.dumps({"words": len(request.ciphertext.words), "tokens": request.ciphertext.size,
                              "word_lengths": [len(w) for w in request.ciphertext.words],
                              "observed_symbols": sorted({g for w in request.ciphertext.words for g in w}),
                              "plaintext_alphabet_size": len(request.plaintext_alphabet.symbols),
                              "dictionary_entries": len(request.dictionary.words)}, indent=2))
            return 0
        if args.output.resolve() == args.config.resolve():
            raise ValueError("Output must differ from the input request")
        input_data = args.config.read_bytes()
        if args.command == "solve":
            if args.timeout_ms is not None:
                request = replace(request, timeout_ms=args.timeout_ms)
            if args.optimize:
                request = replace(request, representation="finite",
                                  optimization=replace(request.optimization, enabled=True, method=args.optimize))
            document = solve_document(request, input_data)
            write_json(args.output, document)
            print_result(document)
            return 3 if document["result"]["status"] == "UNKNOWN" else 0
        if any(n < 0 for n in args.null_symbols) or len(set(args.null_symbols)) != len(args.null_symbols):
            raise ValueError("Sweep budgets must be unique nonnegative integers")
        results = []
        for budget in args.null_symbols:
            nulls = NullBounds(True, budget, request.nulls.max_occurrences, request.nulls.max_consecutive)
            modified = replace(request, nulls=nulls, representation="finite")
            document = solve_document(modified, input_data)
            results.append(document)
            write_json(args.output, {"schema_version": 1, "swept_dimension": "max_distinct_null_symbols",
                                     "experiments": results, "complete": False})
            print(f"null-symbol budget={budget}: ", end="")
            print_result(document)
        write_json(args.output, {"schema_version": 1, "swept_dimension": "max_distinct_null_symbols",
                                 "experiments": results, "complete": True})
        return 3 if any(d["result"]["status"] == "UNKNOWN" for d in results) else 0
    except (ValueError, TypeError, KeyError, OSError, json.JSONDecodeError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    raise SystemExit(main())
