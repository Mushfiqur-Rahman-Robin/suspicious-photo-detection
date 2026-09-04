"""Detector factory (Factory pattern, SPEC §19, ED-9).

The detection rule is swappable via config; only the ``ensemble`` detector is
shipped in v1, but the seam exists so alternate rules (e.g. LOF) can be added
as new adapters without touching the pipeline.
"""

from __future__ import annotations

from config.settings import Settings
from core.exceptions import ConfigurationError
from core.ports import OutlierDetector

from .ensemble_detector import EnsembleDetector

SUPPORTED_DETECTOR_NAMES = frozenset({"ensemble"})


def create_detector(
    settings: Settings,
    detector_name: str | None = None,
) -> OutlierDetector:
    """Instantiate the configured outlier-detection strategy."""
    name = detector_name if detector_name is not None else "ensemble"
    if name == "ensemble":
        return EnsembleDetector(settings)
    raise ConfigurationError(
        f"unknown detector: {name}; supported: {sorted(SUPPORTED_DETECTOR_NAMES)}"
    )
