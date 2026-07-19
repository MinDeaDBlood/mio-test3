from __future__ import annotations

import os
import shutil

from src.logic.common.messages import message
from src.logic.projects.convert.runtime_context import ConvertRuntimeContext
from .models import INPUT_FORMATS, ConvertSelection, ConvertRequest, ConvertResult
from .validators import validate_selection, normalize_items
from .format_router import is_dat_family
from .operations import (
    decompress_br,
    decompress_xz,
    dat_to_raw,
    raw_to_sparse,
    raw_to_dat_or_br,
    sparse_to_raw,
    list_sparse_candidates,
    list_raw_candidates,
    iter_image_file_types,
)


def iter_refile(suffix: str, *, runtime: ConvertRuntimeContext | None = None):
    if runtime is None:
        raise ValueError(
            "Conversion operation requires an explicit ConvertRuntimeContext."
        )
    work = runtime.work_path
    try:
        entries = list(os.scandir(work))
    except OSError:
        return
    for entry in sorted(entries, key=lambda item: item.name.lower()):
        if entry.name.endswith(suffix) and entry.is_file():
            yield entry.name


def list_candidate_groups(
    *, runtime: ConvertRuntimeContext | None = None
) -> dict[str, list[str]]:
    if runtime is None:
        raise ValueError(
            "Conversion operation requires an explicit ConvertRuntimeContext."
        )
    groups: dict[str, list[str]] = {
        source_format: [] for source_format in INPUT_FORMATS
    }
    input_work = runtime.work_path
    try:
        input_entries = list(os.scandir(input_work))
    except OSError:
        input_entries = []
    for entry in sorted(input_entries, key=lambda item: item.name.lower()):
        if not entry.is_file():
            continue
        if entry.name.endswith(".new.dat.br"):
            groups["br"].append(entry.name)
        elif entry.name.endswith(".new.dat.xz"):
            groups["xz"].append(entry.name)
        elif entry.name.endswith(".new.dat"):
            groups["dat"].append(entry.name)

    seen_images: set[tuple[str, str]] = set()
    for item_name, file_type in iter_image_file_types(runtime.work_path):
        group_name = "sparse" if file_type == "sparse" else "raw"
        key = (group_name, item_name)
        if key in seen_images:
            continue
        seen_images.add(key)
        groups[group_name].append(item_name)
    return groups


def choose_candidate_group(
    preferred_format: str, *, runtime: ConvertRuntimeContext | None = None
) -> tuple[str, list[str]]:
    groups = list_candidate_groups(runtime=runtime)
    if groups.get(preferred_format):
        return preferred_format, groups[preferred_format]
    for source_format in INPUT_FORMATS:
        if groups.get(source_format):
            return source_format, groups[source_format]
    return preferred_format, []


def list_candidates(
    from_format: str, *, runtime: ConvertRuntimeContext | None = None
) -> list[str]:
    if runtime is None:
        raise ValueError(
            "Conversion operation requires an explicit ConvertRuntimeContext."
        )
    if from_format == "br":
        return list(iter_refile(".new.dat.br", runtime=runtime))
    if from_format == "xz":
        return list(iter_refile(".new.dat.xz", runtime=runtime))
    if from_format == "dat":
        return list(iter_refile(".new.dat", runtime=runtime))
    if from_format == "sparse":
        return list_sparse_candidates(runtime.work_path)
    if from_format == "raw":
        return list_raw_candidates(runtime.work_path)
    return []


def _normalize_input(
    work: str,
    source_format: str,
    item_name: str,
    basename: str,
    *,
    runtime: ConvertRuntimeContext,
) -> tuple[str | None, str | None]:
    current_name = item_name
    if source_format == "br":
        current_name = decompress_br(work, current_name, output=runtime.output)
    elif source_format == "xz":
        current_name = decompress_xz(work, current_name, output=runtime.output)
    if is_dat_family(source_format):
        if source_format in {"br", "xz"} and current_name is None:
            return None, None
        img_path = dat_to_raw(work, current_name, basename, output=runtime.output)
        return current_name, img_path
    if source_format == "sparse":
        if not sparse_to_raw(work, current_name):
            return current_name, None
        return current_name, os.path.join(work, basename + ".img")
    return current_name, os.path.join(
        work, basename + ".img"
    ) if source_format == "raw" else None


