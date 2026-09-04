# syntax=docker/dockerfile:1

# ---------------------------------------------------------------------------
# Suspicious Photo Detection (SPD) - multi-stage production image.
#
# Best practices applied (dockerfile-optimization skill):
#   * Base pinned to exact patch version (no moving tags).
#   * Multi-stage: build toolchain never reaches the runtime image.
#   * Dependency manifest copied before source for layer-cache hits.
#   * Non-root user with fixed numeric UID/GID.
#   * No secrets or environment-specific config baked into the image.
#   * The batch pipeline runs via the `spd` entrypoint (no long-lived server).
# ---------------------------------------------------------------------------

FROM python:3.13.2-slim-bookworm AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

COPY requirements.txt .

RUN pip install --prefix=/install -r requirements.txt

# ---------------------------------------------------------------------------
FROM python:3.13.2-slim-bookworm AS runtime

LABEL org.opencontainers.image.title="suspicious-photo-detection" \
      org.opencontainers.image.description="Batch ML pipeline that flags visually inconsistent outlet verification images" \
      org.opencontainers.image.source="https://github.com/Mushfiqur-Rahman-Robin/suspicious-photo-detection"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Dedicated non-root user with fixed numeric IDs.
RUN groupadd --gid 10001 appgroup \
    && useradd --uid 10001 --gid appgroup --shell /usr/sbin/nologin --create-home appuser

COPY --from=builder /install /usr/local

WORKDIR /app

COPY src ./src

USER appuser

# `spd` is installed as a console script (pyproject [project.scripts]).
ENTRYPOINT ["spd"]
CMD ["--help"]
