from enum import Enum


class DecryptXtcValidationError(Enum):
    PATH_REQUIRED = 'path_required'
    PATH_NOT_FOUND = 'path_not_found'


__all__ = ['DecryptXtcValidationError']
