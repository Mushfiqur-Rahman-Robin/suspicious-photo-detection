"""`spd` CLI - the batch pipeline entry point (SPEC §7, FR10).

Four subcommands mirror the stage isolation: ``run`` (full pipeline),
``embed`` (cache embeddings only), ``detect`` (score + detect from cache),
``report`` (regenerate outputs from cached results). Exit codes follow the
SPEC §7 contract: 0 success, 2 invalid usage/config, 1 runtime failure.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, NoReturn

import typer

from config.settings import Settings, load_settings
from core.exceptions import SpdError
from pipeline.runner import PipelineRunner

app = typer.Typer(
    name="spd",
    help="Suspicious Photo Detection - batch pipeline that flags visually "
    "inconsistent outlet verification images.",
    add_completion=False,
    no_args_is_help=True,
)


def _build_settings(
    config: Path | None,
    model: str | None,
    device: str | None,
    seed: int | None,
    verbose: bool,
    **overrides: object,
) -> Settings:
    """Merge CLI flags into validated Settings (config > env > defaults).

    Invalid usage/config exits with code 2 (SPEC §7) rather than surfacing as
    a generic runtime failure.
    """
    cli_overrides: dict[str, object] = {}
    if model is not None:
        cli_overrides["embedding_model"] = model
    if device is not None:
        cli_overrides["device"] = device
    if seed is not None:
        cli_overrides["random_seed"] = seed
    if verbose:
        cli_overrides["log_level"] = "DEBUG"
    cli_overrides.update(overrides)
    try:
        return load_settings(config, **cli_overrides)
    except SpdError as exc:
        _exit_with_error(exc)


def _run_pipeline(settings: Settings, command: str) -> None:
    """Execute a runner command, translating domain errors to exit codes."""
    try:
        runner = PipelineRunner(settings)
        if command == "run":
            runner.run_full()
        elif command == "embed":
            runner.run_embed()
        elif command == "detect":
            runner.run_detect()
        elif command == "report":
            runner.run_report()
    except SpdError as exc:
        _exit_with_error(exc)


def _exit_with_error(exc: SpdError) -> NoReturn:
    """Print a structured, single-line error and exit with the mapped code."""
    typer.echo(f"error: {exc}", err=True)
    raise typer.Exit(code=exc.exit_code)


def _base_overrides(
    dataset: Path | None,
    output: Path | None,
) -> dict[str, object]:
    """Collect the dataset/output directory overrides shared by subcommands."""
    overrides: dict[str, object] = {}
    if dataset is not None:
        overrides["dataset_dir"] = dataset
    if output is not None:
        overrides["output_dir"] = output
    return overrides


@app.command()
def run(
    dataset: Annotated[
        Path | None,
        typer.Option(
            "--dataset", "-d", help="Dataset root with one folder per outlet."
        ),
    ] = None,
    output: Annotated[
        Path | None,
        typer.Option(
            "--output", "-o", help="Directory for results.json, results.csv, write-up."
        ),
    ] = None,
    config: Annotated[
        Path | None,
        typer.Option(
            "--config", "-c", help="Optional JSON config file overlaying settings."
        ),
    ] = None,
    model: Annotated[
        str | None,
        typer.Option(
            "--model", help="Embedding model: dino_v2_small (default) | clip."
        ),
    ] = None,
    device: Annotated[
        str | None, typer.Option("--device", help="Device: auto | cpu | cuda | mps.")
    ] = None,
    seed: Annotated[
        int | None, typer.Option("--seed", help="Random seed for reproducibility.")
    ] = None,
    verbose: Annotated[
        bool, typer.Option("--verbose", help="Enable DEBUG logging.")
    ] = False,
) -> None:
    """Run the full pipeline: load -> embed -> score -> detect -> report."""
    settings = _build_settings(
        config,
        model,
        device,
        seed,
        verbose,
        **_base_overrides(dataset, output),
    )
    _run_pipeline(settings, "run")


@app.command()
def embed(
    dataset: Annotated[
        Path | None,
        typer.Option(
            "--dataset", "-d", help="Dataset root with one folder per outlet."
        ),
    ] = None,
    config: Annotated[
        Path | None,
        typer.Option(
            "--config", "-c", help="Optional JSON config file overlaying settings."
        ),
    ] = None,
    model: Annotated[
        str | None,
        typer.Option(
            "--model", help="Embedding model: dino_v2_small (default) | clip."
        ),
    ] = None,
    device: Annotated[
        str | None, typer.Option("--device", help="Device: auto | cpu | cuda | mps.")
    ] = None,
    seed: Annotated[
        int | None, typer.Option("--seed", help="Random seed for reproducibility.")
    ] = None,
    verbose: Annotated[
        bool, typer.Option("--verbose", help="Enable DEBUG logging.")
    ] = False,
) -> None:
    """Extract and cache embeddings only (resumable; re-runs are free)."""
    settings = _build_settings(
        config,
        model,
        device,
        seed,
        verbose,
        **_base_overrides(dataset, None),
    )
    _run_pipeline(settings, "embed")


@app.command()
def detect(
    dataset: Annotated[
        Path | None,
        typer.Option(
            "--dataset", "-d", help="Dataset root with one folder per outlet."
        ),
    ] = None,
    output: Annotated[
        Path | None,
        typer.Option(
            "--output", "-o", help="Directory for results.json, results.csv, write-up."
        ),
    ] = None,
    config: Annotated[
        Path | None,
        typer.Option(
            "--config", "-c", help="Optional JSON config file overlaying settings."
        ),
    ] = None,
    model: Annotated[
        str | None,
        typer.Option(
            "--model", help="Embedding model: dino_v2_small (default) | clip."
        ),
    ] = None,
    device: Annotated[
        str | None, typer.Option("--device", help="Device: auto | cpu | cuda | mps.")
    ] = None,
    seed: Annotated[
        int | None, typer.Option("--seed", help="Random seed for reproducibility.")
    ] = None,
    verbose: Annotated[
        bool, typer.Option("--verbose", help="Enable DEBUG logging.")
    ] = False,
) -> None:
    """Score + detect from cached embeddings only (cache misses error out)."""
    settings = _build_settings(
        config,
        model,
        device,
        seed,
        verbose,
        **_base_overrides(dataset, output),
    )
    _run_pipeline(settings, "detect")


@app.command()
def report(
    output: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="Directory holding cached results.json."),
    ] = None,
    config: Annotated[
        Path | None,
        typer.Option(
            "--config", "-c", help="Optional JSON config file overlaying settings."
        ),
    ] = None,
    model: Annotated[
        str | None,
        typer.Option(
            "--model", help="Embedding model: dino_v2_small (default) | clip."
        ),
    ] = None,
    device: Annotated[
        str | None, typer.Option("--device", help="Device: auto | cpu | cuda | mps.")
    ] = None,
    seed: Annotated[
        int | None, typer.Option("--seed", help="Random seed for reproducibility.")
    ] = None,
    verbose: Annotated[
        bool, typer.Option("--verbose", help="Enable DEBUG logging.")
    ] = False,
) -> None:
    """Regenerate results.csv + write-up from cached results.json."""
    settings = _build_settings(
        config,
        model,
        device,
        seed,
        verbose,
        **_base_overrides(None, output),
    )
    _run_pipeline(settings, "report")


if __name__ == "__main__":
    app()
