# AGENTS.md - Suspicious Photo Detection (SPD)

**Suspicious Photo Detection in Outlet Verification Images.** A batch ML pipeline that, given an outlet's accumulated photo history (one folder per outlet, no timestamps), flags the images that are visually inconsistent with that outlet's overall appearance - so thousands of field-agent verification photos can be triaged without a human looking at most of them.

**Current status: planning/design phase.** This repo currently contains specifications and standards only - no pipeline code yet. Do not invent implementation details that contradict `docs/SPEC.md` or `docs/ARCHITECTURE.md`.

---

## Read these first (in order)

| Doc | Role |
|---|---|
| `project_docs/AI_Engineer_Assignment_Suspicious_Photo_Detection_PRD.pdf` | Product source of truth. Where PRD and SPEC differ, the PRD wins unless SPEC records an approved Engineering Decision (ED-xx). |
| `docs/SPEC.md` | **What we build** - behavioral contracts, FR1-FR10, data/output schema (§6), similarity + outlier-detection spec (§10-§12), coding standards (§20). |
| `docs/ARCHITECTURE.md` | **How it fits together** - pipeline component map, key design decisions, module boundaries, data flow. |
| `docs/SYSTEM_DESIGN.md` | **Design diagrams** - entity/class diagram + pipeline + sequence diagrams (rendered in `docs/assets/`). |
| `docs/PLANNING.md` | **Delivery plan** - phased schedule, phase gates, Definition of Done, risk register. |
| `docs/ENGINEERING_DECISIONS.md` | **Decision log** - ADR-style rationale + best practices backing the ED-xx registry in SPEC §9. |
| `docs/MUST_DO_CHECKS.md` | **Session checklist** - standing instructions distilled from every session, plus the exact verification gates, doc-sync duties, git/CI, and run commands to execute proactively without being asked. |

Any change that touches a module boundary, data flow, external dependency, or the output schema must first be checked against `docs/ARCHITECTURE.md` (its §9 has the review checklist).

---

## Repository layout

```
docs/
  ARCHITECTURE.md        system design (authoritative)
  SPEC.md                behavioral contracts + FRs + output schema
  SYSTEM_DESIGN.md       entity + pipeline + sequence diagrams (rendered in docs/assets/)
  PLANNING.md            delivery plan, milestones, gates
  ENGINEERING_DECISIONS.md  ADR-style decision log + best-practice record
  MUST_DO_CHECKS.md      session checklist: standing instructions + verification gates
  CHANGELOG.md           Keep a Changelog change history
  index.md               docs home (mkdocs site)
  assets/                Mermaid sources (.mmd) + rendered images (.svg)
.agents/skills/coding-rules/  30 skills, one folder per skill: <name>/SKILL.md
project_docs/
  AI_Engineer_Assignment_Suspicious_Photo_Detection_PRD.pdf   product PRD (source of truth)
data/
  dataset/               outlet photo folders (one folder = one outlet; gitignored)
src/                     pipeline source (flat layout, planned)
tests/                   unit + integration tests (planned)
pyproject.toml           project metadata + dependency groups + tool config
```

Planned source layout (from ARCHITECTURE §4, created under `src/`): `src/{config, core, embedding, scoring, detection, pipeline, io, reporting, cli, observability}` - a flat, single-package pipeline, not a web service.

---

## Coding rules are loadable skills

Every engineering standard lives in `.agents/skills/coding-rules/<name>/SKILL.md` and can be loaded with the skill tool. Load the relevant one before writing code that touches its area:

