from __future__ import annotations
from pathlib import Path
from typing import Dict, Tuple
import numpy as np

CLASSES = [
    'Background-dominant',
    'NCR/NET',
    'Edema',
    'Enhancing tumor',
    'Enhancement-dominant',
]

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
except Exception:
    torch = None; nn = None; F = None

if nn is not None:
    class SequenceEncoder(nn.Module):
        def __init__(self):
            super().__init__()
            self.net = nn.Sequential(
                nn.Conv3d(1, 16, 3, padding=1), nn.BatchNorm3d(16), nn.ReLU(), nn.MaxPool3d(2),
                nn.Conv3d(16, 32, 3, padding=1), nn.BatchNorm3d(32), nn.ReLU(), nn.MaxPool3d(2),
                nn.Conv3d(32, 64, 3, padding=1), nn.BatchNorm3d(64), nn.ReLU(),
                nn.AdaptiveAvgPool3d(1),
            )
            self.proj = nn.Linear(64, 512)
        def forward(self, x):
            x = self.net(x).flatten(1)
            return self.proj(x)

    class CertFusionNet(nn.Module):
        def __init__(self, num_classes=5):
            super().__init__()
            self.encoders = nn.ModuleDict({m: SequenceEncoder() for m in ['T1','T1ce','T2','FLAIR']})
            self.fusion = nn.Sequential(
                nn.Linear(2048, 512), nn.ReLU(),
                nn.Linear(512, 128), nn.ReLU(),
                nn.Linear(128, num_classes),
            )
            self.predicate_heads = nn.ModuleDict({
                k: nn.Linear(512, 1) for k in [
                    'Enh','FLAIRAbn','Strong','Core','Peripheral','Diffuse','Ring','LowT1'
                ]
            })
        def forward(self, xs: Dict[str, 'torch.Tensor']):
            z = {m: self.encoders[m](xs[m]) for m in self.encoders}
            logits = self.fusion(torch.cat([z[m] for m in ['T1','T1ce','T2','FLAIR']], dim=1))
            src = {
                'Enh':'T1ce', 'FLAIRAbn':'FLAIR', 'Strong':'T1ce', 'Core':'T1',
                'Peripheral':'FLAIR', 'Diffuse':'FLAIR', 'Ring':'T1ce', 'LowT1':'T1'
            }
            preds = {k: torch.sigmoid(h(z[src[k]])).squeeze(-1) for k,h in self.predicate_heads.items()}
            return logits, preds


def load_checkpoint(path: Path):
    if torch is None or not path.exists():
        return None
    model = CertFusionNet()
    payload = torch.load(path, map_location='cpu')
    state = payload.get('model_state_dict', payload) if isinstance(payload, dict) else payload
    model.load_state_dict(state, strict=False)
    model.eval()
    return model


def prepare_volume(arr: np.ndarray) -> np.ndarray:
    if arr.ndim != 3:
        raise ValueError('Real checkpoint mode requires four 3D NIfTI volumes.')
    from scipy.ndimage import zoom
    target = np.array([128,128,128])
    factors = target / np.array(arr.shape)
    out = zoom(arr, factors, order=1)
    return out.astype(np.float32)


def run_checkpoint(model, modalities: Dict[str, np.ndarray]) -> Tuple[np.ndarray, Dict[str,float]]:
    if torch is None:
        raise RuntimeError('PyTorch is not installed.')
    tensors = {}
    for m, arr in modalities.items():
        vol = prepare_volume(arr)
        tensors[m] = torch.from_numpy(vol)[None,None]
    with torch.no_grad():
        logits, pred = model(tensors)
        probs = torch.softmax(logits, dim=-1).cpu().numpy()[0]
        predicates = {k: float(v.cpu().numpy()[0]) for k,v in pred.items()}
    return probs, predicates
