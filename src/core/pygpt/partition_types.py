from __future__ import annotations

from enum import Enum
from uuid import UUID


class PartitionTypes(Enum):
    Unused = UUID('00000000-0000-0000-0000-000000000000')
    MicrosoftBasicData = UUID('ebd0a0a2-b9e5-4433-87c0-68b6b72699c7')
    MicrosoftReserved = UUID('e3c9e316-0b5c-4db8-817d-f92df00215ae')
    LinuxFilesystem = UUID('0fc63daf-8483-4772-8e79-3d69d8477de4')
    LinuxRaidPart = UUID('a19d880f-05fc-4d3b-a006-743f0f84911e')
    LinuxSwapPart = UUID('0657fd6d-a4ab-43c4-84e5-0933c84b4f4f')
    LinuxLVMPart = UUID('e6d6d379-f507-44c2-a23c-238f2a3df928')
    LinuxHomePart = UUID('933ac7e1-2eb4-4f13-b844-0e14e2aef915')
    LinuxPlainDmCryptPart = UUID('7ffec5c9-2d00-49b7-8941-3ea10a5586b7')
    LinuxLUKSPart = UUID('ca7d7ccb-63ed-4c53-861c-1742536059cc')


__all__ = ['PartitionTypes']
