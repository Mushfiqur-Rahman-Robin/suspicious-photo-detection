# MUST DO CHECKS - Suspicious Photo Detection (SPD)

The repeatable checklist for every coding session on this repo. If you are the
AI assistant working here: run these proactively, do not wait to be asked.
If you are the human: hand this file over instead of re-typing instructions.

---

## 0. Standing instructions (distilled from every session so far)

These are the behavioral asks repeated across all sessions. Apply them in
every iteration without being reminded:

1. **100% alignment with docs/ is non-negotiable.** Check every change
   against `docs/SPEC.md`, `docs/ARCHITECTURE.md`, `docs/TASKS.md`, and the
   PRD. Where they differ, PRD wins, then SPEC (unless an ED-xx says otherwise).
2. **Every coding-rule skill must be followed** - load the relevant skill
   from `.agents/skills/coding-rules/` before touching its area.
3. **Best engineering practices everywhere**, consistently: strict output
   schema, model-agnostic embedder, adaptive thresholds, deterministic output.
4. **CI/CD must end green.** A red pipeline is a task not finished. Fix root
   causes, never gate-skips or suppressions to force green.
5. **Tests and docs are part of "done"** - code without up-to-date tests and
   documentation is incomplete work.
6. **Close out ALL prior review findings** - before starting new work, verify
   previously flagged issues (PR comments, review gaps) are actually resolved.
7. **No credential leaks - strictly.** `.env.example` contains placeholders
   only; `.env` stays gitignored; secrets never enter code, logs, docs, git,
   or images.
8. **TASKS.md is tick-only.** Never alter its content in any way other than
   flipping `[ ]` ↔ `[x]` (with evidence). No rewording, restructuring, or
   adding/removing tasks unless the user explicitly asks.
9. **Stay inside the current TASKS.md phase.** Do not implement ahead of the
   active phase's goal; flag future needs instead of building them early.
10. **Push only when asked in the current session**, with proper Conventional
    Commit messages that cover everything in the change; multiple commits for
    distinct concerns; push to the branch being worked on, as the user names -
    never assume. If the user says "don't push", that overrides everything.
11. **Verify after pushing**: confirm CI is green on the pushed SHA before
    calling it done.
12. **Be careful with anything destructive** (volumes, branches, history,
    system services). When unsure, ask first - data loss is unacceptable.
13. **Protect project invariants** - the output-schema contract (SPEC §6.1),
    score ∈ `[0,1]` semantics, deterministic/cached embeddings (ED-6), and the
    model-agnostic embedder port (ED-1). Never weaken these silently.
14. **Be harshly self-critical**: grill, re-verify multiple times, surface
    gaps proactively rather than declaring things "perfect".
15. **Production framing**: present this project (code, docs, comments, commit
    messages) as a production-quality engineering project on its own terms -
    the professional, standalone standard it stands for.

### Self-maintenance protocol (this file updates itself)

This checklist is a living document. The AI assistant MUST maintain it in
every iteration, without being asked:

- **Detect:** whenever the user corrects behavior, repeats an instruction
  twice, or asks for a check/standard not captured here - that is a new
  standing instruction.
- **Record:** add it to §0 (or the relevant section) **in the same session**,
  phrased as a general rule rather than a one-off task.
- **Prune:** if a rule is superseded or no longer applies (e.g., tooling
  changed), update or remove it instead of letting the file rot.
- **Ship:** include the doc change in the same commit/PR as the work that
  triggered it, so the checklist never drifts from reality.

---

## 1. Verification gates (run ALL before claiming any task done)

All commands run from the repository root (where `pyproject.toml` lives),
using the project venv:

```bash
ruff check .                      # lint incl. N8xx naming
ruff format --check .             # formatting
.venv/bin/mypy src                # strict mypy
.venv/bin/pyright                 # strict pyright
.venv/bin/vulture src             # dead code
.venv/bin/bandit -r src -c pyproject.toml   # security static analysis
.venv/bin/pytest                  # tests; coverage gate >= 80% enforced
.venv/bin/pip-audit -r requirements.txt -r requirements-dev.txt
mkdocs build --strict             # docs build (diagrams must render)
```

Secrets (must not add new findings; the committed baseline is placeholder-only):

