from src.logic.projects.boot_images.service import unpack_boot_image


def unpack_boot(name: str = 'boot', boot: str = None, work: str = None, *, runtime=None):
    return unpack_boot_image(name=name, boot=boot, work=work, runtime=runtime)


def run(mode: str, *, runtime):
    return unpack_boot(mode, runtime=runtime)


__all__ = ['run', 'unpack_boot']
