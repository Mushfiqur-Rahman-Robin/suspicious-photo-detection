---
name: api-design
description: Universal skill for designing clean, consistent, and maintainable HTTP APIs. Covers RESTful conventions, request/response standards, versioning, and error formats.
license: MIT
---

# Skill: API Design

## Purpose
A well-designed API is predictable, consistent, and easy to evolve. A poorly designed API becomes a maintenance burden that constrains every system built on top of it. Follow these principles for every new endpoint.

---

## RESTful Resource Design

- Use **nouns for resources**, not verbs: `/invoices` not `/getInvoices`
- Use **plural nouns** for collections: `/signals`, `/insights`, `/users`
- Use **hierarchical paths** for nested resources: `/tenants/{id}/insights`
- Use **query parameters** for filtering, sorting, and pagination - not path segments
- Resource identifiers in paths use the resource's natural key (UUID or slug): `/invoices/{invoice_id}`

**HTTP Methods:**
| Method | Use |
|---|---|
| `GET` | Retrieve a resource or collection - must be safe and idempotent |
| `POST` | Create a new resource or trigger an action |
| `PUT` | Replace a resource entirely (full update) |
| `PATCH` | Partially update a resource |
| `DELETE` | Remove a resource |

Never use `GET` for operations that mutate state.

---

## URL Conventions

- Lowercase letters and hyphens only: `/anomaly-definitions` not `/anomalyDefinitions`
- No trailing slashes
- Keep path depth reasonable - more than 3-4 levels is a design smell
- Version the API in the path: `/api/v1/...`
- Action endpoints (non-CRUD operations) use a verb after the resource: `/invoices/{id}/approve`

---

## Request Design

- Accept `application/json` by default
- Document all required and optional parameters
- Validate all inputs server-side - never trust client-provided data
- For large collections, support pagination with consistent parameters (e.g., `page`, `page_size` or `cursor`-based)
- Idempotency: `PUT` and `DELETE` must be idempotent; `POST` should support an idempotency key for actions where duplicate execution is harmful

---

## Response Design

**Consistent envelope for success responses:**
```
{
  "data": <resource or array>,
  "meta": {
    "request_id": "...",
    "timestamp": "...",
    "pagination": { ... }   // if applicable
  }
}
```

**Consistent envelope for error responses:**
```
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Human-readable description safe for the consumer to read",
    "details": [ ... ]      // optional, field-level validation errors
  }
}
```

Rules:
- `data` is always the same type for a given endpoint - never sometimes an object, sometimes an array
- `error.code` is a machine-readable constant (uppercase, underscored) - never changes between versions
- `error.message` is safe for consumers but does not expose internal details (no stack traces, SQL errors, or file paths)
- Timestamps are always UTC ISO 8601: `2026-07-03T16:00:00Z`
- IDs are always strings (even if stored as integers) - safer for large IDs and future migrations

---

## HTTP Status Codes

Use status codes semantically and consistently.

| Code | Use |
|---|---|
| `200 OK` | Successful GET, PUT, PATCH |
| `201 Created` | Successful POST that created a resource |
| `204 No Content` | Successful DELETE or action with no response body |
| `400 Bad Request` | Client sent malformed or invalid input |
| `401 Unauthorized` | Authentication required or token invalid |
| `403 Forbidden` | Authenticated but not authorized for this action |
| `404 Not Found` | Resource does not exist (use consistently - do not return 403 when 404 is correct) |
| `409 Conflict` | Request conflicts with existing state (e.g., duplicate creation) |
| `422 Unprocessable Entity` | Input is well-formed but semantically invalid |
| `429 Too Many Requests` | Rate limit exceeded |
| `500 Internal Server Error` | Unexpected server error - never return details in the response body |

Never return `200` with an error body. Never return `500` for a client error.

---

## API Versioning

- Version the API from the start: `/api/v1/`
- Introduce a new version only for breaking changes
- Non-breaking additions (new optional fields, new endpoints) do not require a new version
- Maintain the previous version for a defined deprecation period before removing it
- Communicate deprecations clearly: use a `Deprecation` response header and document the sunset date

**Breaking changes include:**
- Removing a field from a response
- Changing the type or format of an existing field
- Changing an endpoint's URL or method
- Removing an endpoint
- Making a previously optional field required

---

## Documentation Requirements

Every endpoint must have:
- A clear one-line summary
- Description of what it does and any important behavioral notes
- Request parameters (path, query, and body) with types and constraints
- Response schema for the success case
- All possible error response codes with their meaning in this context
- Any authentication or authorization requirements

---

## Common Mistakes

- Using `GET` for operations that change state - breaks caching, proxies, and client expectations
- Returning different shapes from the same endpoint based on a query parameter
- Using `500` for all errors rather than the appropriate 4xx code
- Exposing database IDs, table names, or query strings in responses or error messages
- Inconsistent field naming across endpoints (mixing `camelCase` and `snake_case`)
- Not validating input before processing - trusting that clients will send expected values
- Adding breaking changes to an existing API version without bumping the version number
