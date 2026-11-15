# Reproducibility protocol

## Scope and boundaries

This repository accompanies a descriptive and exploratory paired study of facial inpainting and six image-restoration configurations. The available materials support: (1) tracing the six original ComfyUI workflows to a pinned upstream revision, (2) matching local model files by SHA-256, and (3) **recomputing all tabular statistics from the published pseudonymised numeric observations**.

Source and generated identifiable facial photographs are **not distributed**. Consequently, neither pixel-level regeneration nor recomputation of ArcFace and BRISQUE from images can be performed using the public dataset alone. Those operations require independently authorized image access. A portable adaptation of the original image-level evaluation script is included in `scripts/scriptmetricas.py`. The public repository alone cannot reproduce image-level scores because it does not include the corresponding photographs.

## Repository layout

```text
workflows/                            Source manifest and upstream workflow links (JSONs not redistributed)
scripts/aggregate_results.py          Recompute statistics from numeric CSV
scripts/scriptmetricas.py              ArcFace/BRISQUE evaluation from authorised image pairs
results/metrics_anonymized.csv        180 numeric observations (30 × 6)
results/summary.csv                   Method-specific ArcFace and BRISQUE results
results/summary_common23.csv          Common-case descriptive analysis (23 cases)
models/model_sha256.csv               Model weight and ONNX SHA-256 manifest
environment/requirements-metrics.txt  Metric-evaluation dependency reference
environment/system_info.md            System and Python environment documentation
docs/reproduction.md                  This protocol
```

## 1. Retrieve source and software

```bash
git clone https://github.com/pvelardea/ComfyUI-Facial-Restoration-IJCOPI.git
cd ComfyUI-Facial-Restoration-IJCOPI
```

The six workflow definitions originate in the upstream GusdeJAR repository. This prepared release contains six sanitised JSON workflow files, traced to an exact upstream revision through the source manifest:


| Method | Workflow | Interpretation |
|---|---|---|
| Shared preprocessing | `Inpainting SD.json` | Segment cap and forehead; inpaint occluded areas |
| B1 | `baselineBicubica.json` | Bicubic ×4 interpolation |
| B2 | `baseline4xUltraSharp.json` | 4xUltraSharp |
| B3 | `baselineCodeFormer.json` | 4xUltraSharp followed by CodeFormer |
| P1a | `SDUpscaleFaceDetailer.json` | Stable Diffusion branch with FaceDetailer disabled |
| P1b | `SDUpscaleFaceDetailer.json` | The same branch with FaceDetailer enabled |
| P2 | `upscaleqwen.json` | Qwen-Image-Edit-2511, four-step Lightning LoRA |

Workflows depend on third-party ComfyUI nodes and weights. Load the supplied sanitised JSONs in a compatible ComfyUI installation and configure input paths and model weights locally; public redistribution requires permission from the upstream author. Input photos are not included.

### Recorded experimental parameters

- Shared inpainting: seed `660105955439758`, 30 steps, CFG 5; semantic thresholds 0.30 for `baseball cap` and 0.50 for `forehead`.
- Stable Diffusion upscaling: 40 steps, CFG 5, denoising strength 0.30; 512 × 512-pixel tiles.
- FaceDetailer (P1b only): 50 steps, CFG 5, denoising strength 0.15.
- Qwen: seed `660105955439758`, four steps, CFG 1; four-step Lightning LoRA.

The stated seed is the experimental setting supplied by the investigator. Before a deterministic replay, confirm that **all** stochastic nodes are set to `fixed` rather than `randomize` (including UltimateSDUpscale and FaceDetailer). Do not interpret the saved workflow JSON alone as a full seed log.

## 2. Verify local model files

Consult `models/model_sha256.csv`. For each locally installed model:

```bash
sha256sum /path/to/local/model_file
```

Compare the 64-character digest to the corresponding CSV row. Model filenames or GitHub commit identifiers alone are not equivalent to checkpoint hashes. Weights are not redistributed in this repository.

## 3. Recompute the published statistical summaries

Python 3.11 and SciPy are sufficient for the `aggregate_results.py` script:

```bash
python3 -m pip install scipy
python3 scripts/aggregate_results.py
```

This creates or overwrites:

- `results/summary.csv`, with separate valid counts and 95% Student-t confidence intervals for ArcFace and BRISQUE;
- `results/summary_common23.csv`, using only cases evaluable by all six methods.

Use `--check` to compare recomputed values to the committed summaries without overwriting them:

