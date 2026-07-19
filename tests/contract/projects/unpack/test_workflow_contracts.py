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


import sys
sys.path.insert(0, '.')

import os
import tempfile
from pathlib import Path
from types import SimpleNamespace

from src.logic.projects.unpack.workflow import service as unpack_workflow_service


def _exercise_unpack_workflow_hotspots() -> None:
    with tempfile.TemporaryDirectory() as td:
        work = Path(td)
        (work / 'system.new.dat').write_bytes(b'dat')
        (work / 'system.transfer.list').write_text('transfer')
        (work / 'system.patch.dat').write_text('patch')
        original_sdat2img = unpack_workflow_service.Sdat2img
        try:
            def _fake_sdat2img(_transfer, _new_dat, output_img):
                Path(output_img).write_bytes(b'img')
                return SimpleNamespace(version='4')

            unpack_workflow_service.Sdat2img = _fake_sdat2img
            parts = {}
            result = unpack_workflow_service.unpack_compressed_dat(td, td, 'system', parts)
        finally:
            unpack_workflow_service.Sdat2img = original_sdat2img
        assert result is False
        assert parts['dat_ver'] == '4'
        assert (work / 'system.img').exists()
        assert (work / 'system.new.dat').exists()
        assert (work / 'system.transfer.list').exists()
        assert (work / 'system.patch.dat').exists()

    with tempfile.TemporaryDirectory() as td:
        from src.logic.projects.unpack.workflow import image_operations

        work = Path(td)
        image_path = work / 'system.img'
        image_path.write_bytes(b'sparse')
        state = {'converted': False}
        extracted = []
        original_gettype = image_operations.gettype
        original_simg2img = image_operations.simg2img
        original_extract_ext = image_operations.extract_ext_image
        try:
            image_operations.gettype = lambda _path: 'ext' if state['converted'] else 'sparse'
            image_operations.simg2img = lambda _path: state.__setitem__('converted', True)
            image_operations.extract_ext_image = lambda runtime, work_path, partition_name, parts, **_kwargs: (
                extracted.append((runtime.work_path, work_path, partition_name, dict(parts))),
                True,
            )[1]
            runtime = SimpleNamespace(
                input_path=td + os.sep,
                work_path=td + os.sep,
                output=SimpleNamespace(log=lambda *args, **kwargs: None, report=lambda *args, **kwargs: None),
            )
            parts = {'system': 'legacy'}
            image_operations.process_partition_image(
                runtime,
                td,
                'system',
                str(image_path),
                parts,
                SimpleNamespace(write=lambda _data: None),
            )
        finally:
            image_operations.gettype = original_gettype
            image_operations.simg2img = original_simg2img
            image_operations.extract_ext_image = original_extract_ext
        assert state['converted'] is True
        assert parts['system'] == 'ext'
        assert extracted and extracted[0][2] == 'system'

    from src.logic.projects.unpack.workflow.image_processing import ImageProcessingOperations, process_existing_image

    class _FakeOutput:
        def __init__(self):
            self.logs = []
            self.notifications = []

        def log(self, message):
            self.logs.append(message)

        def notify(self, *args):
            self.notifications.append(args)

    def _ops_for(get_type, *, output, calls):
        class _FakeVbpatch:
            def __init__(self, image_path):
                self.image_path = image_path

            def disavb(self):
                calls.append(('disavb', self.image_path))
                return True

        return ImageProcessingOperations(
            get_type=get_type,
            is_empty_image=lambda _path: False,
            simg2img=lambda path: calls.append(('simg2img', path)),
            lpunpack_get_info=lambda path: {'image': path},
            lpunpack_unpack=lambda image_path, work_path: (calls.append(('lpunpack_unpack', image_path, work_path)), Path(work_path, 'system.img').write_bytes(b'partition'))[-1],
            normalize_super_outputs=lambda work_path: calls.append(('normalize_super_outputs', work_path)),
            unpack_dtbo=lambda *args, **kwargs: (calls.append(('unpack_dtbo', args, kwargs)), True)[1],
            unpack_boot=lambda *args, **kwargs: (calls.append(('unpack_boot', args, kwargs)), True)[1],
            logo_dump=lambda *args, **kwargs: (calls.append(('logo_dump', args, kwargs)), True)[1],
            logo_dumper_cls=type('FakeLogoDumper', (), {'__init__': lambda self, *args, **kwargs: None, 'check_img': lambda self, image_path: None}),
            vbpatch_cls=_FakeVbpatch,
            romfs_parse_cls=type('FakeRomfsParse', (), {'__init__': lambda self, *args, **kwargs: None, 'extract': lambda self, work_path: calls.append(('romfs_extract', work_path))}),
            guoke_logo_cls=type('FakeGuokeLogo', (), {'unpack': lambda self, image_path, output_path: calls.append(('guoke_unpack', image_path, output_path))}),
            aml_main=lambda image_path, work_path: calls.append(('aml_main', image_path, work_path)),
            call=lambda *args, **kwargs: calls.append(('call', args, kwargs)),
            extract_ext_image=lambda runtime, work_path, partition_name, parts, **kwargs: (calls.append(('extract_ext_image', work_path, partition_name, dict(parts), kwargs.get('image_path'))), True)[1],
            extract_erofs_image=lambda runtime, work_path, partition_name, **kwargs: (calls.append(('extract_erofs_image', work_path, partition_name, kwargs.get('image_path'))), True)[1],
            extract_f2fs_image=lambda runtime, work_path, partition_name, **kwargs: (calls.append(('extract_f2fs_image', work_path, partition_name, kwargs.get('image_path'))), True)[1],
            extract_gpt_image=lambda runtime, work_path, partition_name, **kwargs: (calls.append(('extract_gpt_image', work_path, partition_name, kwargs.get('image_path'))), True)[1],
            extract_splash_image=lambda runtime, work_path, partition_name, **kwargs: (calls.append(('extract_splash_image', work_path, partition_name, kwargs.get('image_path'))), True)[1],
            runtime_output=lambda _runtime: output,
        )

    with tempfile.TemporaryDirectory() as td:
        output = _FakeOutput()
        calls = []
        writes = []
        work = Path(td)
        (work / 'super.img').write_bytes(b'super')
        process_existing_image(
            SimpleNamespace(input_path=td, work_path=td + os.sep),
            td,
            'super',
            str(work / 'super.img'),
            {},
            SimpleNamespace(write=lambda data: writes.append(dict(data))),
            operations=_ops_for(lambda _path: 'super', output=output, calls=calls),
        )
        assert ('lpunpack_unpack', str(work / 'super.img'), td) in calls
        assert ('normalize_super_outputs', td) in calls
        assert writes and writes[-1]['super_info']['image'] == str(work / 'super.img')

    with tempfile.TemporaryDirectory() as td:
        output = _FakeOutput()
        calls = []
        parts = {}
        process_existing_image(
            SimpleNamespace(input_path=td, work_path=td + os.sep),
            td,
            'vbmeta',
            str(Path(td) / 'vbmeta.img'),
            parts,
            SimpleNamespace(write=lambda _data: None),
            operations=_ops_for(lambda _path: 'vbmeta', output=output, calls=calls),
        )
        assert calls == [('disavb', str(Path(td) / 'vbmeta.img'))]
        assert parts['vbmeta'] == 'vbmeta'

    for file_type, expected_call in (('gpt', 'extract_gpt_image'), ('splash', 'extract_splash_image')):
        with tempfile.TemporaryDirectory() as td:
            output = _FakeOutput()
            calls = []
            parts = {}
            process_existing_image(
                SimpleNamespace(input_path=td, work_path=td + os.sep),
                td,
                file_type,
                str(Path(td) / f'{file_type}.img'),
                parts,
                SimpleNamespace(write=lambda _data: None),
                operations=_ops_for(lambda _path, current=file_type: current, output=output, calls=calls),
            )
            assert calls == [(expected_call, td, file_type, str(Path(td) / f'{file_type}.img'))]
            assert parts[file_type] == file_type


