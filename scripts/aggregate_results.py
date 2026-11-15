#!/usr/bin/env python3
"""Recompute metric-specific descriptive statistics from pseudonymised numeric observations.

Requires Python >=3.11 and scipy. No images or face embeddings are accessed.
"""
from __future__ import annotations
import argparse
import csv
import math
import statistics
from collections import defaultdict
from pathlib import Path
from scipy.stats import t as student_t

METHODS = {
    "B1": "Bicubic interpolation",
    "B2": "4xUltraSharp",
    "B3": "4xUltraSharp + CodeFormer",
    "P1a": "Stable Diffusion",
    "P1b": "Stable Diffusion + FaceDetailer",
    "P2": "Qwen-Image-Edit",
}
FIELDS = ["method", "method_label", "n_total", "n_evaluable", "n_non_evaluable",
          "evaluability_rate", "metric", "n", "mean", "std_sample",
          "ci95_lower", "ci95_upper"]
REQUIRED = {"case_id", "method", "arcface_cosine", "brisque", "evaluable"}


def parse_finite(raw: str) -> float | None:
    if raw.strip() == "":
        return None
    value = float(raw)
    if not math.isfinite(value):
        raise ValueError(f"Non-finite metric value: {raw!r}")
    return value


def load(path: Path) -> dict[str, dict[str, dict]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not REQUIRED.issubset(set(reader.fieldnames or [])):
            raise ValueError(f"CSV must contain columns: {sorted(REQUIRED)}")
        data: dict[str, dict[str, dict]] = defaultdict(dict)
        for index, row in enumerate(reader, start=2):
            case, method = row["case_id"].strip(), row["method"].strip()
            if not case or method not in METHODS:
                raise ValueError(f"Invalid case/method on CSV row {index}")
            if method in data[case]:
                raise ValueError(f"Duplicate (case_id, method) on CSV row {index}")
            arc = parse_finite(row["arcface_cosine"])
            bri = parse_finite(row["brisque"])
            valid = arc is not None
            if row["evaluable"].strip() not in ("0", "1") or valid != (row["evaluable"].strip() == "1"):
                raise ValueError(f"Inconsistent evaluable flag on CSV row {index}")
            data[case][method] = {"arcface_cosine": arc, "brisque": bri,
                                  "evaluable": valid}
    if not data:
        raise ValueError("Empty data file")
    for case, observed in data.items():
        if set(observed) != set(METHODS):
            raise ValueError(f"Case {case} does not contain all six method records")
    return dict(data)


def summarize(method: str, cases: list[dict], n_total: int) -> list[dict]:
    n_evaluable = sum(r["evaluable"] for r in cases)
    result = []
    for metric in ("arcface_cosine", "brisque"):
        vals = [r[metric] for r in cases if r[metric] is not None]
        n = len(vals)
        if n < 2:
            raise ValueError(f"Insufficient {metric} measurements for {method}: n={n}")
        mean = statistics.mean(vals)
        sd = statistics.stdev(vals)  # sample standard deviation, ddof=1
        margin = student_t.ppf(0.975, n-1) * sd / math.sqrt(n)
        result.append(dict(method=method, method_label=METHODS[method],
                           n_total=n_total, n_evaluable=n_evaluable, n_non_evaluable=n_total-n_evaluable,
                           evaluability_rate=f"{n_evaluable/n_total:.12g}", metric=metric,
                           n=n, mean=f"{mean:.15g}", std_sample=f"{sd:.15g}",
                           ci95_lower=f"{mean-margin:.15g}",
                           ci95_upper=f"{mean+margin:.15g}"))
    return result


def write(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def check(path: Path, expected: list[dict], tolerance: float = 1e-8) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Cannot verify missing file: {path}")
    with path.open(encoding="utf-8-sig", newline="") as f:
        actual = list(csv.DictReader(f))
    if len(expected) != len(actual):
        raise AssertionError(f"Mismatch in row counts for {path}")
    numeric = {"n_total", "n_evaluable", "n_non_evaluable", "evaluability_rate",
               "n", "mean", "std_sample", "ci95_lower", "ci95_upper"}
    for i, (a, b) in enumerate(zip(actual, expected), start=2):
        for key in FIELDS:
            if key in numeric:
                if not math.isclose(float(a[key]), float(b[key]), abs_tol=tolerance, rel_tol=0):
                    raise AssertionError(f"Mismatch {path} row {i} column {key}")
            elif a[key] != str(b[key]):
                raise AssertionError(f"Mismatch {path} row {i} column {key}")
    print(f"OK: {path.name}: {len(expected)} rows verified")


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=root/"results/metrics_anonymized.csv")
    parser.add_argument("--output", type=Path, default=root/"results/summary.csv")
    parser.add_argument("--common-output", type=Path, default=root/"results/summary_common23.csv")
    parser.add_argument("--check", action="store_true", help="Verify committed summaries without overwriting")
    args = parser.parse_args()
    data = load(args.input)
    n_total = len(data)
    all_summaries = []
    shared_cases = [case for case, rows in data.items() if all(rows[m]["evaluable"] for m in METHODS)]
    common_summaries = []
    for method in METHODS:
        all_summaries += summarize(method, [r[method] for r in data.values()], n_total)
        common_summaries += summarize(method, [data[case][method] for case in shared_cases], len(shared_cases))
    if args.check:
        check(args.output, all_summaries)
        check(args.common_output, common_summaries)
    else:
        write(args.output, all_summaries)
        write(args.common_output, common_summaries)
        print(f"Wrote {args.output} and {args.common_output}")
    print(f"Cases={n_total}; complete cases={len(shared_cases)}")
    for method in METHODS:
        print(f"{method}: {sum(r[method]['evaluable'] for r in data.values())}/{n_total} evaluable")


if __name__ == "__main__":
    main()
