# Guardrails

---

1. **Never break working code** - "it is utmost priority that we do not break anything."
2. **Never break the production server** - "I do not want to touch anything or make any fatal changes inside that server now."
3. **Never touch off-limits infrastructure or config** - e.g., a server-level nginx config ("please do not mess with nginx config. keep them as before."). In-repo, container-scoped config changes are fine.
4. **Main branch is sacred** - keep it clean; remove accidental branches; explicit merges only.
5. **Real improvements only** - no hacks, no fake improvements; prove real gains.
6. **No secret leakage ever** - .env gitignored, .env.example placeholders only, mask secrets, secret scans green, verify `git log --all -- .env` is empty.
7. **100% alignment with the source of truth** - never deviate from PRD/SPEC/client requirement; don't go beyond scope.
8. **AI-locked docs untouched** - SPEC, ARCHITECTURE, SYSTEM_DESIGN, PRD unless explicitly instructed; TASK.md is tick-only.
9. **Don't push unless asked** - "'don't push' overrides everything."
10. **Tests and docs are part of done** - coverage gates, lint clean, docs updated in the same change.
11. **Honesty** - report honest gaps, don't tick unverified items, don't declare "perfect" without verification, self-flag mistakes.
12. **Careful with destructive actions** - ask before removing volumes, branches, history, system services; never break your system's package managers (e.g., conda); uninstall packages only when proven safe.
13. **Protect project-specific invariants** - e.g., LLM cost-tracking logic, observability layering (logs vs. tracing), canonical schema/ER alignment, soft deletes. Identify and preserve each project's invariants.
14. **Be extremely careful around production/deploy** - prove safety (nginx -t, docker builds, live checks) before push/merge.
15. **Token/budget discipline** - trial runs on small row limits; log token counts.
16. **Persist instructions** - update MUST_DO_CHECKS.md whenever a new repeated instruction appears; keep AGENTS.md in sync.
