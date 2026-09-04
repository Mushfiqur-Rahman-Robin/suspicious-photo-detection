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
#   * The batch pipeline runs via the `spd` entrypoint (no long-lived server),
#     so no HEALTHCHECK is defined - there is no process to poll.
#
# Image tag: the image MUST be tagged with the concrete project version (see
# docker-compose.yml `SPD_VERSION`, currently 0.1.0) - never `latest`. The
# version is baked into the OCI label below and must stay in sync with
# `pyproject.toml` `[project].version` (commitizen bumps both).
#
# Dependencies: installed with `uv pip install` (uv pinned to UV_VERSION, the
# same resolver used to compile `requirements.txt` from `pyproject.toml`). The
# container installs the SAME runtime lockfile as local development
# (`requirements.txt` - torch 2.14.0 / torchvision 0.29.0, the PyPI default
# CUDA-enabled wheels) so host and container are guaranteed identical.
# `UV_NO_CACHE=1` keeps the downloaded wheels out of the image layer (they are
# written to a temp dir and cleaned during install); on disk-constrained hosts
# this is what makes the multi-GB CUDA stack fit alongside the runtime stage.
#
# Device: default `auto` tries the GPU FIRST and falls back to CPU (or MPS)
# automatically: a host with the NVIDIA container runtime passes `--gpus all`
# and gets CUDA, while a plain CPU host still runs the identical weights
# (embedding output is bit-identical; only the compute backend differs).
# Trade-off: the CUDA wheels make the image several GB larger than a CPU-only
# build would be.
#
# GPU prerequisite: the PyPI CUDA-13 torch wheels activate only on a driver
# that supports CUDA 13 and a GPU with compute capability >= 7.5 (Turing+).
# Older hosts fall back to CPU automatically; for a smaller image there you
# would build with `torch`/`torchvision` from the PyTorch CPU index instead.
# ---------------------------------------------------------------------------

ARG SPD_VERSION=0.1.0
ARG UV_VERSION=0.6.12

# uv is the same resolver that compiled the lockfiles; pinned, no moving tag.
FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv-binary

FROM python:3.13.2-slim-bookworm AS builder

ARG UV_VERSION

COPY --from=uv-binary /uv /uvx /bin/

ENV UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_COMPILE_BYTECODE=0 \
    UV_NO_CACHE=1

WORKDIR /build

COPY requirements.txt .

RUN uv pip install --prefix=/install -r requirements.txt

COPY pyproject.toml .
COPY src ./src

# Install the project itself (console script `spd` + top-level packages) without
# re-resolving deps: everything is already in the /install prefix.
RUN uv pip install --prefix=/install --no-deps .

# ---------------------------------------------------------------------------
FROM python:3.13.2-slim-bookworm AS runtime

ARG SPD_VERSION=0.1.0

LABEL org.opencontainers.image.title="suspicious-photo-detection" \
      org.opencontainers.image.description="Batch ML pipeline that flags visually inconsistent outlet verification images" \
      org.opencontainers.image.source="https://github.com/Mushfiqur-Rahman-Robin/suspicious-photo-detection" \
      org.opencontainers.image.version="${SPD_VERSION}"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Dedicated non-root user with fixed numeric IDs.
RUN groupadd --gid 10001 appgroup \
    && useradd --uid 10001 --gid appgroup --shell /usr/sbin/nologin --create-home appuser

COPY --from=builder /install /usr/local

WORKDIR /app

# Pre-create the writable directories the pipeline mounts volumes onto, owned by
# the runtime user so bind mounts behave regardless of who owns them on the host
# (see docker-compose.yml for the one-time host prep of bind-mounted dirs).
RUN mkdir -p /app/results /app/cache /app/logs \
    && chown -R appuser:appgroup /app/results /app/cache /app/logs

USER appuser

# `spd` is installed as a console script (pyproject [project.scripts]).
ENTRYPOINT ["spd"]
CMD ["--help"]