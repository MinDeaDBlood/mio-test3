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


from pathlib import Path

from PIL import Image

from src.core.file_types import gettype
from src.core.splash_editor import process_splashimg, splash_repack


def test_splash_roundtrip_preserves_multiple_images(tmp_path: Path) -> None:
    source_dir = tmp_path / 'splash'
    source_dir.mkdir()
    image1 = Image.new('RGB', (16, 8), (20, 40, 60))
    image2 = Image.new('RGBA', (9, 7), (200, 100, 50, 255))
    image1.save(source_dir / 'splash1.png')
    image2.save(source_dir / 'splash2.png')

    output = splash_repack(source_dir, tmp_path / 'splash.img', nolimit=True)
    assert gettype(str(output)) == 'splash'

    extracted = process_splashimg(output, tmp_path / 'unpacked' / 'splash.png')
    assert [path.name for path in extracted] == ['splash1.png', 'splash2.png']
    with Image.open(extracted[0]) as decoded1, Image.open(extracted[1]) as decoded2:
        assert decoded1.convert('RGB').tobytes() == image1.tobytes()
        assert decoded2.convert('RGB').tobytes() == image2.convert('RGB').tobytes()


def test_splash_repack_requires_first_image(tmp_path: Path) -> None:
    empty = tmp_path / 'empty'
    empty.mkdir()
    try:
        splash_repack(empty, tmp_path / 'splash.img')
    except FileNotFoundError as exc:
        assert 'splash1.png' in str(exc)
    else:
        raise AssertionError('Splash packing accepted an empty directory')

if __name__ == "__main__":
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
