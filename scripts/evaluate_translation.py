"""Repeatable offline translation comparison; concept coverage is not a quality verdict."""

import argparse, json, time, subprocess
from pathlib import Path
import numpy as np
from app.system.offline import enforce_offline
from app.translation.opus_mt import OpusMT
from app.captions.glossary import Glossary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", action="store_true")
    args = parser.parse_args()
    enforce_offline()
    root = Path(__file__).resolve().parents[1]
    corpus = json.loads(
        (root / "tests/fixtures/translation-corpus.json").read_text(encoding="utf-8")
    )
    model = OpusMT(root / "models/translation/opus")
    variants = {"current": model.translate}
    if args.baseline:
        namespace = {}
        original = subprocess.check_output(
            ["git", "show", "b2cbed5:app/translation/opus_mt.py"], cwd=root
        ).decode("utf-8")
        exec(compile(original, "baseline_opus_mt.py", "exec"), namespace)
        variants["baseline"] = lambda text: namespace["OpusMT"].translate(model, text)
    rows = []
    summaries = {}
    for name, translate in variants.items():
        for case in corpus["cases"]:
            glossary = Glossary(root / "glossaries" / (case["glossary"] + ".json"))
            if name == "baseline":
                glossary.entries = json.loads(
                    subprocess.check_output(
                        [
                            "git",
                            "show",
                            "b2cbed5:glossaries/" + case["glossary"] + ".json",
                        ],
                        cwd=root,
                    ).decode("utf-8")
                )
            english = glossary.english(case["english"])
            start = time.perf_counter()
            output = glossary.chinese(english, translate(english))
            elapsed = time.perf_counter() - start
            missing = [
                group
                for group in case["required_concept_alternatives"]
                if not any(term.casefold() in output.casefold() for term in group)
            ]
            rows.append(
                {
                    "variant": name,
                    "id": case["id"],
                    "english": case["english"],
                    "chinese": output,
                    "seconds": elapsed,
                    "missing_concept_groups": missing,
                    "human_review": "pending",
                }
            )
        subset = [r for r in rows if r["variant"] == name]
        summaries[name] = {
            "cases": len(subset),
            "concept_checks_passed": sum(
                not r["missing_concept_groups"] for r in subset
            ),
            "latency_p50": float(np.percentile([r["seconds"] for r in subset], 50)),
            "latency_p95": float(np.percentile([r["seconds"] for r in subset], 95)),
        }
        print(name, summaries[name], flush=True)
    result = {
        "source": "Authored synthetic evaluation text; no microphone recordings",
        "human_semantic_acceptance": "pending",
        "summaries": summaries,
        "results": rows,
    }
    (root / "docs/evidence/translation-expanded.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
