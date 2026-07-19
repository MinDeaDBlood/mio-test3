# Logging and diagnostics

This document describes the logging system implemented by the current code. Logs are useful well beyond startup crashes: they reconstruct user actions, background work, file operations, external processes, and plugin activity in one timeline.

## Log location

Each application run creates a separate file under:

```text
logs/
```

The filename includes the date, time, and process ID. A restart—for example, after changing the language—creates a new file in the new process, so diagnosing a restart often requires the two adjacent log files.

The file handler records `DEBUG` and above. The file therefore includes ordinary messages, warnings, errors, and complete tracebacks.

## Common record fields

Each structured record includes:

| Field | Meaning |
|---|---|
| Date and time | Exact event time |
| Level | `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL` |
| PID | Process identifier |
| Thread | Main thread or background-job name |
| Logger | Module or subsystem |
| File and line | Call site that produced the record |
| operation | Current operation |
| op_id | Identifier of one invocation of that operation |

`operation` and `op_id` tie records from different layers into one scenario. For example, one partition-packing run receives its own `op_id`, and the selected partitions, external-tool calls, and final result remain associated with it.

## Recorded events

### Application startup and shutdown

The log records module loading, runtime-session creation, language loading, main-window creation, the startup splash, the first-run wizard, entry into Tk's main loop, restart, and process shutdown.

Unhandled exceptions from the main thread, worker threads, and Tk callbacks are recorded with tracebacks.

### User windows

The shared window system is covered by Tk exception logging. Critical user workflows also record open, confirm, and cancel events. The partition-packing window, for example, records the selected partitions, submitted form values, validation failures, and transfer of the job to the background worker.

### Background jobs

`UiTaskRunner` records the worker name, start, successful completion, and failure. Long-running operations receive their own `operation_context`, including elapsed time.

### Python file operations

After the main log is configured, the application installs a Python audit hook. It watches configuration, plugin, temporary-data, and user-workspace directories.

The following operations are recorded at `INFO`:

1. Opening a file for writing, appending, creation, or modification.
2. Creating a directory.
3. Removing a file or directory.
4. Renaming and moving.
5. Copying a file or directory tree.
6. Changing permissions or metadata.
7. Creating a temporary file or directory.
8. Packing or extracting archives through `shutil`.

Reads, `listdir`, and `scandir` are recorded at `DEBUG`. The `logs` directory is excluded from the file audit; otherwise writing the log would recursively create more audit records.

Repeated identical reads within a short interval are coalesced to keep technical activity from drowning out useful events. Reads of the `tool.exe` executable, access to Windows devices such as `NUL`, and attempts to recreate an existing directory are omitted. Modification, copying, movement, deletion, and creation of new files remain fully recorded.

The audit hook sees operations performed by Python code. It cannot see every internal action of a separate executable. For an external tool, the application records the command, PID, stdout, overall exit code, and elapsed time. That identifies where the external boundary began and ended and lets those calls be correlated with files created around them.

### External processes

The shared process runner records:

1. The command, with secret values removed.
2. The tool-directory path.
3. The child PID.
4. Stdout and stderr lines.
5. Exit code.
6. Elapsed time.
7. Missing-file and operating-system errors.
8. A process that is still alive during cleanup.

### Plugins

The plugin subsystem records:

1. Discovery of installed plugins.
2. Reading `info.json`.
3. Manifest status.
4. Dependencies and missing dependencies.
5. Presence of an external `main.py` or `main.sh` entry point.
6. The resulting logic execution plan.
7. Registration of a Python entry point.
8. Invocation of a Python or shell entry point.
9. Parameter names without exposing their values.
10. Shell-process exit code.
11. Installation, removal, export, and skeleton creation.

Here, `main.sh` means the entry point of an installed third-party plugin at `plugins/installed/<id>/main.sh`. It is not a maintenance script under `src`.

### Partition packing

The packing workflow records:

1. Opening the options window and the selected partitions.
2. Form cancellation or confirmation.
3. Validated packing options.
4. Background-job submission.
5. The `work`, `input`, and `output` paths.
6. Reading `parts_info`.
7. The detected type of every partition.
8. Start and completion of each partition.
9. Filesystem and conversion choices.
10. Calls to external packers.
11. The failing stage or final result.

After the user presses Build, the options window closes and the build continues in the background. Messages remain visible in the main-window log area and are written to the file at the same time.

The plugin `before_pack` event fires only after the Build button confirms the form and validation succeeds. Merely opening or canceling the window does not trigger the event.

## Log levels

| Level | Use |
|---|---|
| `DEBUG` | Detailed state, reads, path selection, and technical transitions |
| `INFO` | Operation start or finish, file writes, process launch, and result |
| `WARNING` | A recoverable problem, unsupported variant, or rejected operation |
| `ERROR` | An operation failed, but the application can keep running |
| `CRITICAL` | An unhandled exception or a process that cannot continue |

## Collecting an error report

1. Close any older application instance.
2. Start the application and reproduce the problem once.
3. Note the exact action, such as “Project → Build super → Start.”
4. If the UI still responds, close the application normally.
5. Attach the latest file from `logs`.
6. If an automatic restart happened immediately before the problem, attach the two latest files.
7. Include a screenshot when the problem involves a window or its layout.

Do not copy only the final two lines. The complete file includes the `operation`, `op_id`, and preceding state needed to diagnose the cause.

## Logging-system checks

The primary automated checks are:

```bash
python tests/unit/platform/test_filesystem_audit.py
python tests/unit/platform/test_crash_logging.py
python tests/functional/ui/test_window_foreground.py
```

Run the complete manual suite with:

```bash
python scripts/manual/manual_unit_contracts.py
```

Run GUI scenarios with:

```bash
python scripts/manual/manual_gui_smoke.py
```

GitHub Actions does not run these checks automatically. Developers run them locally when needed.
