# Suspicious Photo Detection (SPD)

**Suspicious Photo Detection in Outlet Verification Images.**

A batch ML pipeline that, given an outlet's accumulated photo history (one
folder per outlet, no timestamps), flags the images that are visually
inconsistent with that outlet's overall appearance - so thousands of
field-agent verification photos can be triaged without a human looking at most
of them.

Read the core documents in order:

1. [SPEC (what we build)](SPEC.md)
2. [ARCHITECTURE (how it fits together)](ARCHITECTURE.md)
3. [SYSTEM DESIGN (entities + pipeline + sequence diagrams)](SYSTEM_DESIGN.md)
4. [PLANNING (delivery plan)](PLANNING.md)
5. [ENGINEERING DECISIONS (ADR log + best practices)](ENGINEERING_DECISIONS.md)
6. [CHANGELOG (change history)](CHANGELOG.md)

The product source of truth is
`project_docs/Suspicious_Photo_Detection_PRD.pdf`.

> This is an unsupervised anomaly-detection pipeline, not a human review
> system. Outlets are compared to themselves; gradual change is legitimate and
> only images that stand apart from the outlet's own distribution are flagged.
