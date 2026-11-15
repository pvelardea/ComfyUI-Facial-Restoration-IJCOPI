# Computational environment

## System and hardware

The following configuration was documented on 14 November 2026:

| Component | Recorded value |
|---|---|
| Operating system | Ubuntu 24.04.4 LTS (x86_64) |
| Processor | Intel Core i7-8700 @ 3.20 GHz (12 logical processors) |
| System memory | Approximately 62 GiB |
| Graphics processor | NVIDIA GeForce RTX 3090, 24 GiB (24,576 MiB reported) |
| NVIDIA driver | 580.178.04 |
| CUDA Toolkit executable (`nvcc`) | Not found during system inspection |

## ComfyUI image-processing runtime

| Component | Recorded value |
|---|---|
| ComfyUI | v0.30.1 |
| ComfyUI Git commit | `0764232429b8cfb10b79b6f186c8cb23e0b22897` |
| Python | 3.11.15 |
| Python environment | `<COMFYUI_DIR>/venv/bin/python` |
| PyTorch | `2.5.1+cu121` |
| torchvision | `0.20.1+cu121` |
| NumPy | `1.26.4` |
| OpenCV Python | `4.8.0.76` |
| InsightFace | `1.0.1` |
| PyIQA | `0.1.15.post2` |
| SciPy | `1.17.1` |
| pandas | `3.0.5` |
| CUDA reported by PyTorch | `12.1`; GPU available |

The relevant ComfyUI custom-node directories included `comfyui_ultimatesdupscale`, `comfyui-impact-pack`, `comfyui-impact-subpack`, `ComfyUI-GGUF`, `comfyui_controlnet_aux`, `facerestore_cf`, `comfyui_segment_anything`, and `qweneditutils`.

## Metric-evaluation Conda environment

| Component | Recorded value |
|---|---|
| Conda environment | `comfyui` |
| Python interpreter | `<CONDA_ROOT>/envs/comfyui/bin/python3` |
| Python version | 3.11 series |
| PyTorch | `2.13.0+cu130` |
| CUDA reported by PyTorch | `13.0`; GPU available |
| ONNX Runtime | `1.27.0` (`onnxruntime` package) |
| `onnxruntime-gpu` | Not installed |
| ONNX Runtime providers | `AzureExecutionProvider`, `CPUExecutionProvider` |
| InsightFace | Import verified; exact installed version in this interpreter not recorded |
| PyIQA | Import verified; exact installed version in this interpreter not recorded |
| InsightFace model package | `buffalo_l` |
| InsightFace detection input size | `640 × 640` pixels |
| Recognition model | `w600k_r50.onnx` (512-dimensional facial embeddings) |
| ONNX inference | All five `buffalo_l` models initialized with `CPUExecutionProvider` |

These are two documented Python environments serving distinct processing and metric-evaluation functions; do not combine their package pins into one installation command.

**Execution evidence:** model imports and initialization were verified in the metric-evaluation Conda environment. This verification did not re-run the study's 30-case image evaluation or independently verify every image-generation operation.

## Model weights and identifiers

See [`../models/model_sha256.csv`](../models/model_sha256.csv) for 19 SHA-256 digests, including `control_v11f1e_sd15_tile.pth`:

`8aa69b8d391e72c2fced6a650268137dc0ed594cafe8a2c0f8b994799a21979b`

SHA-256 identifies the byte content of a file; it does not provide a download URL, license, or evidence of an original experiment timestamp. Third-party weight distribution is not part of this repository.

## Sources of these records

- Read-only workstation diagnostic (`diagnostico_comfyui_20261114_115901.zip`).
- Conda terminal checks performed on 14 November 2026.
- SHA-256 file inventory prepared on 14 November 2026.

No personal photographs or biometric embeddings are included in these records.
