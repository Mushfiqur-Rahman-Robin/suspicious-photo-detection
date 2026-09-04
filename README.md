# Suspicious Photo Detection (SPD)

**Suspicious Photo Detection in Outlet Verification Images.**

A batch ML pipeline that, given an outlet's accumulated photo history (one
folder per outlet, no timestamps), flags the images that are visually
inconsistent with that outlet's overall appearance - so thousands of
field-agent verification photos can be triaged without a human looking at most
of them.

## Status

Planning/design phase. This repository currently contains specifications and
standards only - no pipeline code yet.

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
src/                   pipeline source (flat layout, planned)
tests/                 unit + integration tests (planned)
.agents/skills/        loadable engineering skills (coding rules)
```

## Documentation

Read these in order:

1. `project_docs/AI_Engineer_Assignment_Suspicious_Photo_Detection_PRD.pdf` - product PRD (source of truth)
2. `docs/SPEC.md` - what we build
3. `docs/ARCHITECTURE.md` - how it fits together
4. `docs/SYSTEM_DESIGN.md` - entities + pipeline + sequence diagrams
5. `docs/PLANNING.md` - delivery plan
6. `docs/ENGINEERING_DECISIONS.md` - decision log + best practices
7. `docs/CHANGELOG.md` - change history

The same documents are published as an mkdocs site (`mkdocs.yml`, content under `docs/`).

## Roadmap

- [x] Planning/design phase - specs, architecture, delivery plan, diagrams
- [ ] Embedding layer (model-agnostic: DINOv2 default, CLIP alternate) + cache
- [ ] Scoring (cosine + centroid + kNN) and detection (ensemble + adaptive threshold)
- [ ] Pipeline + CLI (`spd`) + JSON/CSV output + write-up

## Disclaimer

This is an unsupervised anomaly-detection pipeline, not a human review system.
Outlets are compared to themselves; gradual change is legitimate and only images
that stand apart from the outlet's own distribution are flagged.
