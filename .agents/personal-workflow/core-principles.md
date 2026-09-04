# Core Principles

---

1. **Documents-first, code-second.** SPEC.md / AGENTS.md / TASK.md / SYSTEM_DESIGN.md must be "rock solid" and "100% aligned" BEFORE any code. "let's at first make a purely solid plan. then we will code."
2. **PRD/specs are the source of truth.** Docs that are AI-locked (SPEC, ARCHITECTURE, SYSTEM_DESIGN, PRD) are never touched without explicit instruction; TASK.md contents are tick-only.
3. **Everything must be verified, not assumed.** No hallucination. Verify against actual files, model metadata, reference code, and real terminal output. Flag unresolvable items honestly as blocking gaps.
4. **Real improvements, never fake ones.** Hacky "improvements" that don't survive real use (e.g., pre-rendering content that the framework immediately replaces) are rejected. "I need to actually see real improvements."
5. **Tests and docs are part of "done".** A change isn't finished until tests pass, coverage gates are met, lint is clean, and documentation is updated in the same change.
6. **Test-driven changes.** "we need to make sure that the changes are test driven."
7. **Grill yourself before presenting.** Produce finding lists, close all gaps, then re-verify. Be "harshly self-critical" rather than declaring "perfect".
8. **Honesty > optimism.** Report honest gaps; tick only with evidence; remove deferred items; self-flag mistakes.
9. **Branch and push discipline.** Feature branch → dev → main with proper conventional commits; main branch is sacred; push only when asked.
10. **Don't deviate from scope.** Stay inside the current TASK.md week; don't build ahead; avoid over-engineering.
11. **Security sensitivity.** No secret leakage ever; .env.example placeholders only; mask secrets; secret scans green.
12. **Perfectionism with momentum.** Wants 100% thoroughness but also expects "continue" progress rather than stalls.
13. **Live verification matters.** Beyond unit tests: docker compose up, real pipeline runs on limited data, live curl/ssh checks into production.
14. **Token/budget consciousness.** Trial runs on small row limits before full runs; log token counts per run.
