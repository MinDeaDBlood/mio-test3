from __future__ import annotations

from pathlib import Path

from src.app.runtime.contexts.projects import resolve_project_manager
from src.core.paths import prog_path
from src.logic.projects.pack.hybrid import HybridPackRequest, HybridPackResult, HybridRomPackService


class HybridProjectNotSelectedError(RuntimeError):
    """Raised when Hybrid packing is requested without an active project."""


class HybridPackAction:
    """Build the Hybrid packing request and delegate it to the domain service."""

    def __init__(
        self,
        *,
        project_manager: object,
        template_dir: str | Path,
        service: HybridRomPackService | None = None,
    ) -> None:
        self._project_manager = project_manager
        self._template_dir = Path(template_dir)
        self._service = service or HybridRomPackService()

    def execute(self, right_device: str) -> HybridPackResult:
        if not self._project_manager.exist():
            raise HybridProjectNotSelectedError('Project is not selected')
        normalized_device = right_device.strip()
        if not normalized_device:
            raise ValueError('Target device identifier must not be empty')
        request = HybridPackRequest(
            output_dir=Path(self._project_manager.current_work_output_path()),
            template_dir=self._template_dir,
            right_device=normalized_device,
        )
        return self._service.pack(request)


def build_hybrid_pack_action(
    *,
    project_manager: object | None = None,
    service: HybridRomPackService | None = None,
) -> HybridPackAction:
    return HybridPackAction(
        project_manager=resolve_project_manager(project_manager),
        template_dir=Path(prog_path) / 'bin' / 'extra_flash',
        service=service,
    )


def run_hybrid_pack(
    right_device: str,
    *,
    action: HybridPackAction | None = None,
) -> HybridPackResult:
    return (action or build_hybrid_pack_action()).execute(right_device)


__all__ = [
    'HybridPackAction',
    'HybridProjectNotSelectedError',
    'build_hybrid_pack_action',
    'run_hybrid_pack',
]
