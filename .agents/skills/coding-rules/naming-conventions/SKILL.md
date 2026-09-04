---
name: naming-conventions
description: Universal skill for consistent, unambiguous naming across Python modules, classes, functions, variables, constants, database fields, and test identifiers. Applies to any Python project or service.
license: MIT
---

# Skill: Naming Conventions

## Purpose

Consistent naming eliminates cognitive load. A developer reading any file for the first time must be able to infer the purpose, scope, and type of any identifier without consulting additional documentation. These rules apply to every file, in every layer, of any project that adopts this skill.

---

## General Principles

Be descriptive rather than abbreviated. Write out the full word unless the abbreviation is universally accepted across the industry (examples of accepted abbreviations: `url`, `id`, `api`, `db`, `ttl`, `i18n`, `jwt`, `io`, `cli`). Be consistent: if one module method is called `get_user`, the analogous method in a sibling module must also be `get_user`, not `fetch_user` or `retrieve_user`. Avoid noise words such as `get_data`, `do_thing`, and `handle_stuff` - name the *what*, not the *how*. Use one canonical term for each concept across the entire codebase; never use `session` and `conversation` interchangeably for the same entity. Encode intent, not implementation: a name should say what something *is* or *does*, not *how* it does it internally.

---

## Python Naming Rules

| Construct | Convention | Example |
|---|---|---|
| Module / file | `snake_case` | `user_service.py`, `auth_middleware.py` |
| Package / directory | `snake_case` | `application/services/`, `infrastructure/adapters/` |
| Class | `PascalCase` | `UserProfile`, `PaymentGateway`, `EmailSender` |
| Exception | `PascalCase` ending in `Error` | `AuthenticationError`, `RateLimitExceededError` |
| Abstract base class / port | `PascalCase` noun | `Repository`, `NotificationPort`, `CacheBackend` |
| Function / method | `snake_case` verb phrase | `send_email()`, `validate_token()`, `compute_checksum()` |
| Async function / method | `snake_case` - no `async_` prefix | `fetch_user()` not `async_fetch_user()` |
| Variable | `snake_case` noun phrase | `retry_count`, `access_token`, `expiry_timestamp` |
| Boolean variable | `snake_case` with `is_`, `has_`, `can_`, or `should_` prefix | `is_active`, `has_permission`, `can_retry` |
| Module-level constant | `UPPER_SNAKE_CASE` | `MAX_RETRY_ATTEMPTS`, `DEFAULT_TIMEOUT_SECONDS` |
| Enum class | `PascalCase` | `OrderStatus`, `LogLevel`, `HttpMethod` |
| Enum member | `UPPER_SNAKE_CASE` | `OrderStatus.PENDING`, `LogLevel.DEBUG` |
| Type alias | `PascalCase` | `UserId`, `JsonPayload`, `PermissionMatrix` |
| Private helper (internal use only) | Single leading underscore | `_build_headers()`, `_parse_response()` |
| Name-mangled attribute (use sparingly) | Double leading underscore | Only inside classes where attribute name clash is a real risk |
| Pydantic / dataclass model | `PascalCase` noun or noun phrase | `CreateUserRequest`, `InvoicePayload`, `UserProfile` |
| Pydantic / dataclass field | `snake_case` | `created_at`, `user_id`, `retry_count` |
| Test file | mirrors the module under test with a `test_` prefix | `test_user_service.py` mirrors `user_service.py` |
| Test function | describes the behaviour and condition | `test_login_fails_when_password_is_wrong` |
| Test fixture | descriptive noun with no `get_` prefix | `db_session`, `authenticated_client`, `sample_order` |

---

## Naming by Layer

### Domain and Business Logic

Entities and value objects carry domain language names that reflect the business problem rather than technical implementation. Avoid generic technical suffixes such as `Object`, `Model`, and `Bean`. Domain events are always named in past tense to signal that they describe something that already occurred. Port interfaces - the abstract boundaries in hexagonal architecture - use a plain noun or a `<Concept>Port` naming pattern that describes the capability, not the technology behind it.