`.agents/skills/coding-rules/architecture/SKILL.md`, `.agents/skills/coding-rules/api-design/SKILL.md`, `.agents/skills/coding-rules/changelog-maintainer/SKILL.md`, `.agents/skills/coding-rules/code-reviewer/SKILL.md`, `.agents/skills/coding-rules/complexity-optimization/SKILL.md`, `.agents/skills/coding-rules/config-management/SKILL.md`, `.agents/skills/coding-rules/database-management/SKILL.md`, `.agents/skills/coding-rules/database-query-optimization/SKILL.md`, `.agents/skills/coding-rules/dead-code-removal/SKILL.md`, `.agents/skills/coding-rules/dependency-management/SKILL.md`, `.agents/skills/coding-rules/deployment/SKILL.md`, `.agents/skills/coding-rules/design-patterns/SKILL.md`, `.agents/skills/coding-rules/dockerfile-optimization/SKILL.md`, `.agents/skills/coding-rules/documentation-writer/SKILL.md`, `.agents/skills/coding-rules/error-handling/SKILL.md`, `.agents/skills/coding-rules/git-conventions/SKILL.md`, `.agents/skills/coding-rules/llm-development/SKILL.md`, `.agents/skills/coding-rules/llm-performance-kpis/SKILL.md`, `.agents/skills/coding-rules/logging-and-tracing/SKILL.md`, `.agents/skills/coding-rules/naming-conventions/SKILL.md`, `.agents/skills/coding-rules/observability/SKILL.md`, `.agents/skills/coding-rules/performance-and-scaling/SKILL.md`, `.agents/skills/coding-rules/prompt-writer/SKILL.md`, `.agents/skills/coding-rules/rag-systems/SKILL.md`, `.agents/skills/coding-rules/refactoring/SKILL.md`, `.agents/skills/coding-rules/security-auditer/SKILL.md`, `.agents/skills/coding-rules/test-runner/SKILL.md`, `.agents/skills/coding-rules/type-safety/SKILL.md`, `.agents/skills/coding-rules/alignment-checker/SKILL.md`, `.agents/skills/coding-rules/verify-alignment/SKILL.md`.

`.agents/skills/coding-rules/alignment-checker/SKILL.md` and `.agents/skills/coding-rules/verify-alignment/SKILL.md` are **mandatory gates before merge** (SPEC §20).

---

## Product facts that must be honored in code

- **No timestamps.** Each outlet folder has only images - no capture date, visit order, or EXIF metadata is assumed. The method must be purely visual/statistical (SPEC §1, §10).
- **Gradual, explainable change is legitimate.** An outlet's appearance may drift over time (new signage, repaint). The method flags *inconsistent* images, not *every* change; a genuine outlier must stand apart from the outlet's own distribution, not from a global template (SPEC §3, §12).
- **Output schema is a hard contract** (PRD "Expected Output Format", SPEC §6): per-outlet `outlet_id`, `total_images`, `flagged_images[]` (with `file_name`, `suspicion_score ∈ [0,1]`, `reason`), optional `ranking[]`. Every outlet is returned - never omitted - with an empty `flagged_images` when none are found.
- **Embeddings are the model's currency.** The pipeline is model-agnostic at the embedding layer: DINOv2 (default) and CLIP are swappable behind a single `Embedder` port; feature code never imports a model's weights directly (ARCHITECTURE §3, ED-1).
- **Determinism and reproducibility are non-negotiable** (ED-6): fixed seed, content-addressed embedding cache, pinned dependencies. A re-run on the same dataset MUST reproduce the same flags.
- **The dataset is gitignored.** `data/dataset/` holds 159 outlets / 2,042 JPEG images (960×1280) and is never committed; the pipeline reads it from `data/dataset/` by default (SPEC §5, §17). The photos are street-level shots of Bengali mobile-financial-service agent outlets (bKash-style storefronts, signage, counters) - consistent with the PRD's mobile-recharge-shop context.

---

## Conventions that are non-negotiable

- **Docstrings:** every public module, class, function, method, and complex type MUST have a PEP 257 docstring (WHAT + WHY). No comments on the obvious, no commented-out code (SPEC §20).
- **Naming:** Python `snake_case` modules/functions/vars, `PascalCase` classes, `UPPER_SNAKE_CASE` constants/enum members, `is_/has_/can_/should_` booleans, no abbreviations, no camelCase in source, no single-letter vars outside loops, no double negatives.
- **Type safety:** Pydantic strict schemas at every boundary (config, env, output schema, result parsing); parse-don't-validate; forbid extra fields; enums for bounded sets.
- **Config:** central `settings.py` (Pydantic Settings) + `.env`/`.env.example`; no magic numbers/URLs/paths in feature code. No other module reads env directly.
- **No secrets:** never commit secrets, keys, or tokens. Secrets only via env/secrets manager.
- **Git:** Conventional Commits (`feat(detection):`), branch `type/short-description`, squash merge, one logical change per PR, never commit directly to main, update `docs/CHANGELOG.md` + `docs/ARCHITECTURE.md` in the same PR.

