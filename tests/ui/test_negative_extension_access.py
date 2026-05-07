import allure
import pytest
from assertpy import assert_that
from constants.extension import INVALID_EXTENSION_API_DOMAIN, INVALID_EXTENSION_API_KEY
from pages.genai_page import GenAIPage


@pytest.mark.ui
@pytest.mark.negative
class TestNegativeExtensionAccess:
    @allure.title("Accessing blocked Gemini URL with invalid extension API key expects no policy enforcement")
    def test_accessing_blocked_gemini_url_with_invalid_extension_api_key_expects_no_policy_enforcement(
            self, genai_page: GenAIPage, invalid_extension_api_key_configuration: str) -> None:

        with allure.step("Navigate to the blocked Gemini application with an invalid API key configured"):
            genai_page.open_blocked_genai_application()

        with allure.step("Validate policy enforcement is not active with the invalid API key"):
            genai_page.assert_access_remains_available_for("gemini.google.com")
            assert_that(invalid_extension_api_key_configuration).described_as(
                "invalid extension API key used for negative test").is_equal_to(INVALID_EXTENSION_API_KEY)

    @allure.title("Accessing blocked Gemini URL with invalid extension API domain expects no policy enforcement")
    def test_accessing_blocked_gemini_url_with_invalid_extension_api_domain_expects_no_policy_enforcement(
            self, genai_page: GenAIPage, invalid_extension_api_domain_configuration: str) -> None:

        with allure.step("Navigate to the blocked Gemini application with an invalid API domain configured"):
            genai_page.open_blocked_genai_application()

        with allure.step("Validate policy enforcement is not active with the invalid API domain"):
            genai_page.assert_access_remains_available_for("gemini.google.com")
            assert_that(invalid_extension_api_domain_configuration).described_as(
                "invalid extension API domain used for negative test").is_equal_to(INVALID_EXTENSION_API_DOMAIN)

    @allure.title("Accessing blocked Gemini URL with missing extension configuration expects no policy enforcement")
    def test_accessing_blocked_gemini_url_with_missing_extension_configuration_expects_no_policy_enforcement(
            self, genai_page: GenAIPage, missing_extension_configuration: str) -> None:

        with allure.step("Navigate to the blocked Gemini application with missing extension configuration"):
            genai_page.open_blocked_genai_application()

        with allure.step("Validate policy enforcement is not active with missing extension configuration"):
            genai_page.assert_access_remains_available_for("gemini.google.com")
            assert_that(missing_extension_configuration).described_as(
                "missing extension configuration marker").is_equal_to("missing-extension-configuration")
