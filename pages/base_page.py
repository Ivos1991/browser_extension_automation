import allure
from playwright.sync_api import Page

from actions.playwright_actions import PlaywrightActions
from config.settings import Settings


class BasePage(PlaywrightActions):
    def __init__(self, page: Page, settings: Settings) -> None:
        super().__init__(page)
        self.settings = settings

    def open(self, url: str) -> None:
        with allure.step(f"Open {url}"):
            self.navigate(url)

    def wait_for_url_contains(self, value: str, description: str) -> None:
        self.expect_page_url(
            pattern=fr".*{value}.*",
            description=description,
            timeout=self.settings.page_load_timeout_ms,
        )

    def expect_not_on_block_page(self) -> None:
        self.expect_hidden(
            self.page.get_by_text("Access Denied", exact=False),
            "blocked page heading",
            timeout=self.settings.expect_timeout_ms,
        )
