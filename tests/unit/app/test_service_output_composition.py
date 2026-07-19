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


from src.app.composition.service_output import build_ui_service_output
from src.logic.common.messages import message
from src.logic.common.service_output import OutputSeverity


class Texts:
    def resolve_optional(self, key: str, *, default: str) -> str:
        return {"common_service_output_operation_success": "Готово: {item}"}.get(
            key, default
        )


def test_app_composes_logic_output_with_ui_sink() -> None:
    logs: list[str] = []
    notifications: list[dict[str, str]] = []
    output = build_ui_service_output(
        texts=Texts(),
        log=logs.append,
        notify=lambda **kwargs: notifications.append(kwargs),
    )

    output.log("plain log")
    output.report(
        message("operation_complete", "Completed: {item}", item="system"),
        severity=OutputSeverity.SUCCESS,
    )

    assert logs == ["plain log"]
    assert notifications == [{"message": "Готово: system", "color": "green"}]

if __name__ == "__main__":
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
