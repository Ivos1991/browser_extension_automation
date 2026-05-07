from pathlib import Path

import allure
from playwright.sync_api import Page

from core.reporting import attach_file, attach_text


def attachment_type_for_path(path: Path):
    suffix = path.suffix.lower()
    if suffix == ".png":
        return allure.attachment_type.PNG
    if suffix == ".webm":
        return allure.attachment_type.WEBM
    if suffix == ".zip":
        return "application/zip"
    return allure.attachment_type.TEXT


def capture_page_screenshot(page: Page, screenshot_path: Path) -> None:
    if page.is_closed():
        return
    screenshot_path.parent.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(screenshot_path), full_page=True)


def attach_test_evidence(paths: list[Path], page_url: str | None, test_failed: bool) -> None:
    if page_url:
        attach_text("page-url", page_url)

    for path in sorted(paths):
        if not path.exists() or not path.is_file():
            continue
        attach_file(_attachment_name_for_path(path, test_failed), path, attachment_type_for_path(path))


def _attachment_name_for_path(path: Path, test_failed: bool) -> str:
    suffix = path.suffix.lower()
    if suffix == ".png":
        return "failure-screenshot" if test_failed else "page-screenshot"
    if suffix == ".zip":
        return "playwright-trace"
    if suffix == ".webm":
        return "playwright-video"
    return path.name
