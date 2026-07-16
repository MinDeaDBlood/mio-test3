from __future__ import annotations

from src.ui.update import keys
import logging
from enum import Enum, auto
from src.ui.contracts import (
    PendingUpdateOutcomePort,
    UpdateCheckOutcomePort,
    UpdateWorkflowPort,
)


class UpdateActionMode(Enum):
    CHECK = auto()
    INSTALL = auto()


class UpdatePresentationController:
    """Update the updater view and delegate all update work to the application workflow."""

    def __init__(
        self,
        *,
        view,
        host_window,
        settings,
        states,
        workflow: UpdateWorkflowPort,
        texts,
        logger=logging,
    ) -> None:
        self.view = view
        self.host_window = host_window
        self.settings = settings
        self.states = states
        self.workflow = workflow
        self.texts = texts
        self.logger = logger
        self.mode = UpdateActionMode.CHECK

    def start(self) -> None:
        if self.settings.updating == "true":
            self._show_busy_state()
            self.workflow.request_pending(
                on_success=self._finalize_pending_update,
                on_error=self._handle_pending_update_error,
            )
            return
        self.request_update()

    def request_update(self) -> None:
        if self.mode is UpdateActionMode.INSTALL:
            self._request_install_or_pull()
        else:
            self._request_metadata_refresh()

    def close(self) -> None:
        self.states.update_window = False
        self.view.destroy()

    def _request_metadata_refresh(self) -> None:
        self.view.set_notice(self.texts.resolve_required_ui_text(keys.UPDATE_PRESENTER_FETCHING_DATA))
        self.view.clear_change_log()
        self.workflow.request_check(
            on_success=self._apply_release_check, on_error=self._handle_fetch_error
        )

    def _apply_release_check(self, outcome: UpdateCheckOutcomePort) -> None:
        if not self.view.winfo_exists() or not self.states.update_window:
            return
        result = outcome.release
        if result.has_update and result.new_version:
            self.view.set_notice(
                self.texts.resolve_required_ui_text(keys.UPDATE_PRESENTER_NEW_VERSION_FORMAT) % result.new_version,
                color="orange",
            )
            self.view.append_change_log(result.body)
            if outcome.selection.found:
                self.mode = UpdateActionMode.INSTALL
                self.view.set_action_button(text=self.texts.resolve_required_ui_text(keys.UPDATE_PRESENTER_UPDATE_NOW))
            else:
                self.mode = UpdateActionMode.CHECK
                self.view.set_notice(
                    self.texts.resolve_required_ui_text(keys.UPDATE_PRESENTER_DEVICE_UPDATES_NOT_FOUND), color="red"
                )
                self.view.set_action_button(text=self.texts.resolve_required_ui_text(keys.UPDATE_PRESENTER_RETRY))
            return
        self.mode = UpdateActionMode.CHECK
        self.view.set_notice(self.texts.resolve_required_ui_text(keys.UPDATE_PRESENTER_LATEST_VERSION), color="green")
        self.view.append_change_log(result.body)

    def _handle_fetch_error(self, exc: Exception) -> None:
        if not self.view.winfo_exists() or not self.states.update_window:
            return
        raw_text = str(exc.raw_text) if hasattr(exc, "raw_text") else ""
        self.mode = UpdateActionMode.CHECK
        self.view.set_notice(
            self.texts.resolve_required_ui_text(keys.UPDATE_PRESENTER_UPDATE_DOWNLOAD_FAILED)
            if not raw_text
            else self.texts.resolve_required_ui_text(keys.UPDATE_PRESENTER_UPDATE_PARSE_FAILED),
            color="red",
        )
        self.view.set_action_button(text=self.texts.resolve_required_ui_text(keys.UPDATE_PRESENTER_RETRY))
        self.view.append_change_log(raw_text or str(exc))

    def _request_install_or_pull(self) -> None:
        self._show_busy_state()
        try:
            self.workflow.request_install(
                on_progress=self.view.set_progress,
                is_cancelled=lambda: not self.states.update_window,
                on_success=self._finalize_install,
                on_error=self._show_action_error,
            )
        except Exception as exc:
            self._show_action_error(exc)

    def _finalize_install(self, payload: object | None) -> None:
        if not self.view.winfo_exists():
            return
        if payload is None:
            self._reset_after_git_pull()
            return
        self.workflow.persist_and_launch(payload)
        self.host_window.withdraw()
        self.host_window.destroy()

    def _finalize_pending_update(self, outcome: PendingUpdateOutcomePort) -> None:
        result = outcome.result
        if outcome.mode == "apply":
            for warning_path in result.warning_paths:
                self.logger.warning(warning_path)
            if not result.success:
                self.view.set_notice(
                    self.texts.resolve_required_ui_text(keys.UPDATE_PRESENTER_UPDATE_FAILED), color="red"
                )
                self.view.set_action_button(text=self.texts.resolve_required_ui_text(keys.UPDATE_PRESENTER_RETRY))
                return
            self.host_window.destroy()
            return
        if outcome.mode == "cleanup":
            for failed_path in result.failed_paths:
                self.logger.warning(failed_path)
            self.host_window.wm_deiconify()
            self.close()
            return
        raise ValueError(f"Unsupported pending update mode: {outcome.mode}")

    def _handle_pending_update_error(self, exc: Exception) -> None:
        self.logger.exception(
            "Pending update failed", exc_info=(type(exc), exc, exc.__traceback__)
        )
        self.workflow.recover_pending_failure()
        self.view.set_notice(self.texts.resolve_required_ui_text(keys.UPDATE_PRESENTER_UPDATE_FAILED), color="red")
        self.view.set_action_button(text=self.texts.resolve_required_ui_text(keys.UPDATE_PRESENTER_RETRY))
        self.view.reset_progress()

    def _show_busy_state(self) -> None:
        self.host_window.withdraw()
        self.view.show_busy(
            notice_text=self.texts.resolve_required_ui_text(keys.UPDATE_PRESENTER_APPLYING_UPDATE_PACKAGE),
            button_text=self.texts.resolve_required_ui_text(keys.UPDATE_PRESENTER_UPDATING),
        )

    def _show_action_error(self, exc: Exception) -> None:
        self.logger.error(
            "Update action failed", exc_info=(type(exc), exc, exc.__traceback__)
        )
        if not self.view.winfo_exists():
            return
        self.mode = UpdateActionMode.CHECK
        self.view.set_notice(
            self.texts.resolve_required_ui_text(keys.UPDATE_PRESENTER_DOWNLOAD_FAILED_NETWORK), color="red"
        )
        self.view.set_action_button(text=self.texts.resolve_required_ui_text(keys.UPDATE_PRESENTER_RETRY))
        self.view.reset_progress()
        self.host_window.wm_deiconify()

    def _reset_after_git_pull(self) -> None:
        if not self.view.winfo_exists():
            return
        self.mode = UpdateActionMode.CHECK
        self.view.set_action_button(text=self.texts.resolve_required_ui_text(keys.UPDATE_PRESENTER_CHECK_UPDATES))
        self.view.reset_progress()
        self.host_window.wm_deiconify()


__all__ = ["UpdateActionMode", "UpdatePresentationController"]
