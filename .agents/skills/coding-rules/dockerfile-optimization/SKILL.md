---
name: dockerfile-optimization
description: Universal skill for writing lean, secure, reproducible, and production-ready Dockerfiles. Covers multi-stage builds, layer caching, non-root user hardening, image size reduction, build secrets, health checks, and .dockerignore practices. Applicable to any containerized service.
license: MIT
---

# Skill: Dockerfile Optimization

## Purpose

A poorly written Dockerfile produces images that are large, slow to build, insecure, and non-reproducible. These rules ensure that every Docker image is lean, deterministic, and hardened - regardless of the application language or framework.

---

## Core Principles

Every layer in a Docker image is either reused from cache or rebuilt from scratch. Layers are cached by instruction hash, so order instructions from least-frequently-changing to most-frequently-changing to maximise cache hit rate. Never run application processes as the root user in production - create a dedicated non-root user with a fixed, non-zero UID and GID. Pin base images to an exact tag that includes the patch version, because moving tags such as `python:3.12-slim` can change silently between builds and introduce unexpected differences. Use multi-stage builds to ensure that build tools, compilers, test dependencies, and intermediate artifacts never appear in the final production image. Maintain a comprehensive `.dockerignore` file - copying the entire repository context into the build daemon without filtering sends irrelevant and potentially sensitive files into the image.

---

## Layer Ordering for Cache Efficiency

The most impactful optimisation that requires no architectural change is to order the `COPY` and `RUN` instructions in the Dockerfile from least-frequently-changing to most-frequently-changing. For a typical application service, the correct order is: the base image declaration, then OS-level system package installation, then dependency manifest files and dependency installation, and finally the application source code. This ordering ensures that the dependency installation layer - which is often the slowest step - is only invalidated when the dependency manifest actually changes, not on every source file edit.

The most common mistake is to copy the entire source directory before copying the dependency manifest, which forces the dependency installation to re-run on every commit even when dependencies have not changed. Always copy the dependency manifest file alone before running the dependency installer.

---

## Multi-Stage Build Pattern

Multi-stage builds are the most impactful single technique for reducing final image size and attack surface. The principle is to separate the build environment from the runtime environment. The first stage, typically called `builder`, installs all necessary build tools, compiles native extensions if required, and installs all application dependencies into an isolated prefix directory. The second stage, typically called `runtime`, starts from a clean minimal base image, copies only the installed packages from the builder stage, and copies only the application source code. No build tools, no test dependencies, and no intermediate compilation artifacts make it into the final image.

This approach routinely reduces image size by several hundred megabytes for Python services that require compilation of native extensions, because the compiler toolchain is present only in the builder stage.

---

## Base Image Selection

Choose a minimal, explicitly pinned base image. For Python services, the `slim` variant of a specific Debian release provides a good balance of compatibility and size. Alpine Linux appears smaller but causes significant compatibility issues with Python packages that include native C extensions compiled against glibc, because Alpine uses musl libc. Stick with Debian slim variants unless the project has specifically verified Alpine compatibility for all its dependencies.

Always pin to a full version tag that includes the patch version - for example, `python:3.12.4-slim-bookworm` rather than `python:3.12-slim` or `python:latest`. Moving tags can change silently, producing non-reproducible builds. Schedule a quarterly review of the pinned base image to pick up security patches, and update the pin whenever a CVE affecting the base image is published.

---

## System Package Installation

When installing OS-level packages with a package manager such as `apt`, always combine the package index update and the package installation in the same `RUN` instruction. Separating them into two instructions means that Docker may serve a cached, stale package index from a previous build layer and install outdated packages. Always use the flag that suppresses installation of recommended but non-required packages to avoid adding hundreds of megabytes of transitive suggestions. After installation, remove the package manager's cached index files in the same `RUN` instruction to prevent them from occupying space in the image layer. Only install packages that are genuinely required by the production runtime - build tools and development headers belong only in the builder stage.

---

## Dependency Installation

Use the package manager's flag that disables the local download cache when installing application dependencies, because the download cache serves no purpose inside an image layer and adds size. Do not install development, linting, or test dependencies in the production image - maintain separate dependency manifests for production and development environments. If using a non-standard package manager, pin its own version explicitly rather than installing its latest version, to ensure reproducible builds. Always copy the dependency manifest file before any application source files so that Docker can cache the dependency installation layer independently of source changes.

---

## Secrets at Build Time

