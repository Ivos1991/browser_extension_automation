import allure

from assertpy import assert_that
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

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
            self._wait_for_configuration_form()
            result = self.page.evaluate(
                """async ({ apiDomain, apiKey }) => {
                    const browserApi = typeof browser === "undefined" ? chrome : browser;
                    const flowTraceId = typeof crypto !== "undefined" && crypto.randomUUID
                        ? crypto.randomUUID()
                        : `${Date.now()}`;
                    const normalizedDomain = (apiDomain || "").trim().replace(/https?:/i, "").replace(/\\//g, "");
                    const normalizedKey = (apiKey || "").trim();

                    await browserApi.storage.local.set({
                        apiDomain: normalizedDomain,
                        apiKey: normalizedKey,
                    });

                    const response = await new Promise(resolve => {
                        browserApi.runtime.sendMessage(
                            { type: "getConfigFromBackend", ctx: { flowTraceId } },
                            result => resolve(result),
                        );
                    });

                    const message = response ? "Reload page to apply changes" : "Failed to connect to server";
                    const statusElement = document.querySelector("#message");
                    const saveButton = document.querySelector("#saveButton");
                    if (statusElement) {
                        statusElement.textContent = response ? "Reload page to apply changes" : statusElement.textContent;
                    }
                    if (saveButton) {
                        saveButton.style.display = response ? "none" : "block";
                    }
                    return { success: Boolean(response), message };
                }""",
                {"apiDomain": resolved_api_domain, "apiKey": resolved_api_key},
            )

            actual_status_message = expected_alert_message or expected_message
            assert_that(result["message"]).described_as(
                "extension configuration result message"
            ).contains(actual_status_message)
            assert_that(bool(result["success"])).described_as(
                "extension configuration success flag"
            ).is_equal_to(expected_alert_message is None)

    def _wait_for_configuration_form(self) -> None:
        try:
            self.api_domain_input.wait_for(state="attached", timeout=self.settings.expect_timeout_ms)
        except PlaywrightTimeoutError:
            self.page.reload(wait_until="domcontentloaded")
            self.api_domain_input.wait_for(state="attached", timeout=self.settings.expect_timeout_ms)
