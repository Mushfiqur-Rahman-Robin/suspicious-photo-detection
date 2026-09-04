#!/usr/bin/env python3
"""Generate ``results/evaluation.md`` from the synthetic-golden evaluation.

Runs the configured detector against the deterministic synthetic scenarios
(SPEC §16, TASKS P5.1) and writes the precision/recall/F1 report. This is a
supporting artifact, not part of the ``spd`` CLI contract (SPEC §7).

Usage:
    .venv/bin/python -m scripts.run_evaluation [--output results]
"""

from __future__ import annotations

import argparse
from pathlib import Path

from config.settings import load_settings
from core.exceptions import SpdError
from detection.factory import create_detector
from observability.logging import configure_logging, get_logger
from reporting.evaluation import compose_evaluation_report, run_evaluation


def main() -> None:
    """Run the synthetic evaluation and write ``evaluation.md``."""
    parser = argparse.ArgumentParser(
        description="Generate results/evaluation.md from the synthetic golden set."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output directory (defaults to settings.output_dir).",
    )
    args = parser.parse_args()

    settings = load_settings()
    if args.output is not None:
        settings = settings.model_copy(update={"output_dir": args.output})
    configure_logging(settings.log_level, settings.log_dir)
    logger = get_logger("run_evaluation")

    detector = create_detector(settings)
    metrics = run_evaluation(detector, settings)
    report = compose_evaluation_report(metrics, settings)

    output_dir = settings.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    evaluation_path = output_dir / "evaluation.md"
    evaluation_path.write_text(report, encoding="utf-8")
    for name, entry in metrics.items():
        logger.info(
            "scenario_metrics",
            scenario=name,
            precision=round(entry.precision, 3),
            recall=round(entry.recall, 3),
            f1=round(entry.f1, 3),
        )
    logger.info("evaluation_written", path=str(evaluation_path))


if __name__ == "__main__":
    try:
        main()
    except SpdError as exc:
        get_logger("run_evaluation").error("evaluation_failed", cause=str(exc))
        raise SystemExit(exc.exit_code) from exc
