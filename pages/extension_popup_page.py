import allure

from assertpy import assert_that
from playwright.sync_api import Dialog

from constants.extension import EXTENSION_CONFIGURATION_MESSAGE, EXTENSION_POPUP_PATH
from pages.base_page import BasePage


class ExtensionPopupPage(BasePage):
    @property
    def api_domain_input(self):
        return self.page.locator("#apiDomain")

    @property
    def api_key_input(self):
        return self.page.locator("#apiKey")

    @property
    def save_button(self):
        return self.page.locator("#saveButton")

    @property
    def status_message(self):
        return self.page.locator("#message")

    def open(self, extension_id: str) -> None:
        super().open(f"chrome-extension://{extension_id}/{EXTENSION_POPUP_PATH}")

    def configure_api_access(
        self,
        api_domain: str | None = None,
        api_key: str | None = None,
        expected_message: str = EXTENSION_CONFIGURATION_MESSAGE,
        expected_alert_message: str | None = None,
    ) -> None:
        with allure.step("Configure extension API access"):
            resolved_api_domain = self.settings.extension_api_domain if api_domain is None else api_domain
            resolved_api_key = self.settings.extension_api_key if api_key is None else api_key
            self.fill(self.api_domain_input, resolved_api_domain, "extension API domain")
            self.fill(self.api_key_input, resolved_api_key, "extension API key")
            if expected_alert_message:
                with self.page.expect_event("dialog", timeout=self.settings.expect_timeout_ms) as dialog_info:
                    self.click(self.save_button, "extension save button")
                self._assert_dialog_message(dialog_info.value, expected_alert_message)
            else:
                self.click(self.save_button, "extension save button")
            self.expect_text(
                self.status_message,
                expected_message,
                "extension popup status message",
                self.settings.expect_timeout_ms,
            )
            message_text = (self.status_message.text_content() or "").strip()
            assert_that(message_text).described_as(
                "extension popup status message"
            ).contains(expected_message)

    @staticmethod
    def _assert_dialog_message(dialog: Dialog, expected_alert_message: str) -> None:
        actual_message = dialog.message.strip()
        dialog.accept()
        assert_that(actual_message).described_as(
            "extension popup alert message"
        ).contains(expected_alert_message)
