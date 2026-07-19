# Repository structure

The repository root contains launch and build entry points, dependency lists, and runtime resources.

## Application code

`src` contains only code used by the running application.

Tests, manual checks, report generators, and maintenance scripts do not belong under `src`.

The application is divided into these layers:

1. `src/ui` contains windows, widgets, styles, UI resources, and presentation logic.
2. `src/app` contains composition, application controllers, and workflow coordination.
3. `src/logic` contains application operations and the rules for projects, images, and plugins.
4. `src/core` contains low-level format and filesystem algorithms.
5. `src/platform` contains shared adapters for the environment, processes, storage, networking, and restart behavior.

## Tests

`tests` contains automated checks grouped by purpose.

1. `unit` covers individual functions and classes.
2. `functional` covers complete features.
3. `integration` covers components working together.
4. `contract` fixes public interfaces and repository contracts.
5. `regression` protects previously fixed defects.
6. `architecture` enforces layer boundaries and file placement.
7. `smoke` contains fast startup and runtime checks.
8. `e2e` contains end-to-end user flows.
9. `release` verifies builds and archive contents.
10. `external` verifies platform dependencies and external tools.
11. `embedded` contains environment checks moved out of runtime code.
12. `support` contains shared test infrastructure.

Each `test_*.py` module can be launched directly.

```bash
python tests/unit/core/test_byte_size.py
```

## Maintenance scripts

All maintenance scripts live under the root `scripts` directory.

1. `scripts/manual` contains ready-to-run manual suites.
2. `scripts/quality` contains static and structural checks.
3. `scripts/arch_guard` contains Architecture Guard.
4. `scripts/release` contains archive creation and verification.
5. `scripts/audits` contains technical report generators.
6. `scripts/support` contains code shared by scripts.
7. `scripts/config` contains Pytest and Mypy configuration.

The `.cmd` files directly under `scripts` are Windows double-click launchers for the checks.

See [Tests and scripts](tests_and_scripts.md) for the command inventory and execution rules.

## Documentation

1. `docs/en/architecture` and `docs/ru/architecture` contain the matching English and Russian architecture documents.
2. `docs/en/development` and `docs/ru/development` contain the matching developer guides.
3. `docs/archive/audits` contains non-active audit material that does not define the current implementation.
4. `docs/archive/readmes` contains non-active README translations.
5. `docs/README.md` is the language-neutral documentation entry point.

## Runtime data

1. `bin` contains external tools.
2. `config` contains application settings.
3. `languages` contains dynamically discovered language JSON files.
4. `plugins` contains the Plugin Store database and installed plugins.
5. `temp` contains temporary data.
6. `templates` contains runtime templates.
7. `logs` contains application logs.

UI resources live in `src/ui/assets`. There is no root `assets` directory.

## Build output

`build.py` is the only root entry point for building the application.

GitHub Actions invokes `build.py` directly. It does not run files from `scripts` as part of the build.

The distributable archive excludes:

1. `docs`
2. `tests`
3. `scripts`
4. `src`
5. `.github`
6. The root `README.md`
7. Development-tool configuration
