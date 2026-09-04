---
name: design-patterns
description: Guidelines for choosing and applying design patterns (factory, builder, iterator, singleton, etc.) following best practices and avoiding over-engineering.
license: MIT
---

# Skill: Design Patterns

## Purpose
Design patterns are proven, reusable solutions to recurring design problems. They give developers a shared vocabulary and reduce the risk of ad-hoc, inconsistent solutions. However, patterns are tools, not goals. This rule defines when to apply common patterns, how to apply them correctly, and - just as importantly - when NOT to use them. The best pattern is often the simplest code that solves the problem without one.

---

## General Principles

- **Patterns solve problems, they do not create them**: Only introduce a pattern when it addresses a concrete, present need. Never add a pattern "just in case" (see YAGNI).
- **Prefer the simplest thing that works**: A plain function, class, or composition is preferable to a pattern when the pattern's complexity outweighs its benefit.
- **Use the pattern's intent, not its exact textbook shape**: Adapt the implementation to the language's idioms (e.g., use callbacks/interfaces instead of rigid class hierarchies where natural).
- **Name things using the pattern vocabulary**: If you use a factory, name it `*Factory` or `create*()`. Consistent naming makes the pattern obvious to readers.
- **Prefer composition over inheritance**: Favor delegation and interfaces over deep class hierarchies when applying structural and behavioral patterns.
- **Patterns must follow the project's existing conventions**: If the codebase already uses a particular pattern for a problem class, stay consistent with it instead of mixing styles.
- **Document why the pattern was chosen**: A short comment or decision note explaining the problem being solved is worth more than the pattern itself.

---

## Comments and Docstrings

Code must be documented in the right places and with the right kind of comment. Well-placed comments and docstrings are part of the deliverable, not an afterthought.

- **Docstring public interfaces.** Every module, public class, public function/method, and complex type MUST have a docstring explaining its purpose, its parameters, and its return value (and exceptions, where meaningful). Follow the language's idiomatic docstring convention (e.g. PEP 257/docstring format for Python, JSDoc/TSDoc for TypeScript, `//` doc comments for Go, etc.).
- **Docstrings say WHAT and WHY, not HOW.** Describe the contract - what the caller can rely on, edge cases, and invariants - not a line-by-line restatement of the body. A docstring that repeats the code adds noise.
- **Use type annotations / signatures as the source of truth for types.** The docstring documents semantics and intent; the type system documents the shapes. Do not duplicate type information in prose unless it clarifies a non-obvious invariant.
- **Comment the WHY, not the WHAT.** Use inline comments for decisions, constraints, gotchas, and non-obvious reasoning: why this branch exists, why this value is used, why we can't do the obvious thing. Do not comment obvious code (`i = i + 1  # increment i` is noise).
- **Document intentional non-obviousness.** If code looks wrong but is correct (a workaround, a performance trick, an order dependency), a comment explaining why it is that way is mandatory - future maintainers will "fix" it otherwise.
- **Keep comments in sync with code.** A stale comment is worse than no comment. When code changes, update the comment in the same change. Never leave a comment that contradicts the code.
- **Do not document the obvious or redundant.** `get_user()` returning a user needs no comment explaining it returns a user. Reserve comments for things a reader cannot trivially infer.
- **Match the project's tone and conventions.** One language, one style, one voice. Docstrings are part of the codebase and follow the same review process as code.
- **Avoid commented-out code.** Delete dead code; version control preserves history. A large block of commented-out code is a maintenance hazard, not documentation.
- **Follow the language-agnostic rule: prefer expressive names over comments.** If a name is so opaque that it needs a comment, rename it (see `.agents/skills/coding-rules/naming-conventions/SKILL.md`) - but keep the docstring and the WHY comments regardless.

---

## Creational Patterns

### Factory Method / Abstract Factory
**Use when:**
- Object creation is complex or involves logic beyond a simple constructor (validation, defaults, wiring dependencies).
- You need to decouple callers from the concrete class they instantiate.
- You want to centralize creation logic so it can be reused or swapped (e.g., pluggable backends, DI containers).

**How to apply:**
- Prefer a simple static/class factory method (`createX`) before introducing a full Abstract Factory.
- Return the most general interface or base type the caller needs, not the concrete class.
- Keep factory code free of business logic; its job is construction only.

**Avoid when:**
- A simple constructor suffices. A factory for a class with no branching or variation is indirection without payoff.

### Builder
**Use when:**
- An object has many optional configuration parameters or a complex multi-step construction process.
- You want to prevent invalid object states during construction (e.g., enforce required fields before building).
- You need to produce several representations of the same construction process (e.g., JSON and XML exports).

**How to apply:**
- Prefer it when fluent construction improves readability; otherwise a constructor with named parameters or an options object may be simpler.
- Provide a `build()`/`toX()` terminal method that validates and returns the fully constructed, immutable object.
- Keep builder methods chainable, single-purpose, and side-effect-free.

**Avoid when:**
- The object has one or two parameters. A constructor is clearer.
- The language supports named/optional arguments or data classes that already solve the problem.

### Singleton
**Use when:**
- There must be exactly one shared instance of a resource that is genuinely global (e.g., a connection pool, a logger, a configuration store).
- The single-instance guarantee is an actual functional requirement, not just a convenience.

**How to apply:**
- Prefer dependency injection of a single instance over a global static accessor; tests can then supply fakes.
- Make initialization lazy and thread-safe if the instance is created on first use.
- Keep the singleton stateless or minimize mutable state; a global mutable singleton is a hidden global variable.

