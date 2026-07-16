from __future__ import annotations

import platform
from pathlib import Path

from .models import (
    PayloadPackAction,
    PayloadPackCapability,
    PayloadPackImplementationAudit,
)

SPEC = PayloadPackAction()

_WINDOWS_UNSUPPORTED_REASON = (
    'Payload packing is not implemented for Windows yet. '
    'The current build contains payload unpack/extract support, but no verified payload generator pipeline.'
)
_GENERIC_UNSUPPORTED_REASON = (
    'Payload packing is not implemented in the current application build. '
    'The action is intentionally unavailable until a real payload generator pipeline is registered.'
)

# Names that would indicate a real full-payload generator, not just payload
# parsing, extraction or signing helpers. This is intentionally conservative:
# payload_extract and sign_payload are not enough to create a new payload.bin.
_GENERATOR_BACKEND_MARKERS = (
    'brillo_update_payload',
    'delta_generator',
    'ota_from_target_files',
    'payload_generator',
    'generate_payload',
    'create_payload.bin',
)


def audit_implementation(project_root: str | Path | None = None) -> PayloadPackImplementationAudit:
    """Return evidence for whether a real payload pack backend exists."""

    has_registered_pipeline = SPEC.implemented and bool(SPEC.supported_platforms)
    evidence: list[str] = []
    has_generator_backend = False

    if project_root is not None:
        root = Path(project_root)
        own_file = Path(__file__).resolve()
        search_roots = [root / 'bin', root / 'scripts', root / 'src']
        for base in search_roots:
            if not base.exists():
                continue
            for path in base.rglob('*'):
                if path.is_dir():
                    continue
                try:
                    if path.resolve() == own_file:
                        continue
                except OSError:
                    pass
                rel = str(path.relative_to(root)).replace('\\', '/')
                lower_name = path.name.lower()
                if any(marker in lower_name for marker in _GENERATOR_BACKEND_MARKERS):
                    evidence.append(rel)
                    has_generator_backend = True
                    continue
                if path.suffix.lower() not in {'.py', '.sh', '.bat', '.cmd', '.ps1', '.txt', '.md'}:
                    continue
                try:
                    text = path.read_text(encoding='utf-8', errors='ignore').lower()
                except OSError:
                    continue
                if any(marker in text for marker in _GENERATOR_BACKEND_MARKERS):
                    evidence.append(rel)
                    has_generator_backend = True

    return PayloadPackImplementationAudit(
        has_registered_pipeline=has_registered_pipeline,
        has_generator_backend=has_generator_backend,
        evidence=tuple(sorted(set(evidence))),
    )


def get_capability(
    system_name: str | None = None,
    *,
    project_root: str | Path | None = None,
) -> PayloadPackCapability:
    """Return the explicit availability contract for payload packing."""

    normalized = system_name or platform.system()
    audit = audit_implementation(project_root) if project_root is not None else None
    platform_supported = normalized in SPEC.supported_platforms
    has_pipeline = SPEC.implemented and platform_supported
    has_backend = audit.has_generator_backend if audit is not None else SPEC.implemented
    available = bool(has_pipeline and has_backend)

    if available:
        reason = 'Payload packing is available.'
    elif normalized == 'Windows':
        reason = _WINDOWS_UNSUPPORTED_REASON
    else:
        reason = _GENERIC_UNSUPPORTED_REASON

    return PayloadPackCapability(
        available=available,
        platform_name=normalized,
        reason=reason,
        audit=audit,
    )


def is_available(system_name: str | None = None) -> bool:
    return get_capability(system_name).available


__all__ = [
    'SPEC',
    'PayloadPackAction',
    'PayloadPackCapability',
    'PayloadPackImplementationAudit',
    'audit_implementation',
    'get_capability',
    'is_available',
]
