# Plugin development

This document describes the plugin format implemented by the current application, logic, and platform layers.

## Installed plugin location

Installed plugins live under:

```text
plugins/installed/<identifier>/
```

A plugin directory is considered installed when it contains `info.json`.

## Minimal Python plugin

```text
plugins/installed/example_plugin/
  info.json
  main.py
```

Example `info.json`:

```json
{
  "identifier": "example_plugin",
  "name": "Example Plugin",
  "version": "1.0",
  "author": "Author",
  "describe": "What the plugin does",
  "depend": ""
}
```

`identifier` must match the directory name.

`main.py` must provide either a `main` function or an `entrances` dictionary.

The simplest form is:

```python
def main(**values):
    print(values)
```

At invocation time, MIO Kitchen matches function parameter names to runtime values. A required parameter for which no runtime value exists causes registration or invocation to fail.

To expose several entry points:

```python
from src.logic.plugins.runtime import Entry


def run_main(**values):
    print(values)


def before_pack(**values):
    print(values)


entrances = {
    Entry.main: run_main,
    Entry.before_pack: before_pack,
}
```

The available `Entry` values are defined in `src/logic/plugins/runtime/registry.py`.

`Entry.before_pack` runs only when partition packing actually starts. Opening the options window, reviewing settings, or closing it with Cancel does not start a build and does not invoke the plugin.

## Execution path

The UI collects the plugin identifier and form values. `PluginManagerController` in the application layer coordinates the workflow through `PluginGatewayProtocol`. Application code neither reads plugin files nor executes third-party code.

`PluginGateway` in the platform layer inspects the directory, `info.json`, dependencies, and available entry points. `plan_plugin_execution` in logic turns that inspection into a pure execution plan without touching files or processes. The application layer then passes the completed plan back to the platform adapter.

Loading `main.py` and running an external `main.sh` stay in the platform layer. The responsibility chain is:

```text
UI
  → PluginManagerController, application
  → PluginGatewayProtocol
  → PluginGateway inspection, platform
  → plan_plugin_execution, logic
  → PluginGateway execution, platform
```

## Shell plugin

A shell plugin uses `main.sh` instead of `main.py`.

```text
plugins/installed/example_shell_plugin/
  info.json
  main.sh
```

MIO Kitchen launches `main.sh` through BusyBox. Runtime values become environment variables, together with these built-in variables:

| Variable | Value |
|---|---|
| `tool_bin` | External-tools directory |
| `version` | MIO Kitchen version |
| `language` | Current language |
| `bin` | Current plugin directory |
| `moddir` | Shared installed-plugin directory |
| `project_output` | Current project's `output` directory |
| `project` | Current project's working directory |

A shell plugin requires an active project.

## Plugin dependencies

`depend` contains space-separated identifiers of other plugins.

```json
{
  "depend": "base_plugin helper_plugin"
}
```

Before installation and execution, MIO Kitchen verifies that those directories exist under `plugins/installed`.

## Plugin window configuration

When a plugin directory contains `main.json`, Plugin Manager can use it to describe the plugin's configuration controls.

`plugin_config_path` in `src/logic/plugins/module_manager.py` resolves the file path.

Models in `src/logic/plugins/config/service.py` validate the format. Before adding a field, check that implementation rather than relying on examples from older plugins.

## MPK format

An MPK is a ZIP archive with this structure:

```text
plugin.mpk
  info
  main.zip
  icon
```

`icon` is optional.

`info` is an INI file with a `[module]` section.

Example:

```ini
[module]
identifier = example_plugin
name = Example Plugin
version = 1.0
author = Author
describe = What the plugin does
resource = main.zip
system = all
arch = all
depend =
```

`main.zip` contains the files extracted into the installed-plugin directory.

The installer verifies that:

1. The outer archive is valid ZIP.
2. The archive contains `info`.
3. `info` defines `identifier` and `resource`.
4. The named resource exists.
5. The current platform matches `supports` or `system`.
6. The current architecture matches `arch`.
7. Every identifier in `depend` is installed.

## Exporting MPK

Plugin Manager builds an MPK from an installed directory.

During export:

1. `info.json` is converted into the INI file `info`.
2. Every file except `icon` is packed into `main.zip`, or into a resource with another configured name.
3. `icon` is added separately when present.

The implementation lives in `src/logic/plugins/export/service.py`.

## Creating a plugin skeleton

The built-in create-plugin action makes a directory and `info.json`. It does not generate a working `main.py`.

After creating the skeleton, add a `main.py` entry point or an external `main.sh` by hand. These files live only inside the installed-plugin directory; they are not project maintenance scripts under `src`.

## Security

A Python plugin runs inside the MIO Kitchen process and can execute arbitrary code with the current user's permissions.

A shell plugin runs through an external shell and likewise has access to the current user's files.

Install plugins only from trusted sources. The current implementation does not provide an isolated sandbox.

## Checks after plugin-system changes

```bash
python scripts/quality/check_typed_boundaries.py
python scripts/arch_guard/main.py
python -m pytest tests/unit/logic tests/integration tests/functional -q --rootdir=. -c scripts/config/pytest.ini
```

Run the complete manual suite with:

```bash
python scripts/manual/manual_unit_contracts.py
```
