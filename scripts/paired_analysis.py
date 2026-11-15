#!/usr/bin/env python3
"""Analysis of paired ArcFace / BRISQUE scores for six ComfyUI configurations.

Input: results/metrics_anonymized.csv from the SIP25-102 reproducibility package.
No images, model weights, or face embeddings are required.

Requires: Python >=3.10, numpy, scipy.
Example:
  python scripts/paired_analysis.py \
      --input /path/to/results/metrics_anonymized.csv \
      --output-dir results

Method: metric-specific valid pairs, paired mean and median differences, 20,000-resample BCa bootstrap
95% confidence intervals of mean differences, exact two-sided sign test,
exact two-sided Wilcoxon signed-rank test, Holm adjustment across 30
method-pair-by-metric tests. These are exploratory, not pre-registered tests.
"""
import argparse
import csv
import itertools
import math
from pathlib import Path

import numpy as np
from scipy import stats

METHODS = ('B1', 'B2', 'B3', 'P1a', 'P1b', 'P2')
METRICS = ('arcface_cosine', 'brisque')
FOCAL = {('B1', 'B2'), ('B2', 'B3'), ('B2', 'P2'), ('P1a', 'P1b')}
SEED = 20261114
BOOTSTRAP_RESAMPLES = 20000


def load_records(path):
    with open(path, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        required = {'case_id', 'method', 'arcface_cosine', 'brisque', 'evaluable'}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError(f'Missing required columns: {required - set(reader.fieldnames or [])}')
        records = {}
        for row in reader:
            key = (row['case_id'], row['method'])
            if key in records:
                raise ValueError(f'Duplicate case and method: {key}')
            if row['method'] not in METHODS or row['evaluable'] not in {'0','1'}:
                raise ValueError(f'Invalid method or evaluability flag: {key}')
            numeric = {}
            for metric in METRICS:
                raw = (row[metric] or '').strip()
                numeric[metric] = float(raw) if raw else math.nan
                if raw and not math.isfinite(numeric[metric]):
                    raise ValueError(f'Nonfinite numeric entry: {key}, {metric}')
            if (row['evaluable'] == '1') != math.isfinite(numeric['arcface_cosine']):
                raise ValueError(f'ArcFace evaluability flag inconsistent: {key}')
            records[key] = {'evaluable': row['evaluable'] == '1', **numeric}
    cases = sorted({case for case, _ in records})
    if len(cases) != 30 or len(records) != 180:
        raise ValueError(f'Expected 30 cases x 6 methods; found {len(cases)}, {len(records)} records')
    for case in cases:
        if any((case, method) not in records for method in METHODS):
            raise ValueError(f'Missing case-method record for {case}')
    return records, cases


def holm_adjust(pvalues):
    """Step-down Holm family-wise p-value correction."""
    p = np.asarray(pvalues, dtype=float)
    indices = np.argsort(p, kind='stable')
    out = np.empty_like(p)
    prev = 0.0
    count = len(p)
    for rank, idx in enumerate(indices):
        prev = max(prev, min(1.0, (count-rank)*p[idx]))
        out[idx] = prev
    return out


def paired_differences(records, cases, method_a, method_b, metric):
    return np.asarray([
        records[(case, method_a)][metric] - records[(case, method_b)][metric]
        for case in cases
        if math.isfinite(records[(case, method_a)][metric])
        and math.isfinite(records[(case, method_b)][metric])
    ], dtype=float)


def summarise(differences, method_a, method_b, metric, seed):
    d = np.asarray(differences, dtype=float)
    if len(d) < 3 or not np.all(np.isfinite(d)):
        raise ValueError(f'Insufficient valid paired records for {method_a}/{method_b}/{metric}')
    positives, negatives, zeros = int(np.sum(d > 0)), int(np.sum(d < 0)), int(np.sum(d == 0))
    n_discordant = positives + negatives
    sign_test = stats.binomtest(positives, n_discordant, p=0.5, alternative='two-sided') if n_discordant else None
    # For these data there are no zero differences or tied absolute ranks.
    wilcoxon = stats.wilcoxon(d, alternative='two-sided', zero_method='wilcox', method='exact') if n_discordant else None
    bca = stats.bootstrap((d,), np.mean, confidence_level=0.95, method='BCa',
                          n_resamples=BOOTSTRAP_RESAMPLES, random_state=np.random.default_rng(seed))
    tci = stats.t.interval(0.95, df=len(d)-1, loc=float(np.mean(d)), scale=float(stats.sem(d)))
    return {
        'method_A': method_a, 'method_B': method_b, 'metric': metric, 'n_pairs': len(d),
        'mean_difference_A_minus_B': float(np.mean(d)),
        'median_difference_A_minus_B': float(np.median(d)),
        'sd_paired_difference': float(np.std(d, ddof=1)),
        'bca95_lower': float(bca.confidence_interval.low),
        'bca95_upper': float(bca.confidence_interval.high),
        't95_lower': float(tci[0]), 't95_upper': float(tci[1]),
        'A_higher': positives, 'B_higher': negatives, 'equal': zeros,
        'sign_exact_p': float(sign_test.pvalue) if sign_test else 1.0,
        'wilcoxon_exact_p': float(wilcoxon.pvalue) if wilcoxon else 1.0,
        'holm30_sign_p': math.nan, 'holm30_wilcoxon_p': math.nan,
        'interpretation': ('higher ArcFace is preferable' if metric == 'arcface_cosine'
                           else 'lower BRISQUE is preferable'),
    }


def write_csv(path, rows):
    keys = list(rows[0])
    with open(path, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True, type=Path)
    parser.add_argument('--output-dir', required=True, type=Path)
    args = parser.parse_args()
    records, cases = load_records(args.input)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    common_cases = [case for case in cases if all(records[(case,m)]['evaluable'] for m in METHODS)]
    if len(common_cases) != 23:
        raise ValueError(f'Expected 23 common cases, found {len(common_cases)}')

    results = []
    for i, (a,b) in enumerate(itertools.combinations(METHODS,2)):
        for j, metric in enumerate(METRICS):
            d = paired_differences(records, cases, a, b, metric)
            results.append(summarise(d, a, b, metric, SEED + 2*i+j))
    for col, destination in [('sign_exact_p','holm30_sign_p'),('wilcoxon_exact_p','holm30_wilcoxon_p')]:
        adjusted = holm_adjust([r[col] for r in results])
        for row, value in zip(results, adjusted):
            row[destination] = float(value)
    write_csv(args.output_dir/'all_30_pairwise_tests.csv',results)
    focal = [r for r in results if (r['method_A'],r['method_B']) in FOCAL]
    write_csv(args.output_dir/'focal_8_pairwise_tests.csv',focal)

    common_results = []
    for i,(a,b) in enumerate(itertools.combinations(METHODS,2)):
        for j, metric in enumerate(METRICS):
            d = paired_differences(records, common_cases, a, b, metric)
            common_results.append(summarise(d, a, b, metric, SEED+100+2*i+j))
    for col, destination in [('sign_exact_p','holm30_sign_p'),('wilcoxon_exact_p','holm30_wilcoxon_p')]:
        adjusted = holm_adjust([r[col] for r in common_results])
        for row, value in zip(common_results, adjusted):
            row[destination] = float(value)
    write_csv(args.output_dir/'common23_all_30_tests.csv',common_results)
    print(f'Validated {len(cases)} cases, {len(records)} observations; common evaluable = {len(common_cases)}')
    print('Wrote', args.output_dir/'all_30_pairwise_tests.csv')
    print('Wrote', args.output_dir/'focal_8_pairwise_tests.csv')
    print('Wrote', args.output_dir/'common23_all_30_tests.csv')
    for row in focal:
        print(f"{row['method_A']}/{row['method_B']} {row['metric']}: "
              f"meanDelta={row['mean_difference_A_minus_B']:.5f}, "
              f"95%BCa=[{row['bca95_lower']:.5f},{row['bca95_upper']:.5f}], "
              f"A>B={row['A_higher']}/{row['n_pairs']}, "
              f"p_sign_Holm30={row['holm30_sign_p']:.6g}")


if __name__ == '__main__':
    main()
