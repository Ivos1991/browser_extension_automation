import re

from playwright.sync_api import Locator, Page, expect

from core.core_utils.logger import get_logger


class PlaywrightActions:
    def __init__(self, page: Page) -> None:
        self.page = page
        self.logger = get_logger(self.__class__.__name__)

    def navigate(self, url: str, wait_until: str = "domcontentloaded") -> None:
        self.logger.info("Navigate to %s", url)
        self.page.goto(url, wait_until=wait_until)

    def fill(self, locator: Locator, value: str, description: str) -> None:
        self.logger.info("Fill %s", description)
        locator.fill(value)

    def click(self, locator: Locator, description: str) -> None:
        self.logger.info("Click %s", description)
        locator.click()

    def expect_visible(self, locator: Locator, description: str, timeout: int) -> None:
        self.logger.info("Expect visible: %s", description)
        expect(locator, description).to_be_visible(timeout=timeout)

    def expect_hidden(self, locator: Locator, description: str, timeout: int) -> None:
        self.logger.info("Expect hidden: %s", description)
        expect(locator, description).to_be_hidden(timeout=timeout)

    def expect_text(self, locator: Locator, text: str, description: str, timeout: int) -> None:
        self.logger.info("Expect text for %s", description)
        expect(locator, description).to_contain_text(text, timeout=timeout)

    def expect_page_url(self, pattern: str, description: str, timeout: int) -> None:
        self.logger.info("Expect page URL for %s", description)
        expect(self.page, description).to_have_url(re.compile(pattern), timeout=timeout)

    def text_content(self, locator: Locator, description: str, timeout: int) -> str:
        self.expect_visible(locator, description, timeout)
        return locator.inner_text().strip()
