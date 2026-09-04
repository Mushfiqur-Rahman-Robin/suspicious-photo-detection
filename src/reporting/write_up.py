"""One-page write-up generation (SPEC §16, FR9).

A deterministic markdown report grounded in the measured run summary: it
states the method, the outlier rule, the measured KPIs, the trade-offs, the
scalability analysis, and the known limitations. The prose is self-contained
and professional (no internal decision/Spec cross-references leak into the
submitted deliverable) and always reflects the actual measured numbers.
"""

from __future__ import annotations

from pathlib import Path

from core.exceptions import WriteError
from observability.logging import get_logger
from reporting.summary import RunSummary

WRITE_UP_FILENAME = "write_up.md"


def compose_write_up(
    summary: RunSummary,
    max_chars: int,
) -> str:
    """Compose the one-page write-up markdown, capped at ``max_chars``."""
    flagged_rate = (
        summary.total_flagged_images / summary.total_images
        if summary.total_images > 0
        else 0.0
    )
    lines = [
        "# Suspicious Photo Detection - Method Write-up",
        "",
        "## Method",
        f"- **Embeddings:** {summary.model} ({summary.embedding_dim}-dim), "
        "L2-normalized; cosine similarity is computed as a dot product on the "
        "normalized vectors. The embedder is model-agnostic (DINOv2 is the "
        "default; CLIP is an optional alternative selected by config).",
        "- **Scoring:** per-outlet fusion of three complementary signals - "
        "distance to a robust (coordinate-wise median) prototype of the "
        "outlet's embeddings, mean similarity to the k nearest neighbours "
        "(local-density consensus), and a seeded Isolation Forest anomaly "
        "score. The three are weighted equally by default, with the Isolation "
        "Forest contribution down-weighted for small outlets where its scores "
        "are unreliable.",
        "- **Outlier rule:** an adaptive per-outlet threshold "
        "`max(median + k*MAD, score_floor)`; an image is flagged when its "
        "fused score exceeds it, and a deterministic human-readable reason is "
        "chosen from the signal(s) that dominated the flag.",
        "",
        "## Measured run",
        f"- Outlets: {summary.total_outlets}; images: {summary.total_images}; "
        f"flagged images: {summary.total_flagged_images} "
        f"({flagged_rate:.2%} of images; {summary.outlets_with_flags} outlets had flags).",
        f"- Embedding throughput: {summary.embeddings_per_second:.1f} images/sec "
        f"({summary.cache_hits} cache hits / {summary.cache_misses} misses); "
        f"device: {summary.device}; seed: {summary.random_seed}.",
        f"- Stage wall-clock (sec): {format_timings(summary)}.",
        "",
        "## Rationale & trade-offs",
        "- No single signal catches every fake: centroid distance is confused "
        "by multi-cluster outlets, kNN can miss a tight clique of fakes, and "
        "Isolation Forest is unstable at low N - fusing three complementary "
        "signals raises precision without any labels.",
        "- A global threshold is wrong because outlet appearance variance "
        "differs wildly; the robust median + MAD threshold is distribution-free "
        "and needs no per-outlet tuning, and the absolute floor prevents "
        "noise-level flagging in near-uniform outlets.",
        "- The trade-off is precision vs recall at the margin: conservative "
        "flagging minimizes false positives at the cost of missing subtle "
        "one-off changes, which is the right bias for triage.",
        "",
        "## Scalability",
        "- Linear in image count; embeddings are computed once and cached by "
        "content hash, so re-runs and incremental updates are near-free. "
        "Pairwise work is bounded O(N^2) per outlet with N <= ~40 here.",
        "",
        "## Limitations",
        "- A one-off, sharp appearance change (e.g. a full remodel in a single "
        "photo) is statistically indistinguishable from a fake and may be "
        "flagged.",
        "- Multi-cluster robustness relies on local density; a sparsely "
        "populated legitimate second cluster can still be flagged.",
        "- Isolation Forest requires a minimum image count; very small outlets "
        "rely on centroid + kNN only.",
        "- The real dataset has no labels; precision/recall are measured on the "
        "synthetic golden set (`evaluation.md`), not on the real photos.",
        "",
    ]
    write_up = "\n".join(lines)
    if len(write_up) > max_chars:
        write_up = write_up[:max_chars]
        newline_at = write_up.rfind("\n")
        if newline_at != -1:
            write_up = write_up[:newline_at]
    return write_up


def write_write_up(write_up: str, output_dir: Path) -> Path:
    """Write the write-up to ``output_dir/write_up.md`` and return its path."""
    path = output_dir / WRITE_UP_FILENAME
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        path.write_text(write_up, encoding="utf-8")
    except OSError as exc:
        raise WriteError(f"unable to write write-up to {path}: {exc}") from exc
    get_logger("write_up").info(
        "write_up_written", path=str(path), characters=len(write_up)
    )
    return path


def format_timings(summary: RunSummary) -> str:
    """Render the stage timings as a compact, ordered string."""
    if not summary.stage_timings:
        return "n/a (cached report)"
    return ", ".join(
        f"{name}={seconds:.2f}" for name, seconds in summary.stage_timings.items()
    )