```bash
python3 scripts/aggregate_results.py --check
```

For custom locations:

```bash
python3 scripts/aggregate_results.py --input results/metrics_anonymized.csv --output results/summary.csv --common-output results/summary_common23.csv
```

### Data dictionary

`results/metrics_anonymized.csv` is in **long format**: one row per `(case_id, method)` pair (180 rows).

| Field | Definition |
|---|---|
| `case_id` | Pseudonymous case ID `C001`–`C030`. No published lookup links it to an original image or notice |
| `method` | One of `B1`, `B2`, `B3`, `P1a`, `P1b`, `P2` |
| `arcface_cosine` | Cosine similarity between ArcFace embeddings of the inpainted experimental reference and processed output; blank if no usable score |
| `brisque` | No-reference BRISQUE value of the generated image; may be negative |
| `evaluable` | `1` when ArcFace cosine similarity is finite, indicating a paired facial-embedding score; `0` otherwise |

**Statistical denominator:** each metric uses its own available values. Here, ArcFace provides 27 valid pairs for B1/B2/B3/P2 and 23 for P1a/P1b; BRISQUE provides 30 scores per configuration independently of ArcFace detection. The 23-case comparison is a **deliberate common-case sensitivity analysis**, with identical case IDs across all six methods.

**Source of published summaries:** `summary.csv` and `summary_common23.csv` are computed directly from `metrics_anonymized.csv` with the included `aggregate_results.py`, ensuring reproducible summary values.

Mean is the arithmetic mean; `std_sample` uses the sample standard deviation (`ddof=1`); the interval is `mean ± t_(0.975,n−1) × std_sample / √n`. These are descriptive intervals, not identity-verification thresholds or intervals for method differences.

## 4. Recomputing metrics from authorised images (not provided)

The supplied original Python evaluation script has been adapted into
`scripts/scriptmetricas.py` for operation without workstation-specific paths.
The image-level scoring procedure is preserved, while metric summaries use the corrected available-case aggregation:

1. Pair images by identical filenames across the **inpainted reference** and
   **one method's outputs**. Missing or unreadable pairs are reported locally.
2. Read both images with OpenCV. Convert the processed image from BGR to RGB,
   produce a `[1, 3, H, W]` float tensor normalised to `[0, 1]`, and compute
   BRISQUE using PyIQA.
3. Detect faces using InsightFace `buffalo_l`, detection size `640 × 640`, and
   select the face with the largest bounding-box area in each image.
4. Compute ArcFace cosine similarity as `1 − scipy.spatial.distance.cosine`.
   If either face is not detected, record `NaN` for the ArcFace value.
5. Preserve individual records, including missing ArcFace values. For **each metric separately**, use its available scores to calculate the mean, sample SD and Student-t 95% confidence interval. Do not omit BRISQUE merely because ArcFace is missing.

### Run the image-level evaluation

Use the verified Conda environment or another compatible Python environment
with the dependencies in `environment/requirements-metrics.txt`, the
InsightFace `buffalo_l` model pack and a functional PyTorch installation.

From the repository root, for each method separately:

```bash
conda activate comfyui
python3 scripts/scriptmetricas.py \
  --reference-dir /path/to/inpainted_references \
  --generated-dir /path/to/method_outputs \
  --output-dir /path/to/private_results \
  --label qwen \
  --onnx-provider cpu
```

Use labels such as `bicubic`, `ultrasharp`, `codeformer`, `sd`, `sd_fd`
and `qwen` for the six configurations. The script processes **one method per
invocation**. The `--device auto` default selects PyTorch CUDA if available
for BRISQUE; the `--onnx-provider auto` default selects CUDA only when an
ONNX Runtime CUDA provider is available, otherwise CPU. The explicit
`--onnx-provider cpu` argument is appropriate for the documented Conda
environment. Use `--help` for the complete interface.

The script writes:

- `resultados_individuales_<label>.csv`: original columns
  `ArcFace_Cosine`, `BRISQUE`, `filename` (including NaN values);
- `reporte_estadistico_<label>.csv`: Spanish summary columns, recalculated separately by metric
  `Métrica`, `n`, `Media`, `Desviación Estándar`,
  `IC_95_Inferior`, `IC_95_Superior`.

The output directory must be supplied explicitly. The script refuses to
overwrite existing CSVs unless `--overwrite` is set. Output filenames can
identify source photographs: **do not push these raw CSVs to GitHub**. The
repository's `results/metrics_anonymized.csv` is a separately prepared
pseudonymised numerical release; this image-level script does not
automatically anonymise its outputs.