```bash
detect-secrets-hook --baseline .secrets.baseline $(git ls-files)
```

If a gate is missing from the repo tooling (some are not configured yet in
this planning phase), say so explicitly rather than skipping it silently -
and record the gap in the PR.

## 2. Alignment with docs (every feature/change)

- Check the change against `docs/SPEC.md`, `docs/ARCHITECTURE.md`, and the
  ED-xx registry in SPEC §9 before writing code.
- Load `.agents/skills/coding-rules/alignment-checker/SKILL.md` and
  `verify-alignment/SKILL.md` before merge (mandatory gates, SPEC §20).
- **NEVER edit source-of-truth docs** (`ARCHITECTURE.md`, `SPEC.md`,
  `SYSTEM_DESIGN.md`, `PLANNING.md`, the PRD) unless explicitly told to
  update that exact file.
- Method is unsupervised and per-outlet (no global template, no labels);
  gradual change is legitimate; model-agnostic embedder only.
- The I/O module is importable as **`io_layer`**, not `io` (stdlib `io` is
  always resident in `sys.modules`, so a top-level package named `io` is
  unimportable); `io_layer` is what ARCHITECTURE §4 calls "io".
- The DINOv2 default embedder loads ViT-S/14 weights via `torch.hub` pinned
  to a fixed commit SHA (torchvision 0.29 removed DINOv2); the SHA is part of
  the embedding-cache key.

## 3. Documentation duties (same session as the change, not later)

- [ ] `docs/TASKS.md` - tick completed phase tasks honestly; leave gaps unchecked.
- [ ] `docs/CHANGELOG.md` - add entry under `[Unreleased]` in the same PR.
- [ ] `.env.example` - keep field names mirroring `settings.py` exactly when
      config changes.
- [ ] Diagrams - when a diagram changes, update the `.mmd` source and re-render
      the `.svg` (never edit the SVG by hand): `npx -y @mermaid-js/mermaid-cli -i <f>.mmd -o <f>.svg`.
- [ ] Do not create new docs unless asked.

## 4. Git & CI

```bash
git status --short && git diff --stat        # inspect before staging
# Conventional Commits, one logical change per commit:
#   fix(scoring): ... / chore(types): ... / build(docker): ... / docs: ...
git add <files> && git commit -m "type(scope): subject"
git push origin <branch-being-worked-on>     # only when the user asked

# ALWAYS verify CI is green after pushing:
gh run list -L 3 --json conclusion,status,headSha \
  -t '{{range .}}{{printf "%.7s" .headSha}} | {{.status}} | {{.conclusion}}{{"\n"}}{{end}}'
```

- Work happens on feature branches merged to `dev` via PR; never commit
  directly to `main`.
- Secrets only via `.env` (gitignored); CI uses placeholder credentials.
- `data/dataset/` is gitignored; never `git add data/`.

## 5. Pipeline run commands

```bash
# Reproducible full run (seeded, cached embeddings):
.venv/bin/spd run --dataset data/dataset --output results

# Stage isolation / resume:
.venv/bin/spd embed   --dataset data/dataset
.venv/bin/spd detect  --dataset data/dataset
.venv/bin/spd report  --output results
```

- Verify reproducibility: run twice → identical `results/results.json`;
  run with a warm cache → identical output (ED-6).
- Confirm `suspicion_score` ∈ `[0,1]`, `flagged_images` empty (not omitted)
  for clean outlets, and every outlet present exactly once (SPEC §6.1).
- Every run writes structured JSON logs to `logs/spd.log` (`LOG_DIR`); the
  level is shared with the console (INFO by default, DEBUG with `--verbose`).

## 6. Docker hygiene

- Base images pinned to **exact patch versions** - no moving tags, ever.
- Smoke-test the image before pushing: build, run `spd run` on a tiny fixture,
  confirm it exits 0 and produces valid output.

```bash
docker build -t spd:latest .
docker run --rm spd:latest spd --help
```

## 7. Honesty rules (repeated every session, so written down)

- Report gate failures as failures; record missing tooling/gaps explicitly.
- Mark TASKS.md items complete only with evidence (tests pass, CI green).
- If something is partially done, say exactly which part remains.
- The dataset has no labels - never claim precision/recall from the real
  dataset; only from the synthetic golden set (SPEC §16).
