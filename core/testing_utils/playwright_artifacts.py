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


def attach_files(paths: list[Path]) -> None:
    for path in sorted(paths):
        if path.exists() and path.is_file():
            attach_file(path.name, path, attachment_type_for_path(path))


def attach_page_screenshot(page: Page, screenshot_path: Path, name: str = "page-screenshot") -> None:
    if page.is_closed():
        return
    screenshot_path.parent.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(screenshot_path), full_page=True)
    attach_file(name, screenshot_path, allure.attachment_type.PNG)
    attach_text("page-url", page.url)