**Validation scope:** the script was syntax-checked and its CLI inspected,
but the image-level computation was not repeated. Reproducing it requires
lawfully accessible reference and generated photos. The numeric summary
validation is independent and is described in Section 3.

## 5. Ethics, privacy and interpretation

- No identifiable input or reconstructed face images, individual embeddings, notice URLs, or original image filenames are included.
- Pseudonymous numeric results should receive institutional approval before public release; anonymization of filenames does not eliminate every re-identification risk.
- The reference is generated after inpainting and is not an authentic unobstructed high-resolution ground truth.
- ArcFace cosine similarity is a consistency proxy, **not** proof of the depicted person's identity.
- BRISQUE reports image-statistical quality and cannot establish the truth of generated details.
- The data are a small convenience sample; the study is not a validated forensic-identification system.

## 6. Manuscript citation and versioning

Link the manuscript's repository reference to a **tagged release** and include a release commit/hash in the final submission. Record the repository revision and upload the numeric results only after institutional/author approval. Avoid changing the reviewed artifacts in-place after a citable release.

Research context: Universidad Autónoma de Nayarit, SecurityIALab, SIP25-102, supported through the *Productividad Universitaria a través de la Investigación* call with resources originating from the *Impuesto Especial destinado a la UAN 2025*.

## 7. Basic consistency check

From the repository root, run:

```bash
python3 scripts/aggregate_results.py --check
python3 scripts/aggregate_results.py --check
```

The first check uses Python's standard library; the second requires SciPy.
The checks verify the repository structure and aggregated numeric results.
They are not substitutes for re-running image generation or clinical/forensic validation.

## Reproducing the exploratory paired statistical analysis

The retrospective paired analysis uses the shared, pseudonymised `case_id` across the six configurations. It does not reprocess photos. Differences are defined as $\Delta_i = X_{i,A} - X_{i,B}$, retaining the matched images with finite values of the **specific metric being compared** (ArcFace n=27/23; BRISQUE n=30). The 30 exploratory contrasts use 20,000 BCa bootstrap resamples, bilateral exact sign tests and Holm adjustment across the full family. The BCa intervals are marginal and not multiplicity-adjusted.

A reproducible statistical environment can be installed independently from ComfyUI:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r environment/requirements-stats.txt
python scripts/aggregate_results.py --check
python scripts/check_paired_results.py
```

To recompute the full 30-pair comparison CSVs without overwriting the committed data:

```bash
python scripts/paired_analysis.py --input results/metrics_anonymized.csv --output-dir output/paired
```

Outputs: `all_30_pairwise_tests.csv`, `focal_8_pairwise_tests.csv` and `common23_all_30_tests.csv`. The committed versions use the `paired_` filename prefix in `results/`. The random seed and 20,000 resample count are defined at the beginning of `scripts/paired_analysis.py`.

The exact sign test tests predominance of the direction of nonzero differences and does not test whether the mean paired difference equals zero. Reported intervals estimate mean differences, and their nominal 95% coverage has not been adjusted for the 30 comparisons.

## Workflow provenance and preparation

Six sanitised ComfyUI workflow JSONs are bundled. The unmodified originals were obtained from the linked upstream source at the pinned Git commit and verified against `workflows/upstream_manifest.csv`; hashes of the sanitised copies are documented in `workflows/prepared_manifest.csv`. Local input paths and installed model files must be configured before use. See [workflow provenance](workflow_sources.md).

## BRISQUE available-case correction (15 November 2026)

The original summary script used a joint ArcFace/BRISQUE complete-case filter. The corrected release **does not** discard BRISQUE when facial embedding extraction fails. In the released pseudonymised observations, BRISQUE is finite for all 30 outputs per method, while ArcFace is available for 27 or 23 pairs. As a result:

- `results/summary.csv`: separate denominators per metric (ArcFace n=27/23; BRISQUE n=30).
- `results/paired_all_30.csv` and `results/paired_focal_8.csv`: paired BRISQUE comparisons use n=30; ArcFace comparisons use their metric-specific valid pairs. Holm adjustment is recalculated over all 30 tests.
- `results/summary_common23.csv` and `results/paired_common23_all_30.csv`: retain the **same 23 ArcFace-complete photographs** for a deliberate common-case sensitivity analysis. This restriction is not applied to the primary BRISQUE results.

No images were reprocessed and no original per-image scores were modified. All new summaries are derived from `results/metrics_anonymized.csv`.
