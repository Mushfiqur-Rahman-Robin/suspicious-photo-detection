"""Central application configuration.

This module is the ONLY place allowed to read environment variables or a
config file (SPEC §18, config-management skill). Non-secret tunables live
here with committed defaults; environment-specific overrides come from
``.env`` (gitignored); an optional JSON config file and explicit CLI flags
may overlay both. Nothing in the feature code may hardcode a tunable.
"""

from __future__ import annotations

import json
import math
from enum import StrEnum
from pathlib import Path

from pydantic import Field, ValidationError, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from core.exceptions import ConfigurationError


class EmbeddingModel(StrEnum):
    """Embedding backends selectable through the model-agnostic port (ED-1)."""

    DINO_V2_SMALL = "dino_v2_small"
    CLIP = "clip"


class SimilarityMetric(StrEnum):
    """Similarity functions accepted by ``SIMILARITY_METRIC`` (SPEC §10.2)."""

    COSINE = "cosine"


class DeviceKind(StrEnum):
    """Compute devices accepted by ``DEVICE`` / ``--device``."""

    AUTO = "auto"
    CPU = "cpu"
    CUDA = "cuda"
    MPS = "mps"


class LogLevel(StrEnum):
    """Valid structured-log levels (logging-and-tracing skill)."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class Settings(BaseSettings):
    """Validated, immutable configuration for the whole pipeline.

    Why a Pydantic settings object: every stage reads tunables from one
    strongly typed source so a typo or out-of-range value fails fast at the
    boundary instead of silently corrupting results (type-safety skill).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="forbid",
        frozen=True,
    )

    # --- App / logging -----------------------------------------------------
    environment: str = "development"
    log_level: LogLevel = LogLevel.INFO

    # --- Model & embedding (SPEC §22.1, ED-1) ------------------------------
    embedding_model: EmbeddingModel = EmbeddingModel.DINO_V2_SMALL
    embedding_dim: int = 384
    device: DeviceKind = DeviceKind.AUTO
    batch_size: int = 32

    # DINOv2 is no longer shipped by torchvision (removed in torchvision 0.29),
    # so the default adapter loads the official weights through torch.hub,
    # pinned to a fixed commit SHA for reproducibility (ED-6). The hub cache
    # makes repeat loads offline; the SHA is part of the embedding-cache key.
    dino_v2_hub_repo: str = "facebookresearch/dinov2"
    dino_v2_hub_ref: str = "7764ea0f912e53c92e82eb78a2a1631e92725fc8"

    # --- Paths (SPEC §22.3) ------------------------------------------------
    dataset_dir: Path = Path("data/dataset")
    output_dir: Path = Path("results")
    cache_dir: Path = Path("cache/embeddings")
    log_dir: Path = Path("logs")

    # --- Reproducibility (ED-6) ---------------------------------------------
    random_seed: int = 42

    # --- Scoring (SPEC §22.2, §10.3) ----------------------------------------
    similarity_metric: SimilarityMetric = SimilarityMetric.COSINE
    k_neighbors: int = 5
    centroid_weight: float = 1.0 / 3.0
    knn_weight: float = 1.0 / 3.0
    isolation_forest_weight: float = 1.0 / 3.0
    min_images_for_isolation_forest: int = 10
    isolation_forest_estimators: int = 100

    # --- Detection (SPEC §22.2, §11.1) --------------------------------------
    mad_k: float = 3.0
    score_floor: float = 0.5
    min_images_per_outlet: int = 2

    # --- Dataset & output (SPEC §22.3) --------------------------------------
    ignore_corrupt_images: bool = False
    score_decimals: int = 4
    write_up_max_chars: int = 6000

    # --- Output artifact file names (SPEC §22.3) ----------------------------
    # The names of every on-disk artifact are declared once here so no feature
    # module hardcodes a filename (SPEC §18 / config-management skill). They are
    # committed non-secret tunables with stable defaults; a run only changes
    # them via an explicit override.
    results_json_filename: str = "results.json"
    results_csv_filename: str = "results.csv"
    run_summary_filename: str = "run_summary.json"
    write_up_filename: str = "write_up.md"
    log_filename: str = "spd.log"
    evaluation_filename: str = "evaluation.md"

    # --- Untrusted-input bounds (SPEC §17) ----------------------------------
    max_image_dimension: int = 8192
    max_image_pixels: int = 50_000_000

    # --- Quality thresholds for the synthetic golden set (SPEC §16) ---------
    golden_min_precision: float = Field(default=0.8, ge=0.0, le=1.0)
    golden_min_recall: float = Field(default=0.8, ge=0.0, le=1.0)
    golden_min_f1: float = Field(default=0.8, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def _validate_tunable_consistency(self) -> Settings:
        """Reject internally inconsistent tunables before they reach a stage."""
        weights = self.centroid_weight + self.knn_weight + self.isolation_forest_weight
        if not math.isclose(weights, 1.0, abs_tol=1e-6):
            raise ValueError("fusion weights must sum to 1.0")
        if self.min_images_per_outlet < 2:
            raise ValueError("min_images_per_outlet must be at least 2")
        if self.min_images_for_isolation_forest < 2:
            raise ValueError("min_images_for_isolation_forest must be at least 2")
        if self.k_neighbors < 1:
            raise ValueError("k_neighbors must be at least 1")
        if self.score_decimals < 0 or self.score_decimals > 10:
            raise ValueError("score_decimals must be between 0 and 10")
        return self

    def fusion_weights(self) -> tuple[float, float, float]:
        """Return the three fusion weights as a (centroid, knn, if) triple."""
        return (
            self.centroid_weight,
            self.knn_weight,
            self.isolation_forest_weight,
        )


def load_settings(config_path: Path | None = None, **overrides: object) -> Settings:
    """Build validated Settings from ``.env`` plus optional JSON config + CLI flags.

    Precedence (lowest to highest): committed defaults, ``.env``, JSON config
    file (``--config``), explicit call-site overrides. ``overrides`` may carry
    any Settings field name; unknown fields fail with a ConfigurationError.
    """
    if config_path is not None:
        if not config_path.is_file():
            raise ConfigurationError(f"config file not found: {config_path}")
        try:
            file_overrides = json.loads(config_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ConfigurationError(
                f"unable to parse config file {config_path}: {exc}"
            ) from exc
        if not isinstance(file_overrides, dict):
            raise ConfigurationError(
                f"config file {config_path} must contain a JSON object"
            )
        merged_overrides: dict[str, object] = {**file_overrides, **overrides}
    else:
        merged_overrides = dict(overrides)

    try:
        return Settings(**merged_overrides)  # type: ignore[arg-type]  # dynamic overrides validated by pydantic
    except ValidationError as exc:
        raise ConfigurationError(f"invalid configuration: {exc}") from exc
