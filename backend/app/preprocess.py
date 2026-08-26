from __future__ import annotations
from io import BytesIO
from pathlib import Path
from typing import Tuple, Dict
import gzip
import numpy as np
from PIL import Image

try:
    import nibabel as nib
except Exception:
    nib = None

MODALITIES = ('T1', 'T1ce', 'T2', 'FLAIR')

def _zscore(x: np.ndarray) -> np.ndarray:
    x = np.nan_to_num(x.astype(np.float32), nan=0.0, posinf=0.0, neginf=0.0)
    finite = x[np.isfinite(x)]
    if finite.size == 0:
        return np.zeros_like(x)
    mask = x != 0
    vals = x[mask] if np.any(mask) else x.ravel()
    mu, sd = float(vals.mean()), float(vals.std())
    if sd < 1e-6:
        sd = 1.0
    y = (x - mu) / sd
    return np.clip(y, -5, 5)

def _read_nifti(data: bytes, filename: str) -> np.ndarray:
    if nib is None:
        raise ValueError('NIfTI support requires nibabel.')
    import tempfile
    suffix = '.nii.gz' if filename.lower().endswith('.nii.gz') else '.nii'
    with tempfile.NamedTemporaryFile(suffix=suffix) as tmp:
        tmp.write(data); tmp.flush()
        img = nib.load(tmp.name)
        arr = np.asarray(img.get_fdata(dtype=np.float32))
    if arr.ndim == 4:
        arr = arr[..., 0]
    if arr.ndim != 3:
        raise ValueError('Expected a 3D NIfTI volume.')
    return arr

def _read_image(data: bytes) -> np.ndarray:
    img = Image.open(BytesIO(data)).convert('L')
    return np.asarray(img, dtype=np.float32)

def load_modality(data: bytes, filename: str) -> Tuple[np.ndarray, Dict[str, object]]:
    lower = filename.lower()
    if lower.endswith('.nii') or lower.endswith('.nii.gz'):
        arr = _read_nifti(data, filename)
        source_type = 'NIfTI volume'
    else:
        arr = _read_image(data)
        source_type = '2D image'
    norm = _zscore(arr)
    meta = {
        'filename': filename,
        'source_type': source_type,
        'shape': list(arr.shape),
        'mean_raw': round(float(np.mean(arr)), 4),
        'std_raw': round(float(np.std(arr)), 4),
        'nonzero_fraction': round(float(np.mean(arr != 0)), 4),
    }
    return norm, meta

def feature_vector(arr: np.ndarray) -> np.ndarray:
    flat = arr.ravel().astype(np.float32)
    if flat.size > 250_000:
        idx = np.linspace(0, flat.size - 1, 250_000).astype(np.int64)
        flat = flat[idx]
    q = np.percentile(flat, [5, 25, 50, 75, 95])
    abs_flat = np.abs(flat)
    return np.array([
        float(flat.mean()), float(flat.std()), float(q[0]), float(q[1]),
        float(q[2]), float(q[3]), float(q[4]), float(abs_flat.mean()),
        float(np.mean(flat > 1.0)), float(np.mean(flat < -1.0)),
    ], dtype=np.float32)
