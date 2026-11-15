#!/usr/bin/env python3
"""Reproduce and verify committed paired results without overwriting them.

Uses scripts/paired_analysis.py, NumPy and SciPy, but NO photos or embeddings.
"""
from __future__ import annotations
import csv
import math
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
FILES = {
    'all_30_pairwise_tests.csv': 'paired_all_30.csv',
    'focal_8_pairwise_tests.csv': 'paired_focal_8.csv',
    'common23_all_30_tests.csv': 'paired_common23_all_30.csv',
}


def verify(expected: Path, actual: Path, tol: float = 1e-8):
    with expected.open(encoding='utf-8',newline='') as f:
        exp = list(csv.DictReader(f))
    with actual.open(encoding='utf-8',newline='') as f:
        obs = list(csv.DictReader(f))
    if len(exp) != len(obs):
        raise AssertionError(f'{expected.name}: wrong number of rows')
    if exp and set(exp[0]) != set(obs[0]):
        raise AssertionError(f'{expected.name}: different CSV columns')
    for index, (a,b) in enumerate(zip(exp,obs),start=2):
        for col in a:
            try:
                x=float(a[col]); y=float(b[col])
            except (TypeError,ValueError):
                if a[col]!=b[col]:
                    raise AssertionError(f'{expected.name}: row {index} column {col} differs')
            else:
                if math.isnan(x) and math.isnan(y):
                    continue
                if not math.isclose(x,y,abs_tol=tol,rel_tol=0):
                    raise AssertionError(f'{expected.name}: row {index} column {col}: {x} != {y}')
    print(f'OK {expected.name}: {len(exp)} rows (numeric tolerance {tol})')


def main():
    with tempfile.TemporaryDirectory(prefix='ijcopi_paired_') as td:
        subprocess.run([
            sys.executable, str(ROOT/'scripts/paired_analysis.py'),
            '--input', str(ROOT/'results/metrics_anonymized.csv'),
            '--output-dir', td,
        ], check=True, stdout=subprocess.DEVNULL)
        for produced, committed in FILES.items():
            verify(ROOT/'results'/committed, Path(td)/produced)
    print('All paired analysis results are reproducible under this Python environment.')


if __name__=='__main__':
    main()
