# Facial super-resolution workflows: reproducibility materials

Companion repository for *Evaluating Facial Super-Resolution Workflows: Perceptual Quality, Embedding Consistency and Operational Robustness*, an IJCOPI manuscript in preparation.

**Research context:** Universidad Autónoma de Nayarit (UAN), SecurityIALab; project SIP25-102. The work is associated with Gustavo de Jesús Aparicio-Rojas, Pablo Velarde-Alvarado, Rafael Martínez-Peláez, Oscar Gabriel Vizcaino-Monroy, Perla Aguilar-Navarrete, Carlos Vidrios-Serrano and Sergio Benigno Castillo-Valtierra.

## Scope and limitations

This repository provides de-identified numerical observations and reproducible scripts for statistical and figure generation. It **does not** provide identifiable source or reconstructed face photographs, facial embeddings, model weights, The six included workflow JSON files are sanitised copies from the pinned upstream revision; see [`workflows/README.md`](workflows/README.md) and `workflows/prepared_manifest.csv`. The originals belong to their respective author; public redistribution requires an appropriate permission or licence.

The shared inpainted reference was synthetically generated and **is not verified ground truth**. ArcFace similarity measures embedding agreement with that reference, not established identity; BRISQUE measures image-statistical quality, not authenticity of reconstructed facial features. The study is not a validated forensic identification system.

## Contents

| Location | Content |
| --- | --- |
| `results/metrics_anonymized.csv` | Pseudonymised image-level numerical measurements, 30 cases × 6 configurations = 180 rows |
| `results/summary.csv` | Metric-specific means, standard deviations and marginal Student-t 95% confidence intervals |
| `results/paired_all_30.csv` | 30 exploratory comparisons (15 method pairs × 2 metrics) |
| `results/paired_focal_8.csv` | Eight comparisons featured in the manuscript |
| `results/summary_common23.csv`, `results/paired_common23_all_30.csv` | Common 23-case sensitivity analyses |
| `scripts/aggregate_results.py` | Validate the committed descriptive summaries |
| `scripts/paired_analysis.py`, `scripts/check_paired_results.py` | Recompute and verify paired analyses |
| `scripts/plot_results.py` | Regenerate figure files from the numeric CSVs |
| `scripts/scriptmetricas.py` | Recompute ArcFace and BRISQUE only with separately authorised images |
| `figures/` | Figure 1 with 95% error bars (PNG 300 dpi and SVG), plus paired-difference plots |
| `models/model_sha256.csv` | S1 inventory: 19 SHA-256 model and ONNX fingerprints, without redistributing weights |
| `environment/` | Software dependencies and documented computational environments |
| `docs/reproduction.md` | Detailed analysis and methodological reproduction protocol |
| `workflows/` | Six sanitised ComfyUI workflow JSON files plus original and prepared fingerprint manifests |

### Study configurations

- **B1:** bicubic interpolation ×4.
- **B2:** 4xUltraSharp.
- **B3:** 4xUltraSharp followed by CodeFormer.
- **P1a:** Stable Diffusion, ControlNet Tile and UltimateSDUpscale; FaceDetailer disabled.
- **P1b:** equivalent upscale workflow with FaceDetailer enabled.
- **P2:** Qwen-Image-Edit-2511 with GGUF and Lightning LoRA.

All six configurations were applied after a common inpainting stage. The upstream workflow source is [GusdeJAR/ComfyUI-Upscaling-Inpainting](https://github.com/GusdeJAR/ComfyUI-Upscaling-Inpainting/tree/c8c76c854f68c27df79d4f29008f00a0b061fc08/workflows); the exact JSON filenames and original hash identifiers are in the manifest.

## Summary of reported means

The denominator for BRISQUE is **30 per method**, independently of ArcFace evaluability (27 or 23 valid image pairs).

| Method | ArcFace n | Mean ArcFace | BRISQUE n | Mean BRISQUE |
| --- | ---: | ---: | ---: | ---: |
| B1 | 27 | 0.9963 | 30 | 66.0884 |
| B2 | 27 | 0.9728 | 30 | 15.6975 |
| B3 | 27 | 0.8090 | 30 | 19.7280 |
| P1a | 23 | 0.6686 | 30 | 21.3183 |
| P1b | 23 | 0.4888 | 30 | 16.2630 |
| P2 | 27 | 0.7909 | 30 | 10.6381 |

The paired analyses use 20,000-resample BCa bootstrap confidence intervals for within-image mean differences and two-sided exact sign tests adjusted using Holm across 30 tests. These intervals **are not multiplicity-adjusted**. Figure 1 instead displays marginal Student-t confidence intervals for individual method means; its error bars must not be used to infer paired statistical significance.

## Reproduce the published numerical summaries (Windows 11)

Install Python 3.11 or later. Open PowerShell in this repository's folder and run:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r environment/requirements-stats.txt
.\.venv\Scripts\python.exe scripts/aggregate_results.py --check
.\.venv\Scripts\python.exe scripts/check_paired_results.py
```

To regenerate the figures:

```powershell
.\.venv\Scripts\python.exe -m pip install -r environment/requirements-figures.txt
.\.venv\Scripts\python.exe scripts/plot_results.py
```

These statistical commands do **not** need ComfyUI, facial photographs or a GPU. For image-level metric recomputation, see [`docs/reproduction.md`](docs/reproduction.md); authorised photographs, trained weights and a separate configured environment are needed.

## Attribution, use and publication

The six upstream ComfyUI workflows were developed by Gustavo de Jesús Aparicio-Rojas. Refer to [`CREDITS.md`](CREDITS.md), [`docs/workflow_sources.md`](docs/workflow_sources.md) and [`environment/system_info.md`](environment/system_info.md) for the documented provenance and technical limitations.

**Publication note:** no open-source licence is being asserted for the complete research bundle, the original workflow JSONs, or third-party model weights. Upload initially to a **private** GitHub repository and review permissions to make the pseudonymised metrics and files publicly accessible. Public visibility of missing-person notices is not permission to redistribute facial photographs.
