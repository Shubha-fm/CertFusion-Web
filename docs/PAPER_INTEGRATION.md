# Paper-to-Web Traceability

| Paper component | Web implementation |
|---|---|
| Four MRI sequences: T1, T1ce, T2, FLAIR | Four required upload cards and `/api/analyze` multipart fields |
| Per-sequence preprocessing | `backend/app/preprocess.py` |
| Four modality-specific 3D encoders | `SequenceEncoder` in `backend/app/paper_model.py` |
| 512-d latent per sequence | `SequenceEncoder.proj` |
| 2048→512→128→5 fusion head | `CertFusionNet.fusion` |
| Eight continuous predicate heads | `CertFusionNet.predicate_heads` |
| Seven differentiable symbolic templates | `rule_values()` in `backend/app/engine.py` |
| ε = 0.031 bounded verification interface | `robust_rule_status()` |
| UNSAT / SAT / TIMEOUT semantics | API + Formal Assurance tab |
| α = 0.10 uncertainty/set interface | `conformal_like_set()` and Prediction tab |
| TLA+ workflow | `formal/CertFusion.tla`, `formal/CertFusion.cfg` |
| Release traceability | Audit Trail tab |
| Research-use limitation | UI banner, API disclaimer, PDF report |

## Exactness note

The web repository preserves a strict distinction between implemented structure and unavailable experimental artifacts. The neural checkpoint and learned predicate-head parameters are not fabricated. When those weights are absent, the site displays `research-demo` mode and uses a deterministic surrogate to exercise the software path only.

The bundled web verifier checks rule feasibility over intervals around output scores. The manuscript's stronger numerical experiment describes latent-bound propagation and fusion-head verification. If that original verifier is available, place it behind the same service interface and retain the UI unchanged.
