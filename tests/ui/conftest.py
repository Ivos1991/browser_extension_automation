from pathlib import Path
from time import monotonic
from typing import Callable

import allure
import pytest
from playwright.sync_api import BrowserContext, Error, Page

from config.settings import Settings
from constants.extension import EXTENSION_CONFIGURATION_MESSAGE
from constants.extension import INVALID_EXTENSION_API_DOMAIN, INVALID_EXTENSION_API_KEY
from constants.messages import EXTENSION_CONNECTION_FAILURE_MESSAGE
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

    _wait_for_policy_enforcement(browser_context, settings)


@pytest.fixture(scope="session")
def configure_extension_api(
    browser_context: BrowserContext, extension_id: str, settings: Settings
) -> Callable[[str, str, str, str | None], None]:
    def _configure(
        api_domain: str,
        api_key: str,
        expected_message: str,
        expected_alert_message: str | None = None,
    ) -> None:
        page = browser_context.new_page()
        try:
            with allure.step("Configure the browser extension with custom API credentials"):
                popup_page = ExtensionPopupPage(page, settings)
                popup_page.open(extension_id)
                popup_page.configure_api_access(
                    api_domain=api_domain,
                    api_key=api_key,
                    expected_message=expected_message,
                    expected_alert_message=expected_alert_message,
                )
        finally:
            page.close()

    return _configure


@pytest.fixture
def invalid_extension_api_key_configuration(
    configure_extension_api: Callable[[str, str, str, str | None], None], settings: Settings, browser_context: BrowserContext
):
    configure_extension_api(
        settings.extension_api_domain,
        INVALID_EXTENSION_API_KEY,
        EXTENSION_CONFIGURATION_MESSAGE,
        EXTENSION_CONNECTION_FAILURE_MESSAGE,
    )
    yield INVALID_EXTENSION_API_KEY
    configure_extension_api(
        settings.extension_api_domain,
        settings.extension_api_key,
        EXTENSION_CONFIGURATION_MESSAGE,
    )
    _wait_for_policy_enforcement(browser_context, settings)


@pytest.fixture
def invalid_extension_api_domain_configuration(
    configure_extension_api: Callable[[str, str, str, str | None], None], settings: Settings, browser_context: BrowserContext
):
    configure_extension_api(
        INVALID_EXTENSION_API_DOMAIN,
        settings.extension_api_key,
        EXTENSION_CONFIGURATION_MESSAGE,
        EXTENSION_CONNECTION_FAILURE_MESSAGE,
    )
    yield INVALID_EXTENSION_API_DOMAIN
    configure_extension_api(
        settings.extension_api_domain,
        settings.extension_api_key,
        EXTENSION_CONFIGURATION_MESSAGE,
    )
    _wait_for_policy_enforcement(browser_context, settings)


@pytest.fixture
def missing_extension_configuration(
    configure_extension_api: Callable[[str, str, str, str | None], None], settings: Settings, browser_context: BrowserContext
):
    configure_extension_api("", "", EXTENSION_CONFIGURATION_MESSAGE, EXTENSION_CONNECTION_FAILURE_MESSAGE)
    yield "missing-extension-configuration"
    configure_extension_api(
        settings.extension_api_domain,
        settings.extension_api_key,
        EXTENSION_CONFIGURATION_MESSAGE,
    )
    _wait_for_policy_enforcement(browser_context, settings)


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


def _wait_for_policy_enforcement(browser_context: BrowserContext, settings: Settings) -> None:
    probe_page = browser_context.new_page()
    probe_page.set_default_timeout(settings.expect_timeout_ms)
    probe_page.set_default_navigation_timeout(settings.page_load_timeout_ms)
    deadline = monotonic() + (settings.policy_sync_timeout_ms / 1000)
    last_url = ""
    last_error = ""

    try:
        with allure.step("Wait for extension policy enforcement to become active"):
            while monotonic() < deadline:
                try:
                    probe_page.goto(settings.blocked_url, wait_until="domcontentloaded")
                    last_error = ""
                except Error as error:
                    last_error = str(error)
                probe_page.wait_for_timeout(settings.policy_sync_poll_interval_ms)
                last_url = probe_page.url
                if last_url.startswith("chrome-extension://") and "pageOverlay.html" in last_url:
                    return
            pytest.fail(
                "Extension policy enforcement did not become active within "
                f"{settings.policy_sync_timeout_ms}ms. Last observed URL: {last_url or settings.blocked_url}. "
                f"Last navigation error: {last_error or 'n/a'}"
            )
    finally:
        probe_page.close()
