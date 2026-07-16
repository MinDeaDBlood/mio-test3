from __future__ import annotations

from src.logic.tools.mtk_port_tool.boot_port import MtkBootPortMixin
from src.logic.tools.mtk_port_tool.operation_base import (
    MtkOperationBase,
    MtkPortBinaries,
    MtkPortOperationError,
)
from src.logic.tools.mtk_port_tool.packaging import MtkPackagingMixin
from src.logic.tools.mtk_port_tool.system_port import MtkSystemPortMixin


class MtkPortOperation(
    MtkBootPortMixin,
    MtkSystemPortMixin,
    MtkPackagingMixin,
    MtkOperationBase,
):
    """Coordinate MTK port stages while each stage owns one responsibility."""

    def start(self) -> None:
        self._decompress_portzip()
        if self._port_boot() is False:
            raise MtkPortOperationError('MTK boot porting failed')
        if self._port_system() is False:
            raise MtkPortOperationError('MTK system porting failed')
        if self.genimg:
            self._pack_img()
        else:
            self._pack_rom()
        self.clean()


__all__ = ['MtkPortBinaries', 'MtkPortOperation', 'MtkPortOperationError']
