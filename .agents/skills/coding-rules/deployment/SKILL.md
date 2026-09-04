---
name: deployment
description: Universal deployment skill. Covers environment configuration, pre-deploy checks, deployment steps, validation, and rollback for any backend application.
license: MIT
---

# Skill: Deployment

## Purpose
Deploy software in a controlled, repeatable, and safe way. A deployment is not complete when the service starts - it is complete when the service is verified to be healthy and the team can confidently say what is running in production and why.

---

## Core Principles

**Nothing reaches production without passing tests.** All automated tests, linting, and static analysis must pass before a deployment proceeds. Manual deployments that bypass CI are only acceptable in verified emergency scenarios and must be documented.

**Secrets never appear in source code.** All configuration, credentials, and API keys come from environment variables or a secrets manager. If a secret is ever committed, treat it as compromised immediately - rotation is required, not optional.

**Every deployment is reversible.** Before deploying, know exactly how to roll back. Deployments that cannot be cleanly reversed are a risk that must be addressed before they reach production.

**Staging precedes production.** Changes must be validated in a staging environment that mirrors production before they are deployed to production. Skipping staging is a risk, not a shortcut.

---

## Environment Configuration

- All configuration is externalized to environment variables or a secrets manager
- A documented list of all required environment variables is maintained (names and descriptions, never values)
- Application startup validates required configuration and fails fast with a clear error if variables are missing
- Separate configuration is used for development, staging, and production - never share production secrets with lower environments
- `.env` files and secrets are never committed to version control

---

## Pre-Deploy Checklist

### Code Quality
- All unit tests pass
- All integration tests pass
- Coverage meets the project threshold
- Linting passes with no errors
- Type checking passes with no errors
- No security analysis findings above the accepted severity threshold

### Database
- Any database migrations required for this release are tested in staging before production
- Migrations are reversible where possible, or a documented fallback exists
- Any data transformations or backfills do not block application startup

### Environment
- All required environment variables are set in the target environment
- Any new secrets have been provisioned and tested
- External service dependencies (databases, queues, third-party APIs) are accessible from the target environment

### Review
- The change has been through code review
- Security-relevant changes have been reviewed by a second developer

---

## Deployment Steps

The specific steps depend on the stack, but every deployment should follow this structure:

1. Pull or build the verified artifact from the CI pipeline - never deploy directly from a local machine
2. Apply any database migrations (before starting the new application version)
3. Start or update the application service
4. Run health and smoke checks to verify the deployment
5. Monitor logs and metrics for errors in the minutes immediately following deployment

---

## Post-Deploy Validation

After every deployment, verify:
- The health endpoint returns a successful response
- Key application flows return expected responses (smoke tests)
- Application logs show no errors related to the deployment
- No secrets or sensitive data appear in logs (check for known key names such as `api_key`, `token`, `password`)
- Metrics (error rate, response time, memory) are within normal ranges

---

## Rollback

Know the rollback procedure before deploying, not after something goes wrong.

A rollback typically involves:
1. Redeploying the previous known-good artifact
2. Rolling back database migrations if they were applied (only if the migration is reversible)
3. Verifying the service is healthy on the rolled-back version
4. Documenting what failed and why, for post-incident review

Migrations that cannot be safely rolled back require a forward-fix approach: deploy a corrective migration rather than reverting.

---

## CI/CD Gates

Before auto-deploying to any environment:
- All tests pass
- All static analysis passes
- No secrets detected in the codebase (use a secret scanning tool)
- The artifact is tagged and traceable back to a specific commit

Manual approval is required before deploying to production. Auto-deploy to staging is acceptable when all CI gates pass.

---

## Secrets Policy

- Never log the value of any secret, credential, or API key
- Never commit `.env` files or hardcoded secrets to version control
- Rotate any secret immediately upon suspected or confirmed exposure
- Use short-lived credentials and token expiry where the infrastructure supports it
- Document which team members have access to production secrets