**Avoid when:**
- You want it only to avoid passing an object around. Pass it explicitly instead.
- Testability matters and you cannot inject the instance - this is the classic singleton anti-pattern.
- A stateless module-level function or an injected scoped instance would work.

### Prototype
**Use when:**
- Creating a new object is expensive and you can copy an existing one, or when object shapes vary and cloning is the cleanest way to replicate them.

**How to apply:**
- Prefer language-native cloning (e.g., `clone`, spread/copy semantics) over hand-written copy code.
- Decide and document whether the clone is shallow or deep.

**Avoid when:**
- Construction is cheap; plain construction is clearer than cloning.
- A copy constructor or factory with explicit parameters communicates intent better.

---

## Structural Patterns

### Adapter
**Use when:**
- You need to integrate a third-party or legacy interface that does not match the interface your code expects.

**How to apply:**
- Keep the adapter thin - translate the interface, do not add new behavior or logic inside it.

**Avoid when:**
- You control both sides of the interface; change the target instead of wrapping it.

### Facade
**Use when:**
- You need a simple, unified entry point over a complex subsystem, and callers only need a small slice of its capabilities.

**How to apply:**
- Expose a minimal, intention-revealing API and delegate to the subsystem behind it.

**Avoid when:**
- Callers need the full subsystem anyway; a facade that hides nothing is extra indirection.

### Decorator
**Use when:**
- You need to add behavior to objects dynamically without modifying their class, and combinations of behaviors are possible (logging, caching, retries, auth).

**How to apply:**
- Decorators should implement the same interface as the wrapped object and delegate the original call.
- Prefer plain wrapper functions/higher-order functions where the language idiom is functional.

**Avoid when:**
- A single static behavior can simply be added to the class itself.

### Proxy
**Use when:**
- You need to control access, defer expensive initialization (lazy loading), or mediate access to a remote resource.

**How to apply:**
- Keep the proxy's interface identical to the real subject so callers cannot tell the difference.

**Avoid when:**
- The control you need can be handled inside the real object or at the call site.

---

## Behavioral Patterns

### Iterator
**Use when:**
- You need a uniform way to traverse a collection without exposing its internal representation, especially when the collection is lazy, infinite, or non-standard.

**How to apply:**
- Prefer language-native iteration (generators, `for...of`, `yield`, streams, cursor APIs) over hand-written iterator classes.
- Keep iteration lazy when the sequence is large or potentially infinite.

**Avoid when:**
- A plain `for` loop or a standard library method (`map`, `filter`, `foreach`) already covers the case.

### Observer / Event Emitter
**Use when:**
- One object must notify many dependents of state changes without coupling them together (UI updates, pub/sub, event-driven flows).

**How to apply:**
- Prefer the language's native event/stream facilities where they exist.
- Always provide a way to unsubscribe; leaking listeners is a common memory bug.

**Avoid when:**
- A single callback argument is enough; an event system is overkill for one listener.

### Strategy
**Use when:**
- You have interchangeable algorithms that should be selectable at runtime (e.g., different sort/validation/payment strategies).

**How to apply:**
- Represent each strategy as a small object/function behind a common interface.
- Prefer passing a function directly where a single-method strategy is needed.

**Avoid when:**
- A simple `if/else` with two branches is clearer and unlikely to grow.

### Command
**Use when:**
- You need to encapsulate an action as an object for queuing, undo/redo, logging, or deferred execution.

**How to apply:**
- Prefer passing a function/closure where the language supports first-class functions.

**Avoid when:**
- The action is executed immediately in one place; a plain method call is simpler.

### Template Method
**Use when:**
- Several algorithms share an identical skeleton but differ in specific steps.

**How to apply:**
- Define the skeleton once, allow subclasses/callbacks to override only the varying steps.
- Prefer providing hook functions or strategy callbacks over forcing inheritance.

**Avoid when:**
- The shared skeleton is trivial or the variations are rare.

### State
**Use when:**
- An object's behavior changes based on its internal state, and state transitions are complex enough that `if/else` chains become unmaintainable.

**How to apply:**
- Prefer explicit state-machine libraries or a table of transitions when transitions outnumber behaviors.
- Keep transitions and behaviors in one coherent place.

**Avoid when:**
- A few boolean flags and guard clauses are easier to read than a full state pattern.

---

## When NOT to Use a Pattern

- **Over-engineering (YAGNI)**: The future use case that justifies the pattern may never arrive.
- **Premature abstraction**: The pattern hides the actual flow behind layers before the complexity is real.
- **Pattern theater**: Applying a pattern by name without solving a real problem adds complexity and reduces readability.
- **Inflexible misuse**: Forcing the textbook structure when a simplified, language-idiomatic version would be better.

When in doubt, write the straightforward version first. Extract or introduce the pattern only when a concrete need (duplication, coupling, testability, extensibility) demonstrates itself.

---

## Review Checklist

- [ ] The pattern solves a present, concrete problem - not a speculative one
- [ ] The simplest viable solution was considered before the pattern
- [ ] The implementation follows the language's idioms rather than the textbook shape
- [ ] The pattern's name/terminology is reflected in naming and structure
- [ ] The choice is consistent with existing patterns in the codebase
- [ ] The pattern's downside (indirection, hidden flow) is acceptable for the benefit gained
- [ ] Any non-obvious rationale for the pattern is documented
- [ ] The pattern is testable (e.g., the singleton can be injected/faked)
- [ ] Public interfaces have docstrings (purpose, parameters, return, exceptions) following the language's convention
- [ ] Comments explain WHY and non-obvious behavior, not WHAT the code already shows
- [ ] Intentional non-obvious code (workarounds, order dependencies) is commented
- [ ] No stale or contradicting comments; no commented-out code
