"""Structured logging setup (logging-and-tracing skill).

A single structlog factory configured once at startup; no module configures
its own logging. Logs go to the console (human-readable key-value) and, when a
``log_dir`` is provided, to a structured JSON file under that directory so a
batch run leaves an audit trail on disk. Context fields (``run_id``,
``outlet_id``, ``stage``) are bound via contextvars so every downstream log
line is correlatable without passing the logger around.

The stdlib ``logging`` root logger is the sink: structlog events are routed
through ``structlog.stdlib.ProcessorFormatter``, which also normalizes any
third-party stdlib log records into the same format. Level filtering happens
once at the root logger, so console and file share one level.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, cast

import structlog
from structlog.stdlib import BoundLogger

from config.settings import LogLevel

SHARED_PROCESSORS: list[Any] = [
    structlog.contextvars.merge_contextvars,
    structlog.processors.add_log_level,
    structlog.processors.TimeStamper(fmt="iso", utc=True),
    structlog.processors.StackInfoRenderer(),
    structlog.processors.format_exc_info,
]


def _console_formatter() -> structlog.stdlib.ProcessorFormatter:
    """Build the human-readable console formatter (pre-chain included)."""
    return structlog.stdlib.ProcessorFormatter(
        processor=structlog.dev.ConsoleRenderer(),
        foreign_pre_chain=SHARED_PROCESSORS,
    )


def _json_formatter() -> structlog.stdlib.ProcessorFormatter:
    """Build the machine-readable JSON formatter for the log file."""
    return structlog.stdlib.ProcessorFormatter(
        processor=structlog.processors.JSONRenderer(ensure_ascii=False, sort_keys=True),
        foreign_pre_chain=SHARED_PROCESSORS,
    )


def configure_logging(
    log_level: LogLevel,
    log_dir: Path | None = None,
    log_filename: str = "spd.log",
) -> None:
    """Configure the structlog pipeline for this process.

    The console stream always gets a human-readable rendering; when ``log_dir``
    is given, the same events are also written as JSON lines to
    ``log_dir/<log_filename>`` (the directory is created if missing). The
    filename default matches the settings default; callers centralize the name
    in Settings by passing ``settings.log_filename`` (SPEC §18). The configured
    level applies uniformly to both sinks via the root logger.
    """
    level_number = int(getattr(logging, log_level.value, logging.INFO))

    handlers: list[logging.Handler] = []
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(_console_formatter())
    handlers.append(console_handler)

    if log_dir is not None:
        log_dir.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_dir / log_filename, encoding="utf-8")
        file_handler.setFormatter(_json_formatter())
        handlers.append(file_handler)

    root_logger = logging.getLogger()
    root_logger.setLevel(level_number)
    root_logger.handlers = handlers

    structlog.configure(
        processors=[
            *SHARED_PROCESSORS,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> BoundLogger:
    """Return the process-wide structured logger (logging-and-tracing skill).

    ``structlog.get_logger`` resolves to the stdlib-bound logger installed by
    ``configure_logging``; events are filtered by the root logger level.
    """
    return cast(BoundLogger, structlog.get_logger(name))


def bind_run_context(**fields: object) -> None:
    """Bind context fields (run_id, outlet_id, stage) to the current context.

    Context stays bound until ``clear_run_context`` is called, so per-outlet
    fields must be bound around the outlet's own stage execution.
    """
    structlog.contextvars.bind_contextvars(**fields)


def clear_run_context() -> None:
    """Clear all contextvars bound by ``bind_run_context``."""
    structlog.contextvars.unbind_contextvars()