### Infrastructure and Adapters

Concrete implementations of port interfaces are named after the technology they wrap combined with the concept they implement. For example, a Redis implementation of a `Cache` port is named `RedisCache`, and a SendGrid implementation of a notification port is named `SendgridEmailNotifier`. The technology name comes first, making it easy to identify the dependency by reading the class name.

### API and HTTP Layer

Route handler function names use the same `snake_case` verb-noun pattern as all other functions. Request and response Pydantic models follow the pattern `<Action><Resource>Request` and `<Action><Resource>Response`. URL path segments use `kebab-case` with plural nouns, following REST conventions.

### Database

Table names use `snake_case` plural nouns. Column names use `snake_case`. Index names follow a predictable pattern: `ix_<table>_<column>` for single-column indexes and `ix_<table>_<col1>_<col2>` for composite indexes. Unique constraints use the prefix `uq_`. Migration files use a sequential number followed by a short description of the change, making the migration history readable in a directory listing.

### Configuration and Environment Variables

All application-specific environment variables share a common prefix that identifies the project or service (for example, `MYAPP_` or `SERVICE_`). Variable names are all-caps with underscores, grouped by logical section using a shared infix (for example, `MYAPP_DB_HOST`, `MYAPP_DB_PORT`, and `MYAPP_DB_NAME` for database-related settings).

---

## Anti-Patterns - Never Do

**Single-letter variables** are forbidden outside short comprehension iterator variables such as `i`, `k`, or `v` in a `for` loop body. The letters `l` (lowercase L), `O` (uppercase O), and `I` (uppercase I) must never be used as standalone identifiers because they are visually ambiguous in most fonts and editors.

**Redundant type suffixes** add noise without information. Write `users` not `user_list`, `config` not `config_dict`, `error` not `error_str`.

**Vague class names** without a qualifying noun - such as `Manager`, `Helper`, `Processor`, `Handler`, `Utils`, and `Misc` - tell the reader nothing about what the class actually does. Add a domain noun: `QueueJobProcessor` is acceptable; `Processor` alone is not.

**camelCase is forbidden in Python source files.** It is only acceptable inside JSON payloads that must mirror an external API's naming conventions.

**Hungarian notation** - prefixing variable names with their type such as `strName`, `intCount`, or `bIsValid` - must not be used. Python's type annotation system serves this purpose.

**Abbreviations that discard context** are forbidden. Write the full word: `user` not `usr`, `message` not `msg`, `configuration` not `cfg`.

**Double negatives in boolean names** are forbidden. Flip to the positive form: use `is_active` instead of `is_not_inactive`, and `has_error` instead of `no_error`.

---

## Consistency Enforcement

Maintain a project glossary in the repository documentation. When a new concept is introduced, add it to the glossary before writing code that names it. Use linting rules that catch naming convention violations (for example, `ruff`'s `N8xx` rules for Python) as part of CI. During code review, flag any identifier that requires a comment to explain - the name itself should be self-documenting. If a reviewer needs to ask "what does this mean?", the name must be improved before the PR is merged.

---

## Review Checklist

- [ ] All new identifiers follow the correct case convention for their construct type.
- [ ] No abbreviations used that are not on the project's approved list.
- [ ] Analogous constructs across different modules use consistent names.
- [ ] No noise words (`data`, `info`, `stuff`, `object`, `thing`) in any identifier.
- [ ] Boolean variables use `is_`, `has_`, `can_`, or `should_` prefix.
- [ ] Test functions describe the behaviour under test, not the implementation detail.
- [ ] No `camelCase` in Python source files.
- [ ] No single-letter variables outside comprehension loops.
- [ ] Domain event names are in past tense.
- [ ] Enum members are in `UPPER_SNAKE_CASE`.
- [ ] No double negatives in boolean names.