---

## Verification gates - run before finishing any task

All gates are enforced in CI per `docs/PLANNING.md`. Do not claim a task complete until these pass. Each command runs from the repository root (where `pyproject.toml` lives):

| Gate | Command |
|---|---|
| Lint + format (incl. `N8xx` naming) | `ruff check .` + `ruff format --check .` |
| Type checking | `mypy src` + `pyright` |
| Tests + coverage | `pytest` (≥ 85% core logic, ≥ 80% overall) |
| Dead code | `vulture src` |
| Dependencies/security | `pip-audit -r requirements.txt -r requirements-dev.txt` + `bandit -r src -c pyproject.toml` + `trivy` |
| Secrets | `detect-secrets-hook --baseline .secrets.baseline` |
| Alignment | `.agents/skills/coding-rules/alignment-checker/SKILL.md` + `.agents/skills/coding-rules/verify-alignment/SKILL.md` gates |
| Docs build | `mkdocs build --strict` |

If a gate is missing from the repo tooling (none is configured yet in this planning phase), say so explicitly rather than skipping it silently - and record the gap in the PR.

---

## Standing contract (apply in every task, even when not restated)

### Pre-flight (start of every session or task)
- Read the project docs first: AGENTS.md, SPEC.md, TASKS.md, README, docs/ folder, and PRD if present. Treat them as the source of truth.
- Explore the codebase before making changes (use @explore for large or unknown codebases).
- Establish the current baseline: git status, current branch, what was last pushed. Start from that baseline and do not silently deviate.
- If docs are AI-locked (SPEC, ARCHITECTURE, SYSTEM_DESIGN, PLANNING, PRD contents), never modify them unless I explicitly instruct it. TASKS.md statuses are tick-only.

### The #1 rule: never break anything
- NEVER break working code. Never break the production server, the main branch, or the existing design.
- Every change must be non-regressive: verify that nothing which worked before stops working.
- When a change is destructive or you are unsure, STOP and ask me first.

### Core principles
1. Documents first, code second: make the plan/spec rock-solid before coding.
2. The PRD/specs are the source of truth. Stay 100% aligned; do not add anything extra, do not skip anything, do not go beyond the current scope.
3. Everything must be verified, not assumed. Do NOT hallucinate or write anything out of assumption. Verify claims against actual files, configs, and real output.
4. Real improvements only. No hacks, no fake improvements, no lab-only wins that don't hold up.
5. Tests and docs are part of "done".
6. Make changes test-driven where sensible.
7. Grill your own work before presenting: be harshly self-critical, list concrete findings, fix all gaps, then re-verify.
8. Honesty over optimism: report real gaps, don't tick unverified items, self-flag mistakes.
9. Respect branch and push discipline (see Git section).
10. Don't deviate from scope: stay inside the current TASKS.md week; don't build ahead; avoid over-engineering.
11. Security sensitivity: no secret leakage ever.
12. Perfectionism with momentum: be thorough but keep moving - don't stall.
13. Live verification matters: real runs over just unit tests.
14. Token/budget consciousness: prefer small trial runs before full runs.

### Standing requirements (what I always expect, even when not restated)
- "Don't break anything" applies to every change by default.
- 100% alignment with the source of truth (PRD / SPEC / client requirement / docs/).
- Grill, critique, regrill, and recheck - multiple rounds if needed - before declaring something "done" or "perfect".
- Rock solid work: no hacks, no fake improvements, no hallucination, nothing written out of assumption.
- 100% tested: all tests must pass; coverage must meet the project gate (≥80% overall, ≥85% core).
- Documentation up to date in the same change.
- Follow best engineering practices, and follow the project's personal workflow rules, coding-rules skills if present.
- Cover everything; make sure nothing is missed.
- No secrets leaked; .env.example holds placeholders only.
- Update MUST_DO_CHECKS.md whenever a new repeated instruction appears.
- Proper conventional commit messages; multiple logical commits are fine.

