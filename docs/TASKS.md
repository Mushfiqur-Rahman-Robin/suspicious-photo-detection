# TASKS - Suspicious Photo Detection (SPD) - v1

**Traceable task decomposition of `docs/PLANNING.md` §4.** Every task cites its
SPEC §/ED-xx contract and its test plan. Status ticks are the only permitted
edits to this file (tick-only, see `docs/MUST_DO_CHECKS.md` §0).

> Legend: **G** = phase gate · **S** = SPEC section · **E** = Engineering Decision.

---

## Phase 0 - Foundations

^- [x] **P0.1** Repo scaffold: flat `src/` layout under `{config, core, embedding, scoring, detection, pipeline, io, reporting, cli, observability}` (ARCH §4). _S: §5, §20 · E: ED-8_
^- [x] **P0.2** `settings.py` (Pydantic Settings) + `.env`/`.env.example`; config catalog from SPEC §22. _S: §18 · E: ED-8_
^- [x] **P0.3** `pyproject.toml` metadata + dependency groups (test/lint/types/security/docs/dev). _S: §20_
^- [x] **P0.4** CI pipeline (lint/type-check/test/dead-code/security/docs) + pre-commit + Dockerfile + docker-compose. _S: §20 · PLANNING §4_
^- [x] **P0.5** CLI skeleton `spd` (run/embed/detect/report) with `--help` and exit codes. _S: §7, §5.10 · E: ED-8_
^- [x] **P0.6** `docs/` finalized: SPEC, ARCHITECTURE, SYSTEM_DESIGN, PLANNING, TASKS, ENGINEERING_DECISIONS, MUST_DO_CHECKS, CHANGELOG + rendered diagrams. _S: §0_
- **Test:** config validation (missing/invalid values fail fast); `spd --help` exit 0; mkdocs build clean.

## Phase 1 - Embedding layer (model-agnostic)

^- [x] **P1.1** `core/` entities + output-schema models (`OutletResult`, `FlaggedImage`) with `extra="forbid"` and score bounds. _S: §6, §12 · E: ED-7_
^- [x] **P1.2** `core/ports.py`: `Embedder`, `SimilarityScorer`, `OutlierDetector`, `ResultWriter` + custom exceptions. _S: §5, §20_
^- [x] **P1.3** `io/dataset_loader.py`: discovery (folder=outlet, file=image), deterministic sort, corrupt-image policy. _S: §5.1 · FR1_
^- [x] **P1.4** `io/embedding_cache.py`: content-addressed key `sha256(bytes)+model+version`. _S: §13 · E: ED-6_
^- [x] **P1.5** `embedding/dino_v2_embedder.py` (default) + preprocessing + L2-normalization + batched inference. _S: §10.1 · E: ED-1, ED-2_
^- [x] **P1.6** `embedding/clip_embedder.py` (alternate) + `create_embedder` factory. _S: §10.1 · E: ED-1_
- **Test:** loader order-independence + corrupt handling; cache key/hit/miss/transparency; embedder normalized + right dim + deterministic; factory dispatch.

## Phase 2 - Scoring (similarity + signals)

^- [x] **P2.1** `scoring/similarity.py`: cosine matrix `S` (diagonal excluded). _S: §10.2 · E: ED-2_
^- [x] **P2.2** `scoring/centroid.py`: coordinate-wise median centroid, re-normalized. _S: §10.3 · E: ED-3_
^- [x] **P2.3** `scoring/knn.py`: top-k mean similarity (k = min(5, N−1)). _S: §10.3 · E: ED-10_
^- [x] **P2.4** `scoring/fusion.py`: weighted fusion + clamp to `[0,1]`. _S: §10.4 · E: ED-4_
- **Test:** cosine symmetry/range; centroid robustness vs mean; kNN on synthetic clusters; fusion weights + clamp.

## Phase 3 - Detection (ensemble + threshold + reasons)

^- [x] **P3.1** `detection/isolation_forest.py`: seeded, deterministic per-outlet IF score. _S: §10.3 · E: ED-4, ED-6_
^- [x] **P3.2** `detection/ensemble_detector.py` + `create_detector` factory. _S: §11.1 · E: ED-4, ED-9_
^- [x] **P3.3** `detection/threshold.py`: `max(median + k·MAD, floor)`. _S: §11.1 · E: ED-5_
^- [x] **P3.4** `detection/reasons.py`: deterministic reason templates per dominant signal. _S: §11.4 · FR5_
- **Test:** MAD + floor math; N<2 empty flags; uniform-outlet no-flag; injected-fake flagged with right reason; multi-cluster non-flag; seed determinism.

## Phase 4 - Pipeline + CLI + output

^- [x] **P4.1** `pipeline/stage.py`: Template Method stage lifecycle (timing/logging). _S: §19_
^- [x] **P4.2** `pipeline/runner.py`: orchestrate load→embed→score→detect→assemble. _S: §5, ARCH §6.1_
^- [x] **P4.3** `io/result_writer.py`: JSON + CSV for all outlets (empty flags never omitted). _S: §6.1 · FR6_
^- [x] **P4.4** `cli/app.py`: wire `run|embed|detect|report` + global flags. _S: §7 · FR10_
^- [x] **P4.5** `reporting/summary.py` + `reporting/write_up.py`: run summary + one-page write-up. _S: §14, §16 · FR9_
- **Test:** e2e fixture run (round-trip, ranking completeness, empty-flag outlet present, every outlet once); subcommand independence; schema forbid-extra.

## Phase 5 - Validation, write-up, hardening

^- [x] **P5.1** Synthetic-golden eval: precision/recall/F1 on injected outliers. _S: §16, §21_
^- [x] **P5.2** Determinism + cache-transparency regression tests. _S: §13 · E: ED-6_
^- [x] **P5.3** Full-dataset run + qualitative review of sampled flags. _S: §16_
^- [x] **P5.4** `results/write_up.md` (1-page) + `results/evaluation.md`. _S: §16 · FR9_
^- [x] **P5.5** Dockerfile/docker-compose polish; alignment + verify gates. _S: §20 · PLANNING §8_
- **Test:** two identical full runs; cold vs warm cache identical; container `spd run` smoke.

---

## Notes

- **Traceability:** FR1-FR10 are covered across P1-P5 (FR1=P1.3, FR2=P1.5/1.6, FR3=P2, FR4=P3, FR5=P3.4, FR6=P4.3, FR7=P4.2/4.3, FR8=P1.4/P5.2, FR9=P4.5/P5.4, FR10=P4.4). Confirm against SPEC §24 before release.
- **CLIENT/FRONTEND:** none - this is a batch CLI pipeline (SPEC §2.2, ED-8). There is no UI deliverable in the PRD.
- **Out of scope:** web service, database, model fine-tuning, timestamp/EXIF logic (SPEC §2.2).
