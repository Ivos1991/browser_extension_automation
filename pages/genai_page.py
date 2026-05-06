import allure

from assertpy import assert_that

from pages.base_page import BasePage


class GenAIPage(BasePage):
    def open_allowed_genai_application(self) -> None:
        self.open(self.settings.allowed_url)

    def open_blocked_genai_application(self) -> None:
        self.open(self.settings.blocked_url)

    def current_url(self) -> str:
        return self.page.url

    def reload_current_page(self) -> None:
        with allure.step("Reload current page"):
            self.page.reload(wait_until="domcontentloaded")

    def assert_navigation_started_for(self, expected_url_fragment: str) -> None:
        with allure.step(f"Validate navigation toward {expected_url_fragment}"):
            self.wait_for_url_contains(
                expected_url_fragment,
                f"navigation URL containing {expected_url_fragment}",
            )

    def assert_allowed_access_loaded_successfully(self) -> None:
        with allure.step("Validate allowed site access"):
            self.wait_for_url_contains("chatgpt.com", "allowed ChatGPT URL")
            self.expect_not_on_block_page()
            assert_that(self.current_url()).described_as(
                "allowed site current URL"
            ).contains("chatgpt.com")

    def assert_access_remains_available_for(self, expected_url_fragment: str) -> None:
        with allure.step(f"Validate access remains available for {expected_url_fragment}"):
            self.wait_for_url_contains(
                expected_url_fragment,
                f"current URL containing {expected_url_fragment}",
            )
            self.expect_not_on_block_page()
            assert_that(self.current_url()).described_as(
                "current URL with access still available"
            ).contains(expected_url_fragment)