def _exercise_unpack_compressed_dat_helper() -> None:
    from src.logic.projects.unpack.workflow.compressed_dat import unpack_compressed_dat as helper_unpack_compressed_dat

    with tempfile.TemporaryDirectory() as td:
        work = Path(td)
        (work / 'vendor.new.dat').write_bytes(b'ab')
        (work / 'vendor.transfer.list').write_text('transfer')
        calls = []

        class FakeSdat2img:
            version = '5'

            def __init__(self, transfer, dat, img):
                calls.append((transfer, dat, img))
                Path(img).write_bytes(b'img')

        parts = {}
        result = helper_unpack_compressed_dat(
            td,
            td,
            'vendor',
            parts,
            sdat2img_cls=FakeSdat2img,
            call_func=lambda *_args, **_kwargs: 0,
        )
        assert result is False
        assert parts['dat_ver'] == '5'
        assert calls and calls[0][0].endswith('vendor.transfer.list')
        assert (work / 'vendor.img').exists()
        assert (work / 'vendor.new.dat').exists()
        assert (work / 'vendor.transfer.list').exists()


def run_all() -> None:
    _exercise_unpack_workflow_hotspots()
    _exercise_unpack_compressed_dat_helper()


def test_contracts() -> None:
    run_all()

if __name__ == "__main__":
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
