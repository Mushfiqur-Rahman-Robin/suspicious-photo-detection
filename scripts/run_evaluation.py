#!/usr/bin/env python3
"""Generate ``results/evaluation.md`` from the synthetic-golden evaluation.

Runs the configured detector against the deterministic synthetic scenarios
(SPEC §16, TASKS P5.1) and writes the precision/recall/F1 report. This is a
supporting artifact, not part of the ``spd`` CLI contract (SPEC §7).

The synthetic scenarios are the project's held-out labeled TEST set (SPEC §16):
the real dataset is unlabeled and the pipeline trains nothing, so no train/test
split of the real photos exists or is needed. Scenarios are deterministic from
``--seed`` (defaults to ``settings.random_seed``); passing a different seed
samples a fresh held-out test set, which is how any future parameter tuning must
be validated - never on the same seed that gates the release.

Usage:
    .venv/bin/python -m scripts.run_evaluation [--output results] [--seed 42]
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
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Seed for the held-out synthetic test set (defaults to "
        "settings.random_seed; a different seed samples a fresh test set).",
    )
    args = parser.parse_args()

    settings = load_settings()
    if args.output is not None:
        settings = settings.model_copy(update={"output_dir": args.output})
    if args.seed is not None:
        settings = settings.model_copy(update={"random_seed": args.seed})
    configure_logging(
        settings.log_level,
        settings.log_dir,
        settings.log_filename,
    )
    logger = get_logger("run_evaluation")

    detector = create_detector(settings)
    metrics = run_evaluation(detector, settings)
    report = compose_evaluation_report(metrics, settings)

    output_dir = settings.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    evaluation_path = output_dir / settings.evaluation_filename
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