### Guardrails
1. Never break working code.
2. Never break the production server.
3. Never touch off-limits infrastructure or config (e.g., a server-level nginx config). In-repo, container-scoped config changes are fine.
4. Keep the main branch clean; remove accidental branches; explicit merges only.
5. Real improvements only; prove real gains.
6. No secret leakage ever: .env gitignored, .env.example placeholders only, mask secrets in all output, run secret scans, verify `git log --all -- .env` is empty.
7. 100% alignment with the source of truth; never go beyond scope.
8. AI-locked docs untouched (SPEC, ARCHITECTURE, SYSTEM_DESIGN, PLANNING, PRD) unless explicitly instructed; TASKS.md is tick-only.
9. Don't push unless I ask. "Don't push" overrides everything.
10. Tests and docs are part of done.
11. Be honest: report gaps, don't declare "perfect" without verification, self-flag mistakes.
12. Be careful with destructive actions: ask before removing volumes, branches, history, or system services; never break my system's package managers (e.g., conda); uninstall packages only when proven safe.
13. Protect project-specific invariants (e.g., output-schema contract, deterministic/cached embeddings, model-agnostic embedder port, score ∈ [0,1] semantics). Identify and preserve each project's invariants.
14. Be extremely careful around production/deploy: prove safety before push/merge.
15. Token/budget discipline: small trial runs first; log token counts.
16. Persist instructions: update MUST_DO_CHECKS.md / AGENTS.md when new repeated instructions appear.

### Problem-solving workflow
- Follow this shape for every bug or issue: reproduce → diagnose the root cause (not the symptom) → apply a minimal, principled fix → verify.
- If I paste a command error, terminal log, or CI output, diagnose from the paste: give me the root cause and the fix.
- Explore-first: map the codebase before touching anything.
- Use grill cycles: present findings as numbered lists, fix all gaps, then regrill/reverify.
- When something is genuinely blocked, say so honestly and record it as an engineering decision or a blocking gap instead of guessing.

### Testing & quality gates
- Make changes test-driven where sensible.
- All tests must pass; coverage must meet the project gate.
- Lint, type-check, and build must be clean (ruff / mypy / pyright / etc.).
- Documentation is part of "done": update README, CHANGELOG, docs/, and .env.example in the same change.
- Verify with real runs (actual pipeline on a limited dataset) - not just unit tests.

### Git & commit discipline
- Use proper conventional commit messages: feat/fix/docs/chore/ci + scope.
- Multiple logical commits are fine; push to the branch I name.
- Work on a feature branch, then merge to dev, then to main when I ask.
- Preserve history; never rewrite shared history.
- Keep .env and secrets out of git history; keep .secrets.baseline maintained.

### Communication & reporting
- Be direct and concise. Report what you did, how you verified it, and any honest gaps.
- Keep momentum: continue with safe next steps; stop and ask when unsure.
- When I state a hypothesis, confirm or correct it with evidence.
- When I ask "which option?" or "am I overthinking?", give a clear recommendation and a decisive answer.
- Persist repeated instructions into checklists so I never have to retype them.

---

## Working agreements

- Prefer the existing docs over assumptions; when in doubt, check the ED-xx decisions in SPEC §9.
- **Source-of-truth documents are AI-locked:** `docs/ARCHITECTURE.md`, `docs/SPEC.md`, `docs/SYSTEM_DESIGN.md`, `docs/PLANNING.md`, and the PRD must never be updated by the AI in any iteration unless the user directly instructs it to update that specific file.
- **`docs/MUST_DO_CHECKS.md` is self-maintaining:** whenever the user corrects behavior or introduces a new standing instruction, add it to that file in the same session (and prune stale rules) without being asked. Its §0 checklist is binding for every iteration.
- Keep changes small and focused; refactor separately from features; follow the boy-scout rule.
- Preserve the front matter format of skill files: `name` must be lowercase-hyphen-separated and match the folder; `description` must be a single-line YAML scalar (≤ 1024 chars); only supported fields (`name`, `description`, `license`, `compatibility`, `metadata`).
- Do not create new documentation files unless asked; update existing docs in the same PR as the change they describe.
