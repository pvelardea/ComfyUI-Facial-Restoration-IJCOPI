# Original ComfyUI workflow sources

For attribution and reproducibility, the original six workflow JSONs are available in the source repository:

- Source: https://github.com/GusdeJAR/ComfyUI-Upscaling-Inpainting
- Pinned revision: `c8c76c854f68c27df79d4f29008f00a0b061fc08`
- Exact workflow URLs: https://github.com/GusdeJAR/ComfyUI-Upscaling-Inpainting/tree/c8c76c854f68c27df79d4f29008f00a0b061fc08/workflows
- `upstream_manifest.csv`: names and original Git blob SHA-1 hashes of the six files.

This prepared bundle includes **six sanitised copies** of the pinned original JSONs. The unmodified source files were verified against `upstream_manifest.csv` before sanitisation; SHA-256 hashes of the included copies appear in `prepared_manifest.csv`. **Copyright and public redistribution permission remain with the original author; keep this repository private until authorisation is confirmed.**

Expected workflows:

- `Inpainting SD.json`: shared inpainting.
- `baselineBicubica.json`: B1.
- `baseline4xUltraSharp.json`: B2.
- `baselineCodeFormer.json`: B3.
- `SDUpscaleFaceDetailer.json`: P1a/P1b, with FaceDetailer mode changed as appropriate.
- `upscaleqwen.json`: P2.

A saved workflow file does not by itself establish the randomisation state or all executed model versions. Local paths, image inputs, and model dependencies must be configured before use. No original or reconstructed face images are shared here.
