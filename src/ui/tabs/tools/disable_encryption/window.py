from __future__ import annotations

from src.ui.contracts import FstabPatchControllerPort
from src.ui.tabs.tools.disable_encryption import keys
from src.ui.tabs.tools.fstab_patch_window import FstabPatchWindow


class DisableEncryption(FstabPatchWindow):
    def __init__(self, *, language) -> None:
        text = language.resolve_required_ui_text
        super().__init__(
            texts=language,
            title=text(keys.TITLE),
            info_text=text(keys.DESCRIPTION),
            available_partitions_text=text(keys.PARTITIONS_GROUP_TITLE),
            select_all_text=text(keys.SELECT_ALL_CHECKBOX),
            refresh_text=text(keys.REFRESH_BUTTON),
            run_text=text(keys.RUN_BUTTON),
            running_text=text(keys.RUNNING_BUTTON),
            no_partitions_text=text(keys.NO_PARTITIONS_MESSAGE),
            selection_warning=text(keys.SELECTION_REQUIRED_MESSAGE),
            completion_message=lambda count: text(keys.COMPLETION_MESSAGE).format(
                count
            ),
            warning_dialog_title=text(keys.WARNING_DIALOG_TITLE),
            warning_dialog_ok=text(keys.WARNING_DIALOG_OK_BUTTON),
            completion_dialog_title=text(keys.COMPLETION_DIALOG_TITLE),
            completion_dialog_ok=text(keys.COMPLETION_DIALOG_OK_BUTTON),
        )

    def attach(self, *, controller: FstabPatchControllerPort) -> None:
        super().attach(controller=controller)


__all__ = ["DisableEncryption"]
