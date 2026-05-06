import allure

from assertpy import assert_that

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
    ) -> None:
        with allure.step("Configure extension API access"):
            resolved_api_domain = api_domain or self.settings.extension_api_domain
            resolved_api_key = api_key or self.settings.extension_api_key
            self.fill(self.api_domain_input, resolved_api_domain, "extension API domain")
            self.fill(self.api_key_input, resolved_api_key, "extension API key")
            self.click(self.save_button, "extension save button")
            message_text = (self.status_message.text_content() or "").strip()
            assert_that(message_text).described_as(
                "extension popup save confirmation message"
            ).contains(EXTENSION_CONFIGURATION_MESSAGE)
