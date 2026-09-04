# Suspicious Photo Detection (SPD)

**Suspicious Photo Detection in Outlet Verification Images.**

A batch ML pipeline that, given an outlet's accumulated photo history (one
folder per outlet, no timestamps), flags the images that are visually
inconsistent with that outlet's overall appearance - so thousands of
field-agent verification photos can be triaged without a human looking at most
of them.

## Status

Implemented. This repository contains the specifications/standards (which
remain authoritative - `docs/SPEC.md` and `docs/ARCHITECTURE.md` are the source
of truth), the working pipeline under `src/`, unit + integration tests, the
`spd` CLI, and run artifacts under `results/`.

You can run the pipeline two ways - a direct install of the codebase, or a
Docker container. Both paths are verified end to end (smoke procedure in
`docs/MUST_DO_CHECKS.md` §6).

## Quick start (direct install)

Requires Python 3.13. Create a venv and install the package:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .                 # or: uv pip install -e .
```

Then run the full pipeline on the default dataset (embeddings are cached, so
re-runs are free). The first run downloads the pinned DINOv2 weights via
`torch.hub` (needs internet once; the weights are cached afterwards):

```bash
spd run --dataset data/dataset --output results

# GPU first, CPU/MPS fallback is automatic (DEVICE=auto). To force a backend:
spd run --dataset data/dataset --output results --device cuda   # or cpu / mps
```

Stage isolation / resume:

```bash
spd embed   --dataset data/dataset
spd detect  --dataset data/dataset
spd report  --output results
```

## Run with Docker

For users who prefer a container (no local Python env) or want GPU
acceleration. The image is tagged with the concrete project version
(`spd:0.1.0` - never `latest`) and bundles CUDA-enabled torch: the pipeline
tries the GPU first and falls back to CPU automatically (`DEVICE=auto`).

Prerequisites: Docker. GPU passthrough additionally needs the NVIDIA container
runtime and a GPU.

```bash
# One-time host prep so the non-root container can write the mounted outputs:
mkdir -p results cache logs && sudo chown -R 10001:10001 results cache logs

# Build + run the full pipeline (falls back to CPU automatically on non-GPU hosts):
docker compose up --build

# GPU passthrough (NVIDIA runtime + GPU required):
docker run --rm --gpus all \
  -v "$PWD/data:/app/data:ro" -v "$PWD/results:/app/results" \
  -v "$PWD/cache:/app/cache" -v "$PWD/logs:/app/logs" \
  spd:0.1.0 run --dataset data/dataset --output results

# After docker work, clean up unused/orphaned images and build cache:
docker system prune -f
```

## Evaluation

The real dataset has **no labels** and the pipeline **trains nothing**
(pretrained embeddings only, SPEC §2.2), so a train/test split of the photos is
neither needed nor meaningful. Precision/recall/F1 are measured on the
deterministic synthetic golden set (`scripts/run_evaluation.py`, SPEC §16),
which acts as the held-out labeled test set:

```bash
PYTHONPATH=src .venv/bin/python -m scripts.run_evaluation --seed 42 --output results
```

A different `--seed` samples a fresh held-out test set - the mechanism for
validating any future parameter tuning without leaking into the gated test set.

Verification gates (lint, type-check, tests, dead code, security, docs) and
the full gate list live in `docs/MUST_DO_CHECKS.md` §1.

## Repository layout

```
docs/
  ARCHITECTURE.md      system design (authoritative)
  SPEC.md              behavioral contracts, FR1-FR10, output schema
  SYSTEM_DESIGN.md     entities + pipeline + sequence diagrams (rendered in docs/assets/)
  PLANNING.md          phased delivery plan, gates, risk register
  TASKS.md             traceable task decomposition
  ENGINEERING_DECISIONS.md  ADR-style decision log + best-practice record
  MUST_DO_CHECKS.md    session checklist + verification gates
  CHANGELOG.md         Keep a Changelog change history
  index.md             docs home (mkdocs site)
AGENTS.md              engineering conventions and working agreements
project_docs/          PRD (source of truth)
data/dataset/          outlet photo folders (gitignored)
results/               run artifacts: results.json/csv, run_summary.json, write_up.md, evaluation.md
logs/                  structured JSON logs per run (gitignored)
src/                   pipeline source (flat layout; see AGENTS.md)
tests/                 unit + integration tests (mirror src/)
scripts/               supporting scripts (e.g. synthetic-golden evaluation)
Dockerfile + docker-compose.yml   containerized run (GPU-first, CPU fallback)
.agents/skills/        loadable engineering skills (coding rules)
```

## Documentation

Read these in order:

1. `project_docs/Suspicious_Photo_Detection_PRD.pdf` - product PRD (source of truth)
2. `docs/SPEC.md` - what we build
3. `docs/ARCHITECTURE.md` - how it fits together
4. `docs/SYSTEM_DESIGN.md` - entities + pipeline + sequence diagrams
5. `docs/PLANNING.md` - delivery plan
6. `docs/ENGINEERING_DECISIONS.md` - decision log + best practices
7. `docs/CHANGELOG.md` - change history

The same documents are published as an mkdocs site (`mkdocs.yml`, content under `docs/`).

## Disclaimer

This is an unsupervised anomaly-detection pipeline, not a human review system.
Outlets are compared to themselves; gradual change is legitimate and only images
that stand apart from the outlet's own distribution are flagged.