def _convert_request(
    work: str, request: ConvertRequest, *, runtime: ConvertRuntimeContext
) -> ConvertResult:
    basename = os.path.basename(request.item_name).split(".")[0]
    if request.target_format == request.source_format:
        source_path = os.path.join(work, request.item_name)
        return ConvertResult(
            item_name=request.item_name,
            source_format=request.source_format,
            target_format=request.target_format,
            succeeded=os.path.isfile(source_path),
        )
    _, raw_path = _normalize_input(
        work, request.source_format, request.item_name, basename, runtime=runtime
    )
    if request.target_format == "raw":
        return ConvertResult(
            item_name=request.item_name,
            source_format=request.source_format,
            target_format=request.target_format,
            succeeded=bool(raw_path and os.path.exists(raw_path)),
        )
    if request.target_format == "sparse":
        if raw_path and os.path.exists(raw_path):
            succeeded = raw_to_sparse(work, basename)
            return ConvertResult(
                item_name=request.item_name,
                source_format=request.source_format,
                target_format=request.target_format,
                succeeded=succeeded,
            )
        return ConvertResult(
            item_name=request.item_name,
            source_format=request.source_format,
            target_format=request.target_format,
            succeeded=False,
        )
    if request.target_format in {"dat", "br"}:
        if request.source_format in {"raw", "sparse"}:
            if not raw_to_sparse(work, basename):
                return ConvertResult(
                    item_name=request.item_name,
                    source_format=request.source_format,
                    target_format=request.target_format,
                    succeeded=False,
                )
        if request.source_format in {"raw", "sparse"} and os.path.exists(
            os.path.join(work, basename + ".img")
        ):
            succeeded = raw_to_dat_or_br(work, basename, request.target_format)
            return ConvertResult(
                item_name=request.item_name,
                source_format=request.source_format,
                target_format=request.target_format,
                succeeded=succeeded,
            )
        if (
            is_dat_family(request.source_format)
            and raw_path
            and os.path.exists(raw_path)
        ):
            if not raw_to_sparse(work, basename):
                return ConvertResult(
                    item_name=request.item_name,
                    source_format=request.source_format,
                    target_format=request.target_format,
                    succeeded=False,
                )
            succeeded = raw_to_dat_or_br(work, basename, request.target_format)
            return ConvertResult(
                item_name=request.item_name,
                source_format=request.source_format,
                target_format=request.target_format,
                succeeded=succeeded,
            )
        return ConvertResult(
            item_name=request.item_name,
            source_format=request.source_format,
            target_format=request.target_format,
            succeeded=False,
        )
    return ConvertResult(
        item_name=request.item_name,
        source_format=request.source_format,
        target_format=request.target_format,
        succeeded=False,
    )


def _prepare_selected_input(
    *,
    runtime: ConvertRuntimeContext,
    output_work: str,
    source_format: str,
    item_name: str,
) -> str | None:
    safe_name = os.path.basename(item_name)
    output_path = os.path.join(output_work, safe_name)
    source_path = os.path.join(runtime.work_path, safe_name)
    if not os.path.isfile(source_path):
        return None
    os.makedirs(output_work, exist_ok=True)
    if os.path.abspath(source_path) != os.path.abspath(output_path):
        shutil.copy2(source_path, output_path)
    if is_dat_family(source_format):
        basename = safe_name.split(".")[0]
        for suffix in (".transfer.list", ".patch.dat"):
            companion_name = basename + suffix
            companion_source = os.path.join(runtime.work_path, companion_name)
            companion_output = os.path.join(output_work, companion_name)
            if (
                os.path.isfile(companion_source)
                and os.path.abspath(companion_source)
                != os.path.abspath(companion_output)
            ):
                shutil.copy2(
                    companion_source,
                    companion_output,
                )
    return safe_name


def convert_selection(
    selection: ConvertSelection, *, runtime: ConvertRuntimeContext | None = None
):
    if not validate_selection(selection):
        return False
    if runtime is None:
        raise ValueError(
            "Conversion operation requires an explicit ConvertRuntimeContext."
        )
    work = runtime.output_path
    os.makedirs(work, exist_ok=True)
    results: list[ConvertResult] = []
    for item_name in normalize_items(selection.items):
        prepared_name = _prepare_selected_input(
            runtime=runtime,
            output_work=work,
            source_format=selection.from_format,
            item_name=item_name,
        )
        if prepared_name is None:
            runtime.output.log(
                message(
                    "file_not_found",
                    "File not found: {item}",
                    item=os.path.join(runtime.work_path, os.path.basename(item_name)),
                )
            )
            results.append(
                ConvertResult(
                    item_name=os.path.basename(item_name),
                    source_format=selection.from_format,
                    target_format=selection.to_format,
                    succeeded=False,
                )
            )
            continue
        runtime.output.log(
            f"[{selection.from_format}->{selection.to_format}]{prepared_name}"
        )
        result = _convert_request(
            work,
            ConvertRequest(
                source_format=selection.from_format,
                target_format=selection.to_format,
                item_name=prepared_name,
            ),
            runtime=runtime,
        )
        results.append(result)
        if not result.succeeded:
            runtime.output.log(
                message(
                    "operation_failed", "Operation failed: {item}", item=prepared_name
                )
            )
    succeeded = bool(results) and all(result.succeeded for result in results)
    if succeeded:
        runtime.output.report(message("operation_complete", "Operation completed"))
    return succeeded


__all__ = [
    "convert_selection",
    "iter_refile",
    "list_candidates",
    "list_candidate_groups",
    "choose_candidate_group",
]
