---
name: type-safety
description: Universal skill for enforcing strict runtime type safety and data validation. Covers boundary enforcement, avoiding primitive obsession, parsing instead of validating, and using robust validation libraries such as Pydantic for Python or Zod for TypeScript. Applicable to any strongly or gradually typed codebase.
license: MIT
---

# Skill: Type Safety and Data Validation

## Purpose

Type hints and static analysis are only half the battle. They protect you from yourself during development, but they do not protect your application from external data at runtime. Unvalidated data entering a system leads to defensive checks scattered throughout the codebase, unpredictable crashes, and security vulnerabilities. This skill mandates that all data crossing a system boundary must be strictly parsed and validated into a known, strongly typed structure before it reaches any domain logic.

---

## Core Principles

### Parse, Do Not Validate

Do not write code that checks if a payload is valid and then passes the raw dictionary or untyped object deeper into the system. Instead, write code that consumes raw data and returns a strictly typed, immutable data structure, or fails immediately. Once the data is inside the domain layer, no function should ever need to check if a field is missing, if a string is empty, or if an integer is out of bounds - the type itself guarantees validity.

### Enforce Strict Boundaries

Runtime type enforcement must happen at the edges of the system. The primary boundaries are incoming HTTP requests, configuration files, environment variables, message queue payloads, and responses from third-party APIs. Data crossing these boundaries must be instantiated into a typed schema immediately. If the data is invalid, the system must reject it at the boundary with a clear error, rather than crashing midway through a business process.

### Avoid Primitive Obsession

Do not use primitive types such as plain strings, integers, or dictionaries to represent domain concepts that have constraints. If a string represents an email address, it should be parsed into a dedicated email type or validated field that guarantees its format. If an integer represents a quantity that cannot be negative, it should be parsed into a type that enforces that constraint upon instantiation.

---

## Tooling and Implementation

Rely on robust data validation libraries rather than writing custom validation logic. In Python, use Pydantic. In TypeScript, use Zod, Runtypes, or class-validator. In Go, use struct tags and a validation package. These libraries handle type coercion, deep validation, and comprehensive error reporting far better than bespoke if-statements.

When using these libraries, enable their strictest settings. Forbid extra fields that are not defined in the schema to prevent silent data leakage or parameter injection. Do not allow implicit type coercion that silently changes data meaning, such as converting the string "false" to the boolean True.

---

## Usage Rules

**Never Trust External Data:** All data coming from the client, from the database (if the schema lacks strict constraints), or from an external API is untrusted. It must be parsed into a schema before any domain logic touches it.

**Type Hints Are Not Enough:** In gradually typed languages like Python or TypeScript, type annotations are stripped at runtime. A function annotated to receive an integer will happily accept a string at runtime if the caller is untyped or bypasses the static checker. You must use runtime validation libraries at the boundaries to enforce the types dynamically.

**Fail Fast and Clearly:** When validation fails, the error should be caught at the framework boundary and translated into a standard error response (such as an HTTP 422 Unprocessable Entity or a 400 Bad Request). The error must clearly indicate which fields failed validation and why, without leaking internal implementation details.

**Use Enums for Bounded Sets:** Whenever a field must be one of a specific set of values - such as a status, a role, or a category - use an enumeration type. Never use raw strings or magic numbers scattered throughout the code. The validation layer must reject any value not present in the enumeration.

**Centralise Validation Logic:** If a specific field, such as a confirmation code or a phone number, has complex validation rules, encapsulate those rules within the schema definition or a custom type. Do not duplicate the regex or length checks in multiple request handlers.

---

## Review Checklist

- [ ] All incoming HTTP request bodies and query parameters are parsed into strict schema objects.
- [ ] Responses from external APIs are parsed into typed structures before use.
- [ ] The application configuration and environment variables are strictly validated at startup.
- [ ] Schemas forbid extra, undefined fields to prevent parameter injection.
- [ ] Primitive types are not used where constrained domain types (e.g., email, UUID, positive integer) are appropriate.
- [ ] Magic strings and numbers are replaced with explicit enumeration types.
- [ ] Validation logic is encapsulated within the schema, not scattered across request handlers.
- [ ] Validation failures result in clear, structured errors at the system boundary.
