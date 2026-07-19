# Current architecture status

## Current structure

The application uses five primary layers:

```text
src/ui
src/app
src/logic
src/core
src/platform
```

Runtime state is centralized under `src/app/runtime`, and every project uses the single workspace layout described below.

## Dependencies

```text
core      -> core
logic     -> logic, core
platform  -> platform, core
ui        -> ui
app       -> app, ui, logic, core, platform
```

Static cycles and dependency-direction violations are checked automatically.

## Platform, logic, and core boundaries

`src/platform` contains shared and reusable environment adapters. It is not the only place where filesystem, network, or process work can occur.

`src/logic` owns application use cases, including I/O that is intrinsic to those use cases: copying, deleting, archiving, loading, and writing project data.

`src/core` owns low-level algorithms and the system operations tied to them. Direct subprocess use remains in format implementations when separating it would not reduce coupling.

New shared networking, process execution, and persistent storage should generally be exposed through platform adapters. Specific I/O stays beside its use case or algorithm when an extra adapter would add ceremony without creating a reusable boundary.

## Project workspace

There is one supported layout:

```text
Projects/<name>/input
Projects/<name>/unpack
Projects/<name>/output
```

`ProjectManager` creates this layout under the workspace configured by `settings.path`. No setting selects an alternative layout.

## UI and application

UI modules import only UI modules and do not construct domain requests.

The application layer wires dependencies through composition, constructs requests, starts use cases, and publishes results back to the UI.

Project Workspace and Plugin Manager receive explicit host objects. Application state is not stored in arbitrary attributes on Tk windows.

## Logic

Logic contains the real unpack, pack, import, conversion, plugin, and tool behavior.

Broad exception handling is limited to reviewed third-party plugin boundaries and transactional cleanup that re-raises the original failure. Architecture tests derive and enforce this boundary from the current source tree.

## Typed boundaries

Protocols remain only where a dependency has multiple implementations, is shared by several modules, varies at an external boundary, or protects UI from receiving an overly broad runtime object.

`tests/architecture/test_protocol_budget.py` defines the reviewed upper budget. The live test result, rather than a number copied into documentation, is the source of truth.

## Documentation

Current English documentation lives in `docs/en`; current Russian documentation lives in `docs/ru`. Material under `docs/archive` is outside the active documentation set and does not define current behavior.

## Build and checks

The release workflow builds the user artifact. Developers run Pytest, Architecture Guard, Ruff, Mypy, and the manual validation suites described in [Tests and scripts](../development/tests_and_scripts.md).

Development sources, tests, scripts, documentation, and workflow files are not included in the end-user release archive.

## Maintenance rule

Future work should target real images, bundled executables, round trips, and reproduced functional defects. When production behavior changes intentionally, tests and documentation are updated to match it; production code is not changed merely to satisfy an obsolete expectation.
