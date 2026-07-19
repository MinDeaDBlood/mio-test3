# Runtime state contract

## Source of truth

Runtime state lives under `src/app/runtime` only.

Application code does not define parallel runtime facades outside this package.

## Runtime session

`src/app/runtime/session.py` creates one `RuntimeSession` per process.

The session:

1. registers early values;
2. prepares the platform environment;
3. constructs mandatory core services;
4. registers the core runtime phase;
5. validates all required phase keys.

## Typed phases

`src/app/runtime/phases.py` stores four independent dataclass models:

1. `EarlyRuntimeDefaults`;
2. `RuntimeBootstrapServices`;
3. `BootstrapWindowRuntime`;
4. `BootstrapUiRuntime`.

There is no secondary generic key/value store.

Requiring a phase that has not been registered raises `MissingRuntimeValueError`.

## Registration

The official registration functions are:

1. `register_early_runtime_defaults`;
2. `register_core_runtime_services`;
3. `register_bootstrap_window_runtime`;
4. `register_bootstrap_ui_runtime`.

The `sync_registered_*` functions perform partial updates.

## Reading runtime values

Application code uses `require_registered_*` for mandatory values.

It uses `get_registered_*` only when a missing phase is a valid lifecycle state.

New code does not retrieve runtime values by string keys.

## Context modules

`src/app/runtime/contexts` contains narrow application resolvers:

1. `paths.py`;
2. `tooling.py`;
3. `projects.py`;
4. `project_ui.py`;
5. `plugins.py`;
6. `settings.py`;
7. `ui.py`;
8. `project_defaults.py`;
9. `contracts.py`.

`src/app/runtime/contexts/__init__.py` does not re-export runtime values. Each resolver is imported from its concrete module; there is no broad common resolver.

## Access rules

1. Core does not import runtime state.
2. Logic does not import runtime state.
3. UI does not import runtime state.
4. Runtime resolvers are used only inside `app`.
5. The composition root supplies ready dependencies to UI objects and controllers.
6. Logic receives data, models, and explicit operation ports only.
7. A mandatory dependency is never replaced with a silent default.
8. Runtime field names are exact; alias lookup is not supported.

## Window runtime

`BootstrapWindowRuntime` contains:

1. `main_window`;
2. `animation`;
3. `ui_scheduler`;
4. `current_project_name`;
5. `theme`;
6. `language`.

`main_window` is the canonical name for the root window and runtime accessors require that exact field.

## UI runtime

`BootstrapUiRuntime` contains the main UI surfaces created after main-window composition:

1. `unpack_view`;
2. `project_menu`.

## Automated enforcement

Architecture Guard verifies that:

1. runtime state remains under `src/app/runtime`;
2. runtime facades are not defined outside the runtime package;
3. core, logic, and UI do not import runtime state;
4. runtime modules do not form static cycles with the rest of the project.
