#!/usr/bin/env python3
"""Evaluate facial-image outputs using ArcFace and BRISQUE.

Portable adaptation of the original ``scriptmetricas.py`` supplied for the
IJCOPI study. The image-level metric computations are unchanged; summary aggregation is corrected:

* BRISQUE from PyIQA on the processed RGB image in [0, 1];
* InsightFace ``buffalo_l`` with 640x640 detection, largest face by box area;
* ArcFace score = 1 - SciPy cosine distance between paired embeddings;
* missing face => NaN ArcFace; ArcFace and BRISQUE are aggregated independently;
* sample standard deviation and 95% Student-t confidence interval.

Compared with the supplied script, this version replaces hard-coded computer
paths with command-line arguments, selects an ONNX Runtime provider explicitly,
checks inputs and refuses to overwrite existing results by default.

IMPORTANT PRIVACY NOTE: the individual-results file contains local image
filenames. Do not commit that file to a public repository without review.
The repository's ``metrics_anonymized.csv`` is a separately prepared dataset.

Python >=3.11; dependencies listed in environment/requirements-metrics.txt.
"""

from __future__ import annotations

import argparse
import math
import re
from pathlib import Path


SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp"}


def cli() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-dir", type=Path, required=True,
                        help="Directory containing the common INPAINTED reference images")
    parser.add_argument("--generated-dir", type=Path, required=True,
                        help="Directory containing output images of ONE evaluated method")
    parser.add_argument("--output-dir", type=Path, required=True,
                        help="Local results directory (do not publish raw filename-indexed CSV)")
    parser.add_argument("--label", default="qwen",
                        help="Short identifier in output CSV names (default: qwen)")
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto",
                        help="PyTorch device for BRISQUE (default: auto)")
    parser.add_argument("--onnx-provider", choices=("auto", "cpu", "cuda"), default="auto",
                        help="Execution provider for InsightFace (default: auto)")
    parser.add_argument("--overwrite", action="store_true",
                        help="Allow replacing existing local CSV files")
    return parser.parse_args()


def require_directory(directory: Path, name: str) -> Path:
    directory = directory.expanduser().resolve()
    if not directory.is_dir():
        raise NotADirectoryError(f"{name} does not exist or is not a directory: {directory}")
    return directory


