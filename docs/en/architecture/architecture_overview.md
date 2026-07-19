# MIO Kitchen architecture

This document describes the architecture implemented by the current codebase.

## Layers

The project has five primary layers.

1. `src/ui` contains windows, widgets, and presentation state.
2. `src/app` connects user actions to concrete use cases.
3. `src/logic` contains application rules, operation sequences, and use-case-specific I/O.
4. `src/core` contains low-level algorithms, format handling, and system operations that are inseparable from those algorithms.
5. `src/platform` contains reusable environment adapters for settings, languages, Git, the desktop shell, networking, processes, and persistent storage when those concerns form an independent boundary.

Architecture tests enforce the static dependency direction.

```text
core      -> core
logic     -> logic, core
platform  -> platform, core
ui        -> ui
app       -> app, ui, logic, core, platform
```

## UI

`src/ui` owns display and input.

UI code may create windows, widgets, presentation state, localization keys, and callbacks that are supplied by the application layer.

It must not read project files, launch external processes, construct domain requests, or import `src/app`, `src/logic`, `src/core`, or `src/platform`.

## Application

`src/app` owns composition and coordination.

The application layer accepts data from the UI, constructs requests, selects a use case, starts background work, manages window state, and returns results to the UI.

It does not implement image extraction, filesystem processing, or binary algorithms. Direct I/O is limited to small application boundaries where it belongs to the lifecycle of a process, window, or runtime object.

## Logic

`src/logic` contains the application's concrete use cases.

This layer selects operations, validates preconditions, routes files, controls step order, interprets external tool results, and performs work on projects, plugins, and images.

Logic may use `os`, `pathlib`, `shutil`, `zipfile`, `requests`, and other I/O libraries when that work is part of a specific use case. Merely importing `pathlib` or reading an image structure is not an architectural violation.

For new code, volatile boundaries such as networking, external process execution, and persistent storage should move to `platform` when they are reused, vary independently from the use case, or have an independent lifecycle.

Logic never depends on concrete Tk windows and never receives the complete UI state.

The project workspace has one fixed layout.

```text
Projects/<name>/input
Projects/<name>/unpack
Projects/<name>/output
```

`input` keeps source archives and images.

`unpack` keeps extracted partitions and editable working files.

`output` keeps completed build results.

Only this project layout is accepted by the current managers and workflows.

## Core

`src/core` contains low-level Android format, sparse image, boot image, GPT, archive, filesystem, and binary-structure algorithms.

Some low-level modules launch external processes themselves. Current examples include `process_runner.py`, `image2chunks.py`, `blockimgdiff.py`, and `Magisk.py`. Those calls stay with the format algorithm when moving them would not create a genuinely reusable boundary.

New user-facing flows belong in `logic` and `app`. A shared process mechanism belongs in `platform` when several features need it or when it has to vary independently from the algorithm.

## Platform

`src/platform` contains shared adapters for the outside world.

Examples include:

1. settings storage;
2. language-file discovery;
3. JSON repositories;
4. Git operations;
5. application restart;
6. desktop-shell integration;
7. logging setup;
8. reusable filesystem and process adapters.

Platform is not a catch-all ports-and-adapters layer and does not own every I/O operation in the project. An operation stays in `logic` or `core` when it is inseparable from one use case or algorithm and has no value as a shared adapter.

Responsibility is determined by purpose, not by the library being imported. Shared networking, process execution, and persistent storage belong in `platform`; work on one particular archive, image, or use-case workspace may remain in `logic` or `core`.

## Windows and focus

Child windows use `src/ui/common/windowing.py`.

Its `Toplevel` class resolves the owner and establishes transient ownership while the child is still withdrawn. The class applies the current appearance, performs a bounded first paint, moves the window to its final position, and only then reveals it and gives it focus. On Windows, alpha gating, off-screen staging, and DWM cloaking prevent an unthemed first frame from reaching the desktop compositor without pinning the window above unrelated applications.

Hidden utility windows are not forced into view. Native file dialogs receive the active MIO Kitchen window through their `parent` parameter.

## Runtime data

The following directories live beside the application:

```text
bin/
config/
languages/
plugins/
temp/
templates/
logs/
Projects/
```

`config` contains editable settings.

`languages` contains JSON translations discovered at runtime.

`plugins` contains the local store database and installed plugins.

`temp` contains transient data only.

`templates` contains OTA and other runtime templates.

`bin` contains executable tools and their related resources.

## Protocols

Use a `Protocol` only at a genuine boundary.

It is justified when there are several implementations, when an external dependency varies independently, when several modules share one contract, or when the contract prevents a whole window or global state object from leaking across a boundary.

Use the concrete type when a feature has one known implementation.

An architecture test caps the total number of protocol classes so typing does not grow into a second infrastructure layer.

## Exception handling

Logic code catches concrete exception types.

A broad `except Exception` is allowed only at an explicit third-party plugin boundary or during transactional cleanup that re-raises the original error. An AST test enforces this rule.

In `app`, a broad catch is acceptable at boundaries for arbitrary callbacks, background workers, Tk events, and external extensions where the application has to keep the UI responsive.

## Stability

The layer model is stable. Future architectural changes should be local and tied to a concrete feature or a reproduced defect. The overall layer structure should not be redesigned without a practical requirement.
