# Changelog

All notable changes to this project are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versioning follows
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
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

### Changed
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
