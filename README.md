---
title: CertFusion Web
emoji: 🧠
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
---

# CertFusion Web

**Verification-aware neurosymbolic multimodal MRI research application**

CertFusion Web is a GitHub-ready implementation shell for the paper pipeline: four-sequence MRI input, modality-specific feature extraction, multimodal fusion, imaging-informed symbolic priors, bounded consistency checking, uncertainty-aware output, TLA+ workflow assurance, audit logging, and downloadable reports.

> **Research use only.** This software is not a medical device and is not intended for diagnosis, treatment, triage, or patient management.

![Pipeline](docs/pipeline.png)

## What the web application does

1. Accepts **T1, T1ce, T2, and FLAIR** as NIfTI (`.nii`, `.nii.gz`) or 2D PNG/JPG demonstration inputs.
2. Normalizes each sequence and records input provenance.
3. Runs the paper-shaped four-encoder architecture when a trained checkpoint is present.
4. Computes eight predicate scores and the paper's seven differentiable prior templates.
5. Runs bounded rule-consistency checks with **UNSAT / SAT / TIMEOUT** semantics.
6. Shows class probabilities, entropy, uncertainty level, and a set-valued prediction.
7. Shows the **TLA+ workflow invariants** separately from numerical model verification.
8. Stores an in-process audit trail and generates a PDF analysis report.
9. Provides `/api/health`, `/api/model-card`, and `/api/workflow/spec` endpoints.

## Important reproducibility boundary

The manuscript package does not contain the trained neural checkpoint and learned predicate-head parameters. This repository therefore has two execution modes:

- **`paper-checkpoint`**: active when `backend/model_artifacts/certfusion.pt` is supplied. This instantiates the four 3D encoders and 2048→512→128→5 fusion head described in the paper.
- **`research-demo`**: active when no checkpoint is present. It uses a deterministic, input-sensitive surrogate so the complete web, symbolic, verification, uncertainty, reporting, and audit workflow runs immediately. **Demo predictions are not paper results and must not be reported as clinical or experimental evidence.**

The web bounded checker is deliberately scoped. It checks the seven rules in score/probability intervals around the current output. The paper's stronger experiment uses latent bounds for the fusion head. Replace the web verifier with your archived latent-bound implementation if you want exact experimental reproduction.

## Architecture

```text
T1 ──┐
T1ce ├──> modality encoders ──> 2048-d fusion ──> 5-class output ──┐
T2 ──┤                                                            │
FLAIR┘                 predicate heads ──> 7 symbolic rules ──────┤
                                                                  v
                                                bounded Z3 consistency
                                                         │
                                       UNSAT / SAT / TIMEOUT
                                                         │
                                           uncertainty + set output
                                                         │
                                    TLA+ release-status invariants
                                                         │
                                             auditable web result
```

## Free deployment on Hugging Face Spaces

This repository is ready for a **free Docker Space**.

1. Sign in to Hugging Face and create a new Space.
2. Choose **Docker** as the SDK and select the free CPU hardware.
3. Clone the Space repository locally.
4. Copy this repository into the Space, or add the Space as a second Git remote.
5. Push the `main` branch to Hugging Face.
6. Hugging Face will build the Dockerfile and expose the app on port `7860`.

Example using a second remote:

```bash
git clone https://github.com/Shubha-fm/CertFusion-Web.git
cd CertFusion-Web
git remote add space https://huggingface.co/spaces/YOUR-HF-USERNAME/CertFusion-Web
git push space main
```

The root README contains the required Hugging Face Space metadata (`sdk: docker`, `app_port: 7860`). The Dockerfile and `serve.py` are also configured for port `7860` while still allowing a `PORT` environment-variable override.

## Run locally with Docker

```bash
git clone https://github.com/Shubha-fm/CertFusion-Web.git
cd CertFusion-Web
docker compose up --build
```

Open `http://localhost:8000` when using Docker Compose.

## Run without Docker

Backend:

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\\Scripts\\activate
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload --port 8000
```

Frontend:

```bash
cd frontend
npm install
VITE_API_URL=http://localhost:8000 npm run dev
```

Open the Vite URL shown in the terminal, normally `http://localhost:5173`.

## Add the trained model

Place the checkpoint at:

```text
backend/model_artifacts/certfusion.pt
```

Expected architecture:

- four Conv3D encoders: `1→16→32→64`
- adaptive global average pooling
- `64→512` projection per MRI sequence
- concatenated latent dimension: `2048`
- fusion head: `2048→512→128→5`
- eight scalar predicate heads

Then restart the application. `/api/health` should report `checkpoint_loaded: true`.

Set strict mode if you do not want automatic fallback:

```bash
CERTFUSION_MODE=model docker compose up --build
```

## TLA+ workflow

The executable specification is bundled in:

- `formal/CertFusion.tla`
- `formal/CertFusion.cfg`

Checked workflow properties:

- `TypeOK`
- `NoUnsafeRelease`
- `TimeoutNotCertified`
- `CounterexampleNotCertified`
- `ConformalBeforeRelease`
- `TraceableRelease`

TLA+ checks the software-level handling of verification states. It **does not** prove classifier accuracy, clinical validity, or abstraction soundness.

## Other Docker deployment

The same image can also run on Render, Railway, Cloud Run, Fly.io, or another Docker host. Set the platform's `PORT` variable if it does not use `7860`.

## API

`POST /api/analyze` multipart fields:

- `t1`
- `t1ce`
- `t2`
- `flair`

Other endpoints:

- `GET /api/health`
- `GET /api/model-card`
- `GET /api/workflow/spec`
- `GET /api/report/{request_id}`

Interactive API documentation is available at `/docs` when using the backend directly.

## Recommended paper additions after real checkpoint integration

A deployment subsection can report:

- end-to-end response latency
- preprocessing time
- neural inference time
- verification time
- input-format rejection/error rate
- successful report generation rate
- agreement between offline and web predictions on a held-out test subset
- exact software/container version

Do not use the surrogate-mode outputs for these manuscript values.

## License

Choose a license appropriate for your data and model-release obligations before making the repository public. Source code can be open even when trained weights require separate controlled distribution.
