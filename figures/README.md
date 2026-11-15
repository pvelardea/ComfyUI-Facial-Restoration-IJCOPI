# Figures and statistical interpretation

- `mean_arcface_vs_brisque.png` and `.svg`: Figure 1 of the manuscript, 300 dpi, with horizontal marginal Student-t 95% confidence intervals for BRISQUE n=30 and vertical marginal Student-t intervals for ArcFace n=27 or 23. The `n` labels refer to ArcFace. These are **not** joint confidence regions or comparisons between processing methods.
- `paired_arcface_differences.png`, `paired_brisque_differences.png`: mean paired differences A−B with marginal BCa 95% intervals (20,000 bootstrap draws, **no multiplicity adjustment**); exact sign tests with Holm adjustments are in the CSV results, not these intervals.

Regenerate these figures from CSVs with `python scripts/plot_results.py`.
