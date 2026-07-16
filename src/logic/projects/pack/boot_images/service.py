from src.logic.projects.boot_images.service import repack_boot_image


def repack_boot(name: str = 'boot', source: str = None, boot: str = None, *, runtime):
    return repack_boot_image(name=name, source=source, boot=boot, runtime=runtime)


def run(mode: str, *, runtime):
    return repack_boot(mode, runtime=runtime)


__all__ = ['repack_boot', 'run']
