# Module boundaries

This document lists the project's canonical boundaries. New code should import the concrete module that owns the responsibility it needs.

## Application startup

### `src/app/entrypoint.py`

This is the one canonical entry point for startup, restart, and runtime-session synchronization.

The root `tool.py` imports startup directly from this module. The UI layer contains no entry point and does not depend on the application layer.

## Main window

### `src/app/composition/main_window.py`

`create_main_window()` creates the main window and supplies its text catalog and Tk DnD path.

`compose_main_window()` assembles the tabs, settings, project workspace, Plugin Manager, and right-hand panel.

The UI class in `src/ui/main_window.py` does not invoke composition by itself.

## Composition

### `src/app/composition`

This is the only place where the application layer constructs concrete UI classes and connects them to controllers, services, runtime state, and localization.

## Windows and dialogs

### `src/ui/common/windowing.py`

Provides the shared `Toplevel` class, window-owner resolution, first-paint staging, and centralized foreground presentation. New application windows must not import `tkinter.Toplevel` directly.

### `src/ui/common/window_appearance.py`

Owns the current theme and transparency for registered root and top-level windows. Appearance changes are applied to every live window through this registry.

### `src/ui/common/window_paint.py`

Performs bounded initial painting. It drains layout and native window events without running unrelated Tk timer or file callbacks.

### `src/ui/common/window_reveal.py`

Reveals a prepared root only after its first native surface has been painted. On Windows it uses an alpha gate and off-screen staging to prevent an unthemed white frame from reaching the compositor.

### `src/ui/startup_splash.py`

Displays the application-managed startup splash after file logging is active, then delegates the final main-window reveal to the shared reveal pipeline.

### `src/app/composition/dialogs.py`

Connects the application layer to warnings, confirmations, and file dialogs. On Windows, file dialogs receive the active owner window.

## Localization

### `src/app/localization_selection.py`

Loads the selected language catalog from the saved setting.

### `src/app/localization_runtime.py`

Holds the application's localization catalog.

### `src/ui/localization.py`

Contains only the `LocalizationCatalog` protocol.

UI code receives the catalog explicitly and does not import the application singleton.

## Settings

### `src/platform/settings_repository.py`

Reads and writes the root `config/settings.ini`. It does not start application behavior or select a language.

### `src/app/settings`

Coordinates setting changes and the application actions they trigger.

## Platform

### `src/platform`

Contains technical adapters for files, JSON, INI, languages, networking, processes, Git, logging, and the desktop shell.

Platform code does not choose user workflows and does not contain image-processing rules.

Configuration and infrastructure adapters use the concrete boundaries listed in this document; no additional top-level source layer is defined.

## Root data directories

### `config`

Contains editable application settings.

### `languages`

Contains dynamically discovered language JSON files.

### `plugins`

Contains the single local `plugin_db.json` catalog and the `installed` directory.

### `temp`

Contains temporary downloads and working files only.

### `templates/ota`

Contains OTA templates for the unfinished payload-packing workflow. They are not active settings.

## Runtime

### `src/app/runtime/session.py`

Creates one runtime session and registers core services.

### `src/app/runtime/phases.py`

Registers and reads the four typed runtime phases.

### `src/app/runtime/models.py`

Contains the dataclass models for those runtime phases.

### `src/app/runtime/contexts`

Contains narrow resolver modules for the application layer only.

Its root `__init__.py` deliberately re-exports nothing.

## Background work and the UI thread

### `src/app/background_jobs.py`

Creates an application-managed background job.

### `src/app/ui_tasks.py`

Runs worker functions and delivers completion through the UI dispatcher.

### `src/app/ui_feedback.py`

Coordinates application notifications and delivers results through the supplied UI dispatcher.

### `src/logic/common/service_output.py`

Provides a UI-neutral message and progress channel for the logic layer.

## Diagnostics and core errors

### `src/core/diagnostics.py`

Provides an independent sink for core diagnostic events. Standard `logging` is used by default; an operation may explicitly supply another sink at the external boundary.

### `src/core/errors.py`

Contains shared typed errors for the low-level layer.

## MTK Port Tool

### `src/core/mtk_port`

Handles boot images, safe ZIP extraction, property files, and updater scripts.

### `src/logic/tools/mtk_port_tool`

Contains models, profiles, and the porting sequence.

### `src/app/composition/mtk_port_tool.py`

Contains composition functions.

### `src/ui/tabs/tools/mtk_port_tool`

Contains the window and its presentation behavior.

MTK Port Tool code stays within these four explicit package boundaries.

## Projects

### `src/logic/projects`

Contains project domain models, validation, and working operations.

### `src/app/projects`

Contains application controllers for project workflows.

### `src/ui/tabs/project`

Contains project views, presenters, and presentation controllers.

## Plugins

### `src/logic/plugins`

Contains plugin domain models and operations.

### `src/app/plugins`

Contains application workflows, repositories, and runtime adapters.

### `src/ui/tabs/plugins`

Contains plugin windows, forms, cards, and presentation state.

## Updates

### `src/logic/update`

Contains release models and file-preparation operations.

### `src/app/update_controller.py`

Implements the update application state machine.

### `src/app/update_orchestrator.py`

Coordinates update application and cleanup.

### `src/ui/update`

Contains the update window and presentation controller.

## Low-level operations

### `src/core`

Contains image, archive, process, data-format, and filesystem primitives.

Core is not a composition boundary and does not provide a UI facade.

## Typed plugin and Tk boundaries

### `src/logic/plugins/store_models.py`

Validates external catalog JSON and creates immutable `PluginCatalogItem` values.

### `src/logic/plugins/runtime/registry.py`

Stores `VirtualPluginInfo` and typed plugin callables. A third-party plugin's return value remains an opaque `object` until a consumer validates it explicitly.

### `src/logic/plugins/config/service.py`

Converts plugin-window configuration into `PluginDialogConfig`, `PluginConfigInfo`, `PluginControlGroup`, and `PluginControlConfig`.

### `src/app/runtime/contexts/contracts.py`

Contains precise runtime protocols for the scheduler, task runner, state, and Plugin Store. The shared contract does not use `Any`.

### `src/app/ui_feedback.py`

Passes notifications through explicit `text`, `color`, `title`, and `master` fields. The localization catalog is connected to the real dialog in the main window.

### `scripts/quality/check_typed_boundaries.py`

Runs strict Mypy checks for the selected architectural boundaries.

See `typed_boundaries.md` for the detailed contract.
