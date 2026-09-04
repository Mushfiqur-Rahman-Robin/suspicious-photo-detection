---
name: config-management
description: Universal skill for centralizing all application configuration. Defines the boundary between sensitive secrets (API keys, database passwords, ports - managed via .env) and non-sensitive, repeated tunables (managed via a committed config.yml or settings.py). Prohibits hardcoded magic numbers and strings in feature code. Applicable to any service.
license: MIT
---

# Skill: Configuration Management

## Purpose

A hardcoded value scattered across a codebase is a hidden assumption. When that assumption changes - a timeout value, a service URL, a pagination limit, or a feature threshold - developers must hunt through source files rather than editing one authoritative place. Furthermore, hardcoding sensitive credentials is an immediate security vulnerability. This skill mandates that all configuration is centralized, drawing a strict line between static application tunables and environment-specific secrets.

---

## The Golden Rule

There are absolutely no hardcoded variables, magic numbers, or raw configuration strings allowed in feature code, business logic, or infrastructure adapters.

Every application must have a single source of truth for configuration - typically a central `config.yml` or a `settings.py` module. This central configuration merges two distinct streams of data: non-sensitive application variables that are committed to version control, and sensitive credentials that are strictly loaded from environment variables or `.env` files.

---

## Secret vs Non-Secret Classification

Understanding the distinction between secrets and non-secret tunables dictates how a value is stored and managed.

**Sensitive Secrets** include API keys, database passwords, database hostnames, port numbers, JWT signing secrets, OAuth client secrets, encryption keys, and observability write tokens. These values change depending on the deployment environment (local, staging, production) and their exposure would constitute a security breach. Secrets must be stored in a `.env` file (which is strictly excluded from version control) or managed by a secure secrets manager in production. They must never be committed to the repository.

**Non-Secret Tunables** include timeout durations, default pagination sizes, rate limit thresholds, retry counts, maximum payload sizes, standard application URLs, and default system prompts. Because these values are often repeated across the application and generally remain consistent across environments, they must be centralized in a configuration file such as `config.yml` or a `settings.py` class that is committed to version control. This provides a single, trackable place for developers to tweak the application's behaviour without modifying business logic.

---

## The Central Configuration Pattern

The application must establish a single authoritative configuration module or object. This object acts as the bridge between the codebase and the external configuration files.

When the application starts, the configuration module should parse the committed non-sensitive tunables from the `config.yml` or `settings.py` file, and then overlay or inject the sensitive secrets loaded from the environment variables or `.env` file.

All feature code, database adapters, and API routers must import and read from this central configuration object. No code outside of the central settings module is permitted to read environment variables directly or parse the configuration file on its own. This guarantees that if a variable changes, or if validation logic is added to a configuration field, it only needs to be updated in one place.

---

## Secret Handling and Type Safety

When the central configuration module loads a sensitive secret from the environment, it should use an opaque string type or a designated secret wrapper provided by the language or framework (for example, a secret string type in Pydantic). This ensures that if the configuration object is accidentally logged, printed, or returned in an API response, the actual secret value is masked or redacted. The raw value of the secret must only be extracted at the exact point of execution where it is strictly required, such as when constructing a database connection pool or an HTTP client authorization header.

---

## Managing Environment Variables

For the sensitive secrets that cannot be committed, maintain two separate files.

The `.env` file holds the actual configuration values for the local environment. It must be listed in the repository's ignore file and must never be staged or committed.

The `.env.example` file is a template committed to version control. It contains every environment variable name that the application expects, with a placeholder value and a descriptive comment. Every secret required by the application must have a corresponding entry in the `.env.example` file. The comment should explain the purpose of the variable and note whether it is strictly required to run the application in production. When a new developer clones the repository, copying the example file and filling in the placeholders must be sufficient to run the application locally.

---

## Adding a New Configuration Value

When introducing a new variable that is used repeatedly across the application (like a default cache expiration time), add it to the committed `config.yml` or `settings.py` file with a sensible default value. Update the central configuration object to parse and expose this new field.

When introducing a new sensitive credential or environment-specific variable (like a new third-party API key), add the field to the central configuration object to read from the environment. Then, add the variable name to the `.env.example` file with a descriptive comment, and update your local `.env` file with the actual value. Update any deployment runbooks or infrastructure scripts to provision the new secret in staging and production environments.

---

## Anti-Patterns - Never Do

Hardcoding a numeric literal as a timeout, row limit, or threshold directly inside an API router or service class is strictly forbidden.

Hardcoding a URL string, hostname, or file path directly in feature code is forbidden.

Reading an environment variable directly using the language's native environment access functions (such as reading the operating system environment array) inside business logic is a bypass of the configuration system and is forbidden.

Declaring a field that holds a sensitive secret as a plain string type, allowing it to be easily printed or logged in plain text, is a security vulnerability.

---

## Review Checklist

- [ ] No numeric literals are used as timeouts, limits, or thresholds in feature code - all are managed centrally.
- [ ] No hardcoded URLs, hostnames, file paths, or service identifiers appear in feature code.
- [ ] All non-sensitive tunables are centralized in a committed `config.yml` or `settings.py` file.
- [ ] All sensitive secrets and ports are sourced exclusively from the environment or a `.env` file.
- [ ] The `.env` file is listed in the version control ignore list and is never committed.
- [ ] Every sensitive environment variable is documented with a placeholder in `.env.example`.
- [ ] No direct environment variable reads occur outside the central configuration module.
- [ ] Secrets are loaded into opaque wrapper types to prevent accidental logging or exposure.
