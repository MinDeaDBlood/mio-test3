#!/usr/bin/env python3
from __future__ import annotations

# Direct file execution bootstrap
import sys as _direct_sys
from pathlib import Path as _DirectPath

_DIRECT_PROJECT_ROOT = _DirectPath(__file__).resolve().parent
while _DIRECT_PROJECT_ROOT != _DIRECT_PROJECT_ROOT.parent:
    if (
        (_DIRECT_PROJECT_ROOT / "src").is_dir()
        and (_DIRECT_PROJECT_ROOT / "tests").is_dir()
        and (_DIRECT_PROJECT_ROOT / "scripts").is_dir()
    ):
        break
    _DIRECT_PROJECT_ROOT = _DIRECT_PROJECT_ROOT.parent
else:
    raise RuntimeError(f"Project root was not found for {__file__}")

_direct_root_text = str(_DIRECT_PROJECT_ROOT)
if _direct_root_text not in _direct_sys.path:
    _direct_sys.path.insert(0, _direct_root_text)
if __package__ in {None, ""}:
    _direct_relative = _DirectPath(__file__).resolve().relative_to(
        _DIRECT_PROJECT_ROOT
    ).with_suffix("")
    __package__ = ".".join(_direct_relative.parts[:-1])


import argparse
import ast
import json
from dataclasses import asdict, dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
UI_ROOT = PROJECT_ROOT / 'src' / 'ui'
CONTROL_TYPES = {'Button', 'Checkbutton', 'Radiobutton'}


@dataclass(frozen=True)
class ControlRecord:
    path: str
    line: int
    control_type: str
    target: str | None
    command_at_construction: bool
    command_configured_later: bool
    has_variable: bool

    @property
    def connected(self) -> bool:
        if self.control_type == 'Button':
            return self.command_at_construction or self.command_configured_later
        return self.command_at_construction or self.command_configured_later or self.has_variable


def _name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _name(node.value)
        return f'{prefix}.{node.attr}' if prefix else node.attr
    return None


def _keyword_enabled(call: ast.Call, keyword_name: str) -> bool:
    for keyword in call.keywords:
        if keyword.arg != keyword_name:
            continue
        return not (isinstance(keyword.value, ast.Constant) and keyword.value.value is None)
    return False


def audit_file(path: Path) -> list[ControlRecord]:
    tree = ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
    parents: dict[ast.AST, ast.AST] = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            parents[child] = parent

    later_commands: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr not in {'configure', 'config'}:
            continue
        target = _name(node.func.value)
        if target and _keyword_enabled(node, 'command'):
            later_commands.add(target)

    records: list[ControlRecord] = []
    for call in (node for node in ast.walk(tree) if isinstance(node, ast.Call)):
        control_type = _name(call.func)
        if not control_type:
            continue
        control_type = control_type.rsplit('.', 1)[-1]
        if control_type not in CONTROL_TYPES:
            continue
        target: str | None = None
        parent = parents.get(call)
        if isinstance(parent, ast.Assign) and parent.targets:
            target = _name(parent.targets[0])
        elif isinstance(parent, ast.AnnAssign):
            target = _name(parent.target)
        records.append(
            ControlRecord(
                path=str(path.relative_to(PROJECT_ROOT)),
                line=call.lineno,
                control_type=control_type,
                target=target,
                command_at_construction=_keyword_enabled(call, 'command'),
                command_configured_later=bool(target and target in later_commands),
                has_variable=_keyword_enabled(call, 'variable'),
            )
        )
    return records


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Audit UI controls and write the control inventory report.')
    arguments = (
        _direct_sys.argv[1:]
        if argv is None and __name__ == "__main__"
        else (argv or [])
    )
    parser.parse_args(arguments)
    records = [record for path in UI_ROOT.rglob('*.py') for record in audit_file(path)]
    unresolved = [record for record in records if not record.connected]
    counts = {
        control_type: sum(record.control_type == control_type for record in records)
        for control_type in sorted(CONTROL_TYPES)
    }
    report = {
        'success': not unresolved,
        'counts': counts,
        'total': len(records),
        'unresolved_controls': [asdict(record) for record in unresolved],
        'state_only_selectors': [
            asdict(record)
            for record in records
            if record.control_type in {'Checkbutton', 'Radiobutton'}
            and record.has_variable
            and not record.command_at_construction
            and not record.command_configured_later
        ],
        'configured_after_construction': [
            asdict(record) for record in records if record.command_configured_later and not record.command_at_construction
        ],
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report['success'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
