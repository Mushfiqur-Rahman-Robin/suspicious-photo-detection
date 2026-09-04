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

## Quick start

```bash
# Full pipeline on the default dataset (embeddings are cached, re-runs are free):
.venv/bin/spd run --dataset data/dataset --output results

# Stage isolation / resume:
.venv/bin/spd embed   --dataset data/dataset
.venv/bin/spd detect  --dataset data/dataset
.venv/bin/spd report  --output results

# Synthetic-golden precision/recall/F1 report (SPEC §16):
PYTHONPATH=src .venv/bin/python -m scripts.run_evaluation --output results
```

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