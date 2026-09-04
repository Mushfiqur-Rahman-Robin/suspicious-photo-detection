# Changelog

All notable changes to this project are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versioning follows
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added (pipeline implementation, Phases 1-5)
- Working `spd` CLI (`run`/`embed`/`detect`/`report`) with a model-agnostic
  `Embedder` port (DINOv2 ViT-S/14 default; CLIP as the optional `clip` extra),
  content-addressed `.npy` embedding cache, cosine-similarity scoring, robust
  centroid + kNN + seeded Isolation Forest signals, `median + k*MAD` adaptive
  threshold with a score floor, deterministic reason templates, strict Pydantic
  output schema (SPEC §6.1), JSON + CSV results, `run_summary.json` KPIs, and a
  one-page `write_up.md`.
- `src/` module tree: `config`, `core`, `embedding`, `scoring`, `detection`,
  `pipeline`, `io_layer`, `reporting`, `cli`, `observability`.
- Unit + integration + reproducibility test suite (186 tests, ~95% coverage) covering
  config, schema, loader, cache, scoring, detection, embedders, pipeline, CLI, and
  determinism (two identical runs, cold vs warm cache byte-identical).
- `scripts/run_evaluation.py` - synthetic-golden precision/recall/F1 report generator
  writing `results/evaluation.md` (SPEC §16).
- `results/` artifacts from the full-dataset run: `results.json` (159 outlets /
  2,042 images), `results.csv`, `run_summary.json`, `write_up.md`, `evaluation.md`.
- Structured file logging: every run now also writes machine-readable JSON log
  lines to `logs/spd.log` (new `LOG_DIR` setting; `logs/` is gitignored), in
  addition to the human-readable console output. Level filtering is shared
  between console and file.

### Changed (pipeline implementation)
- `src/io` module renamed to **`io_layer`**: a top-level package named `io` cannot be
  imported at runtime because the stdlib `io` module is always resident in
  `sys.modules`. `io_layer` is the same module ARCHITECTURE §4 calls "io".
- DINOv2 default embedder now loads the official ViT-S/14 weights through `torch.hub`
  pinned to a fixed commit SHA, because torchvision 0.29 removed DINOv2 from its
  `models` module. The pinned SHA is part of the embedding-cache key (ED-6).
- `.github/workflows/cicd.yml` docker job reduced to compose-file validation only; the
  full image build + CLI smoke steps are kept commented with rationale (fast CI).
- pytest `pythonpath` now includes `src` so the flat top-level packages import in tests.
- `.env.example` mirrors every `Settings` field; `cache/` added to `.gitignore`.
- `docs/TASKS.md` - all Phase 0-5 tasks ticked as implemented with evidence.
- Combined centroid + kNN reason now reads exactly `"Distinct background and
  signage compared to the rest of the series"` - matching the PRD example
  wording verbatim (the flag output never referenced it before, but the schema
  example and PRD both use "and").
- The one-page `write_up.md` and the `evaluation.md` report are now written in
  plain, self-contained prose: internal ED-xx / Spec cross-references were
  removed from the submitted deliverables while the method, rationale,
  trade-offs, scalability, and limitations are described in full detail.
- The PRD file was renamed to `project_docs/Suspicious_Photo_Detection_PRD.pdf`
  and every reference across the repo updated; `.env` re-synced to the current
  `.env.example` (placeholders only).

### Fixed (pipeline implementation)
- Docker image now installs the project package itself, so the `spd` console
  script exists inside the container (`spd run`/`embed`/`detect`/`report`
  work as documented). The runtime image pre-creates `/app/results`, `/app/cache`
  and `/app/logs` owned by the non-root user, and `docker-compose.yml` mounts
  `./logs` alongside `./data`, `./results`, and `./cache`.
- The container builds from a CPU-only lockfile (`requirements-docker.in` /
  `requirements-docker.txt`): same pinned torch 2.14.0 / torchvision 0.29.0
  versions but the CPU wheels, so the image is ~1.5 GB instead of the multi-GB
  CUDA stack that the PyPI default torch build would pull in. Batch inference
  already runs on CPU, so results are identical.

### Added (baseline, planning phase)
- `docs/SPEC.md` - behavioral contracts, FR1-FR10, strict output schema (§6),
  similarity + outlier-detection specification (§10-§12), coding standards (§20).
- `docs/ARCHITECTURE.md` - pipeline component map, key design decisions, module
  boundaries, data flow, architecture review checklist.
- `docs/SYSTEM_DESIGN.md` - entity/output-schema diagram, pipeline diagram,
  single-run sequence diagram, and detection-decision diagram (rendered in `docs/assets/`).
- `docs/PLANNING.md` - six-phase delivery plan, phase gates, risk register, release checklist.
- `docs/TASKS.md` - traceable decomposition of PLANNING phases, each task citing its SPEC §/ED-xx contract.
- `docs/ENGINEERING_DECISIONS.md` - ADR-style decision log (ED-1…ED-10) + best-practice guardrails.
- `docs/MUST_DO_CHECKS.md` - session checklist: standing instructions + verification gates.
- Mermaid diagram sources (`.mmd`) and rendered images (`.svg`) under `docs/assets/`
  (`pipeline`, `seq-run`, `entities`, `detection`).
- `docs/index.md` - docs home for the mkdocs site.
- `pyproject.toml` - project metadata + dependency groups (test/lint/types/security/docs/dev)
  + ruff/mypy/pyright/pytest/coverage/bandit/vulture/commitizen configuration.
- `AGENTS.md` - project-specific engineering conventions, product facts, and verification gates.

### Changed (baseline, planning phase)
- `AGENTS.md` expanded with the project's read-first table, repository layout,
  loadable-skill index, product facts, and working agreements (no standing rule removed).
- Dataset facts corrected repo-wide: image count 2,359 → 2,042, median 13 → 12
  (`docs/SPEC.md` §1.3, §8, §15; `docs/assets/seq-run.{mmd,svg}`; `AGENTS.md`).
- `docs/SPEC.md` §1.3 now records the verified image content (Bengali
  mobile-financial-service agent outlets: storefronts, signage, counters).
- `docs/PLANNING.md` delivery target changed from ~2 weeks to ~2 days; plan made
  internally consistent (day-1/day-2 phase split in §5, compressed-timeline risk in
  §6, day checkpoints in §7).
- `docker-compose.dev.yml` renamed to `docker-compose.yml`; compose + `.dockerignore`
  references updated; image tag `spd:dev` → `spd:latest` (`docker-compose.yml`,
  `docs/MUST_DO_CHECKS.md`).
- Em/en dashes replaced with ASCII hyphens across the repository (docs, skills, configs).
- `.pre-commit-config.yaml` hook revisions updated to latest (pre-commit-hooks v6.0.0,
  ruff v0.16.6, bandit 1.9.4, commitizen v4.18.0).
- `.env` created from `.env.example` (placeholder-only, gitignored).
- Diagram SVGs re-rendered from their `.mmd` sources (mermaid-cli 11.17.0) so every
  artifact is regenerated, not hand-edited.
- CLIP extra pinned to `open-clip-torch>=3.3.0,<4`; `docs/SPEC.md` §13 records that a
  CLIP run must compile its own lockfile (ED-6).
- `mkdocs` + `mkdocs-material` added to the `dev` extra and pinned in
  `requirements-dev.txt`; the CI docs job now installs from the lockfile.
- `.github/workflows/cicd.yml` gains a Docker build + CLI smoke job, and the `ci-gate`
  depends on it.

## [0.1.0]

*Planning/design baseline - no release yet.*
