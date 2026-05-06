import allure
import pytest
from assertpy import assert_that
from config.settings import Settings
from constants.extension import INVALID_EXTENSION_API_KEY
from core.testing_utils.visual_regression import assert_locator_matches_snapshot
from pages.blocked_page import BlockedPage
from pages.genai_page import GenAIPage


@pytest.mark.ui
@pytest.mark.smoke
@pytest.mark.allowed
@allure.title("Accessing allowed ChatGPT URL expects successful access")
def test_accessing_allowed_chatgpt_url_expects_successful_access(genai_page: GenAIPage, settings: Settings) -> None:
    with allure.step("Navigate to the allowed ChatGPT application"):
        genai_page.open_allowed_genai_application()

    with allure.step("Validate access is allowed and the configured URL is correct"):
        genai_page.assert_navigation_started_for("chatgpt.com")
        genai_page.assert_allowed_access_loaded_successfully()
        assert_that(genai_page.current_url()).described_as(
            "allowed ChatGPT URL after navigation"
        ).contains("chatgpt.com")
        assert_that(settings.allowed_url).described_as("configured allowed URL").contains("chatgpt.com")


@pytest.mark.ui
@pytest.mark.smoke
@pytest.mark.blocked
@allure.title("Accessing blocked Gemini URL expects access denied page")
def test_accessing_blocked_gemini_url_expects_access_denied_page(genai_page: GenAIPage, blocked_page: BlockedPage) -> None:
    with allure.step("Navigate to the blocked Gemini application"):
        genai_page.open_blocked_genai_application()

    with allure.step("Validate the access denied page is rendered"):
        blocked_page.assert_access_denied_page_is_displayed(verify_visual=True)


@pytest.mark.ui
@pytest.mark.blocked
@allure.title("Accessing configured blocked URL expects access denied page")
def test_accessing_configured_blocked_url_expects_access_denied_page(
    genai_page: GenAIPage, blocked_page: BlockedPage, settings: Settings) -> None:
    with allure.step("Navigate to the configured blocked URL"):
        genai_page.open_blocked_genai_application()

    with allure.step("Validate the configured blocked URL is enforced"):
        blocked_page.assert_access_denied_page_is_displayed()
        assert_that(settings.blocked_url).described_as("configured blocked URL").contains("gemini.google.com")


@pytest.mark.ui
@pytest.mark.blocked
@pytest.mark.visual
@allure.title("Accessing blocked Gemini URL expects blocked page visual layout")
def test_accessing_blocked_gemini_url_expects_blocked_page_visual_layout(
    genai_page: GenAIPage, blocked_page: BlockedPage, blocked_modal_snapshot_path, settings: Settings) -> None:
    with allure.step("Navigate to the blocked Gemini application"):
        genai_page.open_blocked_genai_application()

    with allure.step("Validate the blocked page layout and snapshot baseline"):
        blocked_page.assert_access_denied_page_is_displayed(verify_visual=True)
        blocked_page.assert_modal_layout_is_centered()
        assert_locator_matches_snapshot(
            locator=blocked_page.modal_frame,
            baseline_path=blocked_modal_snapshot_path,
            actual_path=settings.visual_artifacts_dir / "gemini-blocked-modal.actual.png",
            diff_path=settings.visual_artifacts_dir / "gemini-blocked-modal.diff.png",
            max_diff_pixels=settings.visual_max_diff_pixels,
            update_baseline=settings.update_visual_baselines,
        )


@pytest.mark.ui
@pytest.mark.blocked
@allure.title("Refreshing blocked Gemini URL expects access denied page to persist")
def test_refreshing_blocked_gemini_url_expects_access_denied_page_to_persist(genai_page: GenAIPage, blocked_page: BlockedPage) -> None:
    with allure.step("Navigate to the blocked Gemini application"):
        genai_page.open_blocked_genai_application()

    with allure.step("Validate the access denied page before refresh"):
        blocked_page.assert_access_denied_page_is_displayed()

    with allure.step("Refresh the blocked page and validate enforcement persists"):
        genai_page.reload_current_page()
        blocked_page.assert_access_denied_page_is_displayed()


@pytest.mark.ui
@pytest.mark.blocked
@allure.title("Opening blocked Gemini URL in new tab expects access denied page")
def test_opening_blocked_gemini_url_in_new_tab_expects_access_denied_page(secondary_page, settings: Settings) -> None:
    secondary_tab_genai_page = GenAIPage(secondary_page, settings)
    secondary_tab_blocked_page = BlockedPage(secondary_page, settings)

    with allure.step("Open the blocked Gemini application in a fresh tab"):
        secondary_tab_genai_page.open_blocked_genai_application()

    with allure.step("Validate the access denied page is still enforced in the new tab"):
        secondary_tab_blocked_page.assert_access_denied_page_is_displayed()


@pytest.mark.ui
@allure.title("Accessing blocked Gemini URL with invalid extension API key expects no policy enforcement")
def test_accessing_blocked_gemini_url_with_invalid_extension_api_key_expects_no_policy_enforcement(
    genai_page: GenAIPage, invalid_extension_api_key_configuration: str) -> None:
    with allure.step("Navigate to the blocked Gemini application with an invalid API key configured"):
        genai_page.open_blocked_genai_application()

    with allure.step("Validate policy enforcement is not active with the invalid API key"):
        genai_page.assert_access_remains_available_for("gemini.google.com")
        assert_that(invalid_extension_api_key_configuration).described_as(
            "invalid extension API key used for negative test").is_equal_to(INVALID_EXTENSION_API_KEY)
