---
name: security-auditer
description: Universal security audit skill. Applicable to any backend, API, or AI-integrated system. Covers input validation, authentication, data isolation, secrets management, and safe error handling.
license: MIT
---

# Skill: Security Auditor

## Purpose
Identify security vulnerabilities before they reach production. Security reviews are not optional for production systems - they are a required step before any release. Address critical and high-severity findings unconditionally before merging.

---

## Threat Categories

| Category | Examples |
|---|---|
| **Injection** | SQL injection, prompt injection, command injection, LDAP injection |
| **Broken access control** | Missing auth checks, IDOR, privilege escalation, horizontal data leakage |
| **Data exposure** | Secrets in logs, PII in responses, stack traces to consumers, credentials in version control |
| **Insecure configuration** | Debug mode in production, permissive CORS, weak secrets, no rate limiting |
| **Insufficient logging** | Missing audit trails, silent error swallowing, no traceability |
| **Unsafe dependencies** | Outdated packages with known CVEs, transitive vulnerabilities |
| **AI-specific risks** | Prompt injection via user data, LLM output trusted without validation, AI mutating system state |

---

## Audit Checklist

### Input Validation
- All inputs (HTTP params, headers, body fields, file uploads) are validated and sanitized before use
- Values are validated against expected types, formats, and allowed ranges
- Free-text or user-controlled strings are never directly embedded in queries, commands, or prompts without explicit sanitization
- File uploads are validated for type, size, and content - not just extension

### Authentication & Authorization
- All protected endpoints require authentication
- Authorization is enforced server-side for every request - not just once at login
- Role and permission checks cannot be bypassed by manipulating client-supplied data
- Tokens are validated for expiry, signature, and scope on every use

### Data Isolation
- Users or tenants can only access data they are authorized to see
- Data access functions are scoped to the appropriate owner or tenant
- There is no shared mutable state that could leak data between requests or users

### Secrets Management
- No secrets, API keys, credentials, or sensitive configuration appear in source code or version control
- Secrets are loaded from environment variables or a secrets manager
- Secrets are never logged, even at debug level
- Rotation procedures exist for all secrets

### Error Handling
- Internal error details (stack traces, database messages, file paths, service names) never reach API consumers
- Error responses use safe, generic messages with structured error codes
- Exceptions are caught intentionally - nothing is swallowed silently

### Audit Logging
- Security-relevant events are logged: authentication attempts, authorization failures, data access, configuration changes
- Logs contain enough context to reconstruct what happened and who did it
- Audit logs are protected from tampering - append-only where possible

### AI-Specific (if applicable)
- External AI/LLM services cannot access the database or modify system state
- LLM output is treated as untrusted input - validated against an expected schema before use
- User-controlled data included in prompts is clearly separated from instructions
- AI calls are logged with enough context for audit and cost tracking

### Dependency Security
- Dependencies are kept up to date and scanned for known vulnerabilities
- No dependency with a critical or high CVE is present in production
- Transitive dependencies are included in the security scan

### Configuration
- Production systems do not run with debug mode enabled
- CORS policies are as restrictive as the application allows
- Rate limiting is in place for public or authenticated endpoints where abuse is a risk
- TLS is enforced for all external communication

---

## Audit Procedure

1. Walk through the changed code using the checklist above
2. Check dependency manifests for known vulnerabilities
3. Verify that new endpoints have authentication and authorization
4. Confirm that no secrets appear in code, logs, or responses
5. Confirm error responses are safe for consumers to read

---

## Verdict

- ✅ **Pass** - no critical or high findings
- 🟡 **Conditional pass** - medium or low findings noted and tracked; no blocking concerns
- 🔴 **Fail** - one or more critical or high findings; must resolve before any deployment