Never pass secrets as build arguments (`ARG`) or build-time environment variables (`ENV`). Both are stored permanently in the image manifest and are visible to anyone who runs `docker history` on the image. If build-time secrets are required - for example, a private package registry authentication token - use Docker BuildKit's secret mount mechanism, which provides a temporary in-memory file during the specific `RUN` instruction that needs it and leaves no trace in the final image or its history. Application runtime secrets such as API keys and database passwords must never be baked into the image at all; they are injected at container startup through environment variables, a secrets manager, or mounted secret files provided by the orchestrator.

---

## Non-Root User

Create a dedicated operating system user and group with fixed, non-zero numeric identifiers before the final application stage begins. Use `chown` during the copy instruction to set the correct file ownership in a single layer rather than adding a separate `RUN chown` instruction. Set the active user to the non-root application user as the last instruction before the entry point. Never use the root user for the runtime process unless the application strictly requires it, and document the reason clearly if an exception is made.

---

## Environment Variables

Always set the Python-specific variables that prevent bytecode file accumulation (`PYTHONDONTWRITEBYTECODE`) and ensure that log output is flushed without buffering (`PYTHONUNBUFFERED`). Do not set application configuration variables - database connection strings, API keys, or service URLs - in the Dockerfile itself, because these values differ between environments and must be provided at container startup time by the deployment configuration.

---

## The `.dockerignore` File

A `.dockerignore` file at the repository root is mandatory. Without it, every `COPY . .` instruction sends the entire repository - including version control metadata, virtual environments, test artifacts, documentation, and local secret files - into the build context. At minimum, the file must exclude the version control directory, virtual environment directories, compiled bytecode files and their cache directories, test runner caches, coverage reports, documentation source directories, local environment files containing real secrets, and editor or IDE metadata directories. The environment variable example file should be explicitly excluded from the exclusion rule if it is safe to include (using a negation pattern), since it contains no real secrets and serves as documentation.

---

## Health Checks

Every production image must define a `HEALTHCHECK` instruction. This allows the container orchestrator to distinguish between a container that has started and one that is actually serving traffic correctly. The check interval should be long enough to avoid adding overhead but short enough to detect failures quickly. The timeout must be shorter than the interval so that a single slow check does not block subsequent checks. The start period must be long enough for the application to complete its initialisation before the orchestrator begins evaluating health - services that perform database migrations, load models, or warm caches at startup need a longer start period. The retry count should be set high enough that transient blips do not cause premature container replacement.

---

## Port Documentation

The `EXPOSE` instruction documents the port that the container listens on. It does not publish the port - that is controlled by the orchestrator through the deployment configuration (for example, a `docker-compose.yml` port mapping or a Kubernetes Service definition). Always include `EXPOSE` for documentation purposes even though it has no runtime enforcement effect.

---

## Image Size Reduction - Expected Gains

| Technique | Typical Reduction |
|---|---|
| Multi-stage build removing build toolchain | 200 - 500 MB |
| Suppressing recommended packages in `apt` | 30 - 100 MB |
| Removing package manager cache in the same layer | 30 - 60 MB |
| Disabling pip download cache | 10 - 50 MB |
| Comprehensive `.dockerignore` | 50 - 300 MB, varies by repository |
| Switching from a full base image to a `slim` variant | 400 - 700 MB |

---

## CI and Supply Chain Integrity

Build images from CI only, using the verified source at a specific commit. Never build and push images from a developer's local machine in a team environment, because local environments may differ from CI and may contain local modifications. Tag every image with both a semantic version and the full commit SHA so that any deployed image can be traced back to an exact source revision. Scan every built image for known OS and package vulnerabilities before pushing it to the registry, using a tool appropriate to the project's security posture. For high-assurance deployments, sign images to enable the container orchestrator to verify that only images produced by the trusted CI pipeline are run in production.

---

## Review Checklist

- [ ] Base image pinned to an exact patch version tag - not `latest` or a minor-version alias.
- [ ] Multi-stage build used; build tools absent from the final runtime stage.
- [ ] Non-root user created with a fixed numeric UID and GID; active user set before the entry point.
- [ ] Package index update and package installation combined in one instruction; cache purged in the same instruction.
- [ ] Dependency manifest copied before application source code for layer cache efficiency.
- [ ] Suppressed recommended packages in package manager install; disabled download cache in pip install.
- [ ] No secrets in build arguments, build-time environment variables, or copy instructions.
- [ ] `.dockerignore` excludes version control metadata, virtual environments, test artifacts, and local secret files.
- [ ] `HEALTHCHECK` defined with a correct interval, timeout, start period, and retry count.
- [ ] Python bytecode suppression and unbuffered output variables are set.
- [ ] Application runtime configuration is not baked into the image.
- [ ] Image vulnerability scanning is integrated into CI before the push step.
