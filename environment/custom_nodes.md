# ComfyUI custom-node dependencies

The following custom-node directories were present in the documented ComfyUI installation:

| Directory | Role within the workflows |
|---|---|
| `comfyui_ultimatesdupscale` | Tiled Stable Diffusion upscaling |
| `comfyui-impact-pack` | FaceDetailer and associated utilities |
| `comfyui-impact-subpack` | Face detector nodes |
| `ComfyUI-GGUF` | Quantised GGUF model loading |
| `comfyui_controlnet_aux` | ControlNet conditioning/preprocessing nodes |
| `facerestore_cf` | Face restoration / CodeFormer nodes |
| `comfyui_segment_anything` | SAM and GroundingDINO nodes |
| `qweneditutils` | Qwen image-editing utilities |

These are observed directory identifiers, not a complete version-locked installation manifest. Verify compatibility with the JSON definitions and install the appropriate upstream node repositories before executing workflows. No unverified custom-node commit IDs are asserted.

Do not install arbitrary code solely on the basis of a workflow file; review the sources and follow local security policies.
