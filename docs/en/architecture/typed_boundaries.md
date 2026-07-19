# Typed boundaries

## Purpose

Typing protects the boundaries between UI, application, logic, platform, and external data. It should not create a separate abstraction for every object.

## When to use a Protocol

Create a new Protocol only when at least one of these conditions applies:

1. there are several real implementations;
2. the dependency varies at an external boundary or test seam;
3. several modules share the contract;
4. the boundary prevents a whole window, global runtime object, or another overly broad object from crossing layers.

When one feature has one known implementation, use the concrete class or an ordinary `Callable`.

`tests/architecture/test_protocol_budget.py` defines the current reviewed upper budget. Exceeding it requires an architectural decision, not the mechanical addition of another interface.

## Plugin Store

External JSON is converted into validated logic-layer models.

Application composition creates concrete repository sessions, operation state, and fetch, install, and uninstall controllers.

The UI receives only the dependencies it needs and does not construct application controllers itself.

One-off Protocols for single concrete implementations are intentionally avoided.

## Background tasks

`UiTaskRunner` preserves the worker result type and sends completion through the UI dispatcher.

The callable that starts a worker uses a normal function type; a separate Protocol is unnecessary when only one function shape exists.

## Tk boundary

Narrow Protocols remain where code must work with different Tk windows, a scheduler host, or an external UI boundary without receiving the complete window object.

Dynamic Tkinter parameters may use `Any` only at the immediate external boundary.

## Checks

Two independent checks protect the design:

1. `scripts/quality/check_typed_boundaries.py` runs strict mypy checks on selected architectural boundaries.
2. `tests/architecture/test_protocol_budget.py` prevents uncontrolled growth in Protocol classes.

Developers run these checks explicitly as part of the local quality suite.
