---
name: prompt-writer
description: Universal skill for authoring LLM prompt templates in AI-integrated systems. Covers safety, grounding, versioning, output schema, and injection defense.
license: MIT
---

# Skill: Prompt Writer

## Purpose
Author prompt templates that are safe, predictable, and auditable. A poorly designed prompt introduces hallucination risk, injection vulnerabilities, and output that cannot be validated. A well-designed prompt behaves like a deterministic function: given consistent inputs, it produces consistent, schema-conforming outputs.

---

## Core Principles

**Prompts are code.** They must be versioned, reviewed, tested, and maintained like any other part of the codebase. An unversioned prompt is a silent breaking change waiting to happen.

**Grounding is not optional.** Every prompt that uses system data must explicitly instruct the LLM to base its output only on the provided context. It must not allow the LLM to draw on general world knowledge to fill gaps in the data.

**Output must be structured.** Free-text responses from an LLM are not reliably parseable. Prompts must specify a JSON output schema. The caller validates the response against that schema before using it.

**Prompts do not make decisions.** A prompt may ask the LLM to summarize, explain, or categorize - it must never ask the LLM to decide, recommend mandatory actions, or take a prescriptive position. Those boundaries must be defined in the system prompt.

**Minimize context.** Include only the data the LLM needs for the specific task. Large context windows increase cost, latency, and hallucination surface area. Exclude raw records; include aggregated or pre-processed signals.

---

## Prompt Structure

Every prompt consists of two parts:

**System prompt** - defines the LLM's role, behavioral constraints, output language, and output schema. This is fixed per template. It must include:
- A clear role definition (what the LLM is acting as)
- A grounding instruction: base output strictly on provided data
- A no-new-facts instruction: do not introduce information not present in the context
- The output language directive (injected from configuration, e.g. tenant language)
- The expected JSON output schema with field names and descriptions

**User prompt** - provides the specific context for this call. It uses parameterized slots filled at runtime. It must include only the data needed for the task, with values clearly labeled as data (not instructions).

---

## Versioning

- Every prompt file has a version identifier (e.g., `PROMPT_VERSION = "1.2.0"`)
- The version in use at call time must be stored in any audit log or output record
- Increment patch version for wording changes with no behavioral change
- Increment minor version when new slots or output fields are added
- Increment major version when the schema or grounding rules change significantly
- Never modify a prompt and leave the version unchanged

---

## Output Schema Design

Define a clear, minimal JSON schema for every prompt's expected output. Rules:
- Fields should be flat and simple - avoid deeply nested structures
- Every field must have a clear purpose - remove fields that callers don't use
- Include a field that references at least one piece of provided input (for traceability)
- Include a label field if the output represents an advisory or informational classification
- The schema must be documented in the system prompt so the LLM is guided to comply

---

## Validation and Fallback

The caller is responsible for validating LLM responses against the expected schema. The Prompt Writer's job is to make the schema explicit and clear in the prompt. Design expectations:
- If the response is missing required fields → treat as invalid
- If a field value is outside acceptable bounds → treat as invalid
- Invalid responses must trigger a defined fallback - never propagate unvalidated LLM output
- The fallback behavior must be documented and tested

---

## Injection Defense

Prompt injection occurs when data embedded in the prompt is interpreted as instructions by the LLM. Mitigations:
- Separate data from instructions through structure and labeling (e.g., wrap data in clearly delimited sections)
- Avoid including raw user-provided free text in prompts without explicit sanitization and labeling
- Include an instruction in the system prompt to ignore any instructions found within the data sections
- Treat any LLM response that contradicts the system prompt's constraints as invalid

---

## What to Avoid

- Prompts that ask the LLM to "do its best" or "use your judgment" - this produces inconsistent output
- Prompts that embed large volumes of raw data - summarize or aggregate before including
- Prompts without a defined output schema - unparseable responses are a production risk
- Unversioned prompts - a changed prompt without a version change is an invisible breaking change
- Instructions in the prompt that conflict with each other - the LLM will behave unpredictably
- Asking the LLM to make decisions that should belong to the application layer
