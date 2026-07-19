# Runtime environment

## Python dependencies

Install the application's Python dependencies from the repository root.

```bash
python -m pip install -r requirements.txt
```

Install the optional local quality tools separately.

```bash
python -m pip install -r requirements-quality.txt
```

`requirements-quality.txt` is not used by GitHub Actions and is not required by users of the packaged application.

The source launcher supports Python 3.10 or newer. The current GitHub Actions build uses Python 3.12.

## System dependencies

Windows uses Tk bundled with the official Python distribution.

Linux requires Tk and LZO. GitHub Actions installs `python3-tk` and `liblzo2-dev` only while building the Linux package.

macOS uses the selected runner environment together with the packages in `requirements.txt`.

## Manual environment checks

```bash
python scripts/quality/check_system_dependencies.py
python scripts/quality/check_required_dependencies.py --smoke-only
python scripts/quality/check_required_assets.py
```

These commands do not run automatically during a build.

## GUI checks on Linux

When Xvfb is available, run the graphical checks with:

```bash
xvfb-run -a python scripts/manual/manual_gui_smoke.py --full
```

GitHub Actions does not run this suite. It is a manual validation path.

## Runtime directories

The packaged application keeps editable data next to the executable.

```text
<application root>/
  bin/
  config/
    settings.ini
    context_rules.json
    mtk_port_profiles.json
  languages/
  plugins/
    plugin_db.json
    installed/
  temp/
    plugins/
      downloads/
      runtime/
    updates/
    magisk/
    mtk_port/
  templates/
    ota/
  logs/
```

User projects are created below the workspace selected in Settings. Every project contains `input`, `unpack`, and `output`.

## Directory ownership

### `bin`

Contains external executables and their supporting resources. Application settings and installed plugins are not stored here.

### `config`

Contains editable application configuration. Prefer editing these files while the application is closed.

### `languages`

The application discovers `languages/*.json` dynamically. Adding a language does not require a source-code change when the JSON contains the required keys and valid metadata.

### `plugins`

`plugins/plugin_db.json` is the only local Plugin Store database.

Installed plugins live under `plugins/installed`.

Downloaded archives and temporary extraction data live under `temp/plugins`.

### `temp`

Contains temporary application data only. Installed modules use `plugins/installed`; runtime path resolution does not consult alternate roots.

### `templates/ota`

Contains templates for unfinished payload-packing support. The active Tools windows do not use these files.

### UI resources

Images and the resource loader live under `src/ui/assets` in the source tree. There is no separate root `assets` directory.

## GitHub Actions

The `.github/workflows/build.yml` workflow performs these steps:

1. Checks out the source.
2. Installs Python 3.12.
3. Installs `requirements.txt`.
4. Runs `build.py` for the selected platform.
5. Verifies the finished ZIP archives before publication.
6. Publishes a release when the workflow inputs allow it.

The workflow does not invoke files under `scripts`, Pytest, Ruff, Mypy, or Architecture Guard.

## Release archive cleanup

`scripts/release/build_release_archive.py` excludes generated content from:

```text
plugins/installed
temp
logs
Projects
```

The distributable build also excludes `docs`, `tests`, `scripts`, `src`, `.github`, and development-tool configuration.

## Application restart

When the language changes, the packaged application launches a new process through `src/platform/process_restart.py`.

For a PyInstaller one-file build, the child process receives `PYINSTALLER_RESET_ENVIRONMENT=1`. That gives the restarted instance its own temporary extraction directory instead of tying it to files owned by the previous process.
