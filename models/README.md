# Model weight manifest

`model_sha256.csv` lists the SHA-256 digests of 19 model weight files and InsightFace ONNX components used by the processing and evaluation pipelines.

Verify each locally acquired file with:

In Windows 11 PowerShell:

```powershell
Get-FileHash -Algorithm SHA256 -Path "C:\path\to\model.safetensors"
```

In Linux:

```bash
sha256sum /path/to/model
```

Compare the output digest with `sha256` in the CSV. These digests identify the **bytes** of the model files and are independent of their local directory names.

**No checkpoint weights are redistributed here.** Download weights only from authorised original distributors and comply with each model licence. A model hash alone does not establish redistribution permission, benchmark validity or historical provenance.
