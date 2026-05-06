import allure

from assertpy import assert_that

from constants.extension import EXTENSION_OVERLAY_PATH_PATTERN
from constants.messages import (
    ACCESS_DENIED_MESSAGE,
    ACCESS_DENIED_MESSAGE_PARTIAL,
    ACCESS_DENIED_TITLE,
    BLOCKED_PAGE_GUIDELINES_TEXT,
)
from pages.base_page import BasePage


class BlockedPage(BasePage):
    @property
    def modal_frame(self):
        return self.page.locator(".container:visible, .frame:visible").first

    @property
    def denied_title(self):
        return self.page.get_by_text(ACCESS_DENIED_TITLE, exact=False)

    @property
    def denied_message(self):
        return self.page.get_by_text(ACCESS_DENIED_MESSAGE_PARTIAL, exact=False)

    @property
    def guidelines_message(self):
        return self.page.get_by_text(BLOCKED_PAGE_GUIDELINES_TEXT, exact=False)

    @property
    def blocked_visual(self):
        return self.page.locator("img:visible, svg:visible").first

    def title_text(self) -> str:
        return self.text_content(
            self.denied_title,
            "blocked page title",
            self.settings.page_load_timeout_ms,
        )

    def message_text(self) -> str:
        return self.text_content(
            self.denied_message,
            "blocked page message",
            self.settings.page_load_timeout_ms,
        )

    def assert_access_denied_page_is_displayed(self, verify_visual: bool = False) -> None:
        with allure.step("Validate blocked access page"):
            self.expect_page_url(
                EXTENSION_OVERLAY_PATH_PATTERN,
                "blocked page overlay URL",
                self.settings.page_load_timeout_ms,
            )
            assert_that(self.title_text()).described_as(
                "blocked page title text"
            ).is_equal_to(ACCESS_DENIED_TITLE)
            assert_that(self.message_text()).described_as(
                "blocked page message text"
            ).contains(ACCESS_DENIED_MESSAGE_PARTIAL).contains(ACCESS_DENIED_MESSAGE)
            assert_that(
                self.text_content(
                    self.guidelines_message,
                    "blocked page guidelines message",
                    self.settings.page_load_timeout_ms,
                )
            ).described_as("blocked page guidelines text").contains("guidelines")
            if verify_visual and self.blocked_visual.count() > 0:
                self.expect_visible(
                    self.blocked_visual,
                    "blocked page visual asset",
                    self.settings.page_load_timeout_ms,
                )

    def assert_modal_layout_is_centered(self, tolerance_pixels: int = 30) -> None:
        with allure.step("Validate blocked modal layout position"):
            box = self.modal_frame.bounding_box()
            viewport = self.page.viewport_size

            assert_that(box).described_as("blocked modal bounding box").is_not_none()
            assert_that(viewport).described_as("browser viewport size").is_not_none()

            center_x = box["x"] + (box["width"] / 2)  # type: ignore[index]
            center_y = box["y"] + (box["height"] / 2)  # type: ignore[index]
            expected_x = viewport["width"] / 2  # type: ignore[index]
            expected_y = viewport["height"] / 2  # type: ignore[index]

            assert_that(abs(center_x - expected_x)).described_as(
                "blocked modal horizontal center delta"
            ).is_less_than_or_equal_to(tolerance_pixels)
            assert_that(abs(center_y - expected_y)).described_as(
                "blocked modal vertical center delta"
            ).is_less_than_or_equal_to(tolerance_pixels)