def main() -> None:
    args = cli()
    if not re.fullmatch(r"[a-zA-Z0-9_-]+", args.label):
        raise ValueError("--label must contain only ASCII letters, digits, '_' or '-'")
    ref_dir = require_directory(args.reference_dir, "--reference-dir")
    gen_dir = require_directory(args.generated_dir, "--generated-dir")
    out_dir = args.output_dir.expanduser().resolve()

    individual_path = out_dir / f"resultados_individuales_{args.label}.csv"
    summary_path = out_dir / f"reporte_estadistico_{args.label}.csv"
    if not args.overwrite:
        existing = [str(p) for p in (individual_path, summary_path) if p.exists()]
        if existing:
            raise FileExistsError("Output exists; choose another directory or use --overwrite: "
                                  + ", ".join(existing))

    # Imports after command-line parsing allow --help without the ML stack.
    import cv2
    import numpy as np
    import pandas as pd
    import pyiqa
    import torch
    import onnxruntime as ort
    from insightface.app import FaceAnalysis
    from scipy import stats
    from scipy.spatial.distance import cosine

    if args.device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("--device cuda requested but torch.cuda.is_available() is False")
    device = "cuda" if args.device == "auto" and torch.cuda.is_available() else args.device
    if device == "auto":
        device = "cpu"

    available = ort.get_available_providers()
    cuda_available = "CUDAExecutionProvider" in available
    if args.onnx_provider == "cuda" and not cuda_available:
        raise RuntimeError("CUDAExecutionProvider requested but not available in ONNX Runtime: "
                           + ", ".join(available))
    if args.onnx_provider == "cpu" or (args.onnx_provider == "auto" and not cuda_available):
        provider = "CPUExecutionProvider"
        ctx_id = -1
    else:
        provider = "CUDAExecutionProvider"
        ctx_id = 0

    if provider not in available:
        raise RuntimeError(f"ONNX Runtime provider unavailable: {provider}")

    print(f"PyTorch BRISQUE device: {device}")
    print(f"ONNX Runtime requested provider: {provider}")
    app_face = FaceAnalysis(name="buffalo_l", providers=[provider])
    app_face.prepare(ctx_id=ctx_id, det_size=(640, 640))
    for name, model in app_face.models.items():
        actual_providers = model.session.get_providers()
        print(f"InsightFace model {name}: {actual_providers}")
        if provider not in actual_providers:
            raise RuntimeError(f"Requested provider {provider} not active for model {name}")

    brisque_metric = pyiqa.create_metric("brisque", device=device)

    def get_face_embedding(image_bgr):
        faces = app_face.get(image_bgr)
        if not faces:
            return None
        faces = sorted(
            faces,
            key=lambda face: (face.bbox[2] - face.bbox[0]) *
                             (face.bbox[3] - face.bbox[1]),
            reverse=True,
        )
        return faces[0].embedding

    def calculate_metrics(path_ref: Path, path_gen: Path):
        ref = cv2.imread(str(path_ref))
        gen = cv2.imread(str(path_gen))
        if ref is None or gen is None:
            return None

        # Same channel conversion and tensor scaling as supplied original script.
        gen_rgb = cv2.cvtColor(gen, cv2.COLOR_BGR2RGB)
        gen_tensor = (torch.from_numpy(gen_rgb).permute(2, 0, 1)
                      .unsqueeze(0).float().to(device) / 255.0)
        with torch.no_grad():
            score_brisque = brisque_metric(gen_tensor).item()

        emb_ref = get_face_embedding(ref)
        emb_gen = get_face_embedding(gen)
        if emb_ref is None or emb_gen is None:
            score_arcface = np.nan
        else:
            score_arcface = 1 - cosine(emb_ref, emb_gen)
        return {"ArcFace_Cosine": score_arcface, "BRISQUE": score_brisque}

    reference_images = sorted(
        (p for p in ref_dir.iterdir() if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS),
        key=lambda p: p.name,
    )
    if not reference_images:
        raise ValueError(f"No supported images found in reference directory: {ref_dir}")

    rows = []
    missing_outputs = []
    unreadable_pairs = []
    for source in reference_images:
        candidate = gen_dir / source.name
        if not candidate.is_file():
            missing_outputs.append(source.name)
            continue
        metrics = calculate_metrics(source, candidate)
        if metrics is None:
            unreadable_pairs.append(source.name)
            continue
        metrics["filename"] = source.name
        rows.append(metrics)

    if not rows:
        raise RuntimeError("No readable filename-matched image pairs found")

    # Keep per-image metric fields; summarise independently by metric.
    df = pd.DataFrame(rows, columns=["ArcFace_Cosine", "BRISQUE", "filename"])
    failed_arcface = df[df["ArcFace_Cosine"].isna()]
    failed_brisque = df[df["BRISQUE"].isna()]

    summary_rows = []
    for metric in ("ArcFace_Cosine", "BRISQUE"):
        data = df[metric].dropna()
        n = len(data)
        if n < 2:
            raise RuntimeError(f"Only {n} valid observations for {metric}; at least 2 needed")
        mean_val = data.mean()
        std_val = data.std()  # sample SD, ddof=1
        ci = stats.t.interval(0.95, df=n - 1,
                              loc=mean_val, scale=std_val / math.sqrt(n))
        summary_rows.append({
            "Métrica": metric,
            "n": n,
            "Media": mean_val,
            "Desviación Estándar": std_val,
            "IC_95_Inferior": ci[0],
            "IC_95_Superior": ci[1],
        })
        print(f"{metric}: mean={mean_val:.4f}; SD={std_val:.4f}; "
              f"CI95=[{ci[0]:.4f}, {ci[1]:.4f}]")

    out_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(individual_path, index=False)
    pd.DataFrame(summary_rows).to_csv(summary_path, index=False)
    print(f"Reference images: {len(reference_images)}")
    print(f"Filename-matched and readable pairs: {len(df)}")
    print(f"No ArcFace score: {len(failed_arcface)}")
    print(f"No BRISQUE score: {len(failed_brisque)}")
    print(f"Missing generated filenames: {len(missing_outputs)}")
    print(f"Unreadable matched image pairs: {len(unreadable_pairs)}")
    if missing_outputs:
        print("Missing generated image filenames (local only):", ", ".join(missing_outputs))
    if unreadable_pairs:
        print("Unreadable image filenames (local only):", ", ".join(unreadable_pairs))
    if len(failed_arcface):
        print("No usable ArcFace metric (local only):",
              ", ".join(failed_arcface["filename"].astype(str)))
    if len(failed_brisque):
        print("No usable BRISQUE metric (local only):",
              ", ".join(failed_brisque["filename"].astype(str)))
    print(f"Individual results: {individual_path}")
    print(f"Summary: {summary_path}")
    print("WARNING: raw output includes filenames; do not upload it publicly.")


if __name__ == "__main__":
    main()
