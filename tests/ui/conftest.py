from pathlib import Path
from typing import Callable

import allure
import pytest
from playwright.sync_api import BrowserContext, Page

from config.settings import Settings
from constants.extension import INVALID_EXTENSION_API_KEY
from pages.blocked_page import BlockedPage
from pages.extension_popup_page import ExtensionPopupPage
from pages.genai_page import GenAIPage


@pytest.fixture(scope="session", autouse=True)
def configured_extension(browser_context: BrowserContext, extension_id: str, settings: Settings) -> None:
    page = browser_context.new_page()
    try:
        with allure.step("Configure the browser extension with the default API credentials"):
            popup_page = ExtensionPopupPage(page, settings)
            popup_page.open(extension_id)
            popup_page.configure_api_access()
    finally:
        page.close()


@pytest.fixture
def configure_extension_api(
    browser_context: BrowserContext, extension_id: str, settings: Settings
) -> Callable[[str, str], None]:
    def _configure(api_domain: str, api_key: str) -> None:
        page = browser_context.new_page()
        try:
            with allure.step("Configure the browser extension with custom API credentials"):
                popup_page = ExtensionPopupPage(page, settings)
                popup_page.open(extension_id)
                popup_page.configure_api_access(api_domain=api_domain, api_key=api_key)
        finally:
            page.close()

    return _configure


@pytest.fixture
def invalid_extension_api_key_configuration(
    configure_extension_api: Callable[[str, str], None], settings: Settings
):
    configure_extension_api(settings.extension_api_domain, INVALID_EXTENSION_API_KEY)
    yield INVALID_EXTENSION_API_KEY
    configure_extension_api(settings.extension_api_domain, settings.extension_api_key)


@pytest.fixture
def genai_page(page, settings: Settings) -> GenAIPage:
    return GenAIPage(page, settings)


@pytest.fixture
def blocked_page(page, settings: Settings) -> BlockedPage:
    return BlockedPage(page, settings)


@pytest.fixture
def secondary_page(browser_context: BrowserContext, settings: Settings) -> Page:
    page = browser_context.new_page()
    page.set_default_timeout(settings.expect_timeout_ms)
    page.set_default_navigation_timeout(settings.page_load_timeout_ms)
    yield page
    page.close()


@pytest.fixture(scope="session")
def blocked_modal_snapshot_path() -> Path:
    return Path("tests/ui/snapshots/gemini-blocked-modal.png")
