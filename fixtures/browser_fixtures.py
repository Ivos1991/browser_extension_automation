from pathlib import Path
from typing import Any

import pytest
from playwright.sync_api import BrowserContext, Page, Playwright, sync_playwright

from config.settings import Settings
from core.browser_factory import BrowserFactory
from core.exceptions import ExtensionConfigurationError
from core.reporting import attach_text
from core.testing_utils.evidence import (
    should_attach_test_evidence,
    should_capture_extension_logs,
    should_capture_trace,
    should_record_video,
)
from core.testing_utils.playwright_artifacts import capture_page_screenshot
from pages.extension_popup_page import ExtensionPopupPage


@pytest.fixture(scope="session")
def playwright_instance() -> Playwright:
    with sync_playwright() as playwright:
        yield playwright


@pytest.fixture(scope="session")
def browser_context(request: pytest.FixtureRequest, settings: Settings, playwright_instance, logger) -> BrowserContext:
    settings.playwright_output_dir.mkdir(parents=True, exist_ok=True)
    collect_all_evidence_requested = bool(request.node.get_closest_marker("collect_all_evidence"))
    if should_record_video(settings.browser_evidence_mode, collect_all_evidence_requested):
        settings.videos_dir.mkdir(parents=True, exist_ok=True)
    if should_capture_trace(settings.browser_evidence_mode, collect_all_evidence_requested):
        settings.traces_dir.mkdir(parents=True, exist_ok=True)
    factory = BrowserFactory(
        playwright_instance,
        settings,
        logger,
        collect_all_evidence_requested=collect_all_evidence_requested,
    )
    try:
        context = factory.launch()
    except ExtensionConfigurationError as error:
        pytest.skip(str(error))
    try:
        yield context
    finally:
        context.close()
        factory.cleanup()


@pytest.fixture(scope="function")
def page(request: pytest.FixtureRequest, browser_context: BrowserContext, settings: Settings) -> Page:
    collect_all = bool(request.node.get_closest_marker("collect_all_evidence"))
    enable_trace = should_capture_trace(settings.browser_evidence_mode, collect_all)
    resolved_extension_id = request.getfixturevalue("extension_id")
    if enable_trace:
        browser_context.tracing.start(screenshots=True, snapshots=True, sources=True)
    page = browser_context.new_page()
    page.set_default_timeout(settings.expect_timeout_ms)
    page.set_default_navigation_timeout(settings.page_load_timeout_ms)
    yield page

    trace_path: Path | None = None
    if enable_trace:
        trace_path = settings.traces_dir / f"{request.node.name}.zip"
        try:
            browser_context.tracing.stop(path=str(trace_path))
        except Exception:
            trace_path = None

    report = getattr(request.node, "rep_call", None)
    test_failed = bool(report and report.failed)
    should_attach = should_attach_test_evidence(
        settings.browser_evidence_mode,
        collect_all,
        test_failed,
    )

    page_url: str | None = None
    evidence_paths: list[Path] = []

    if should_attach:
        screenshot_path = settings.screenshots_dir / f"{request.node.name}.png"
        capture_page_screenshot(page, screenshot_path)
        page_url = page.url
        if screenshot_path.exists():
            evidence_paths.append(screenshot_path)

    if settings.extension_logs_enabled and should_capture_extension_logs(
        settings.browser_evidence_mode,
        collect_all,
        test_failed,
    ):
        log_path = _download_extension_logs(
            browser_context=browser_context,
            settings=settings,
            extension_id=resolved_extension_id,
            artifact_name=request.node.name,
        )
        if log_path is not None and log_path.exists():
            evidence_paths.append(log_path)

    video = page.video
    page.close()
    video_path = _resolve_video_path(video)

    if should_attach:
        evidence_paths.extend(
            path for path in [trace_path, video_path] if isinstance(path, Path) and path.exists()
        )

    setattr(request.node, "_allure_evidence_paths", evidence_paths)
    setattr(request.node, "_allure_evidence_page_url", page_url)


@pytest.fixture(scope="session")
def extension_id(browser_context: BrowserContext) -> str:
    attach_text("extension-service-workers", str(len(browser_context.service_workers)))
    resolved_extension_id = _get_extension_id(browser_context)
    attach_text("extension-id", resolved_extension_id)
    return resolved_extension_id


def _get_extension_id(browser_context: BrowserContext) -> str:
    service_workers = browser_context.service_workers
    service_worker = service_workers[0] if service_workers else browser_context.wait_for_event("serviceworker")
    extension_id = _extract_extension_id(service_worker.url)
    if not extension_id:
        raise RuntimeError(f"Could not determine extension id from service worker URL: {service_worker.url}")
    return extension_id


def _extract_extension_id(service_worker_url: str) -> str | None:
    prefix = "chrome-extension://"
    if not service_worker_url.startswith(prefix):
        return None
    return service_worker_url.removeprefix(prefix).split("/", maxsplit=1)[0]


def _resolve_video_path(video: Any) -> Path | None:
    if video is None:
        return None
    try:
        video_path = video.path()
    except Exception:
        return None
    return Path(video_path)


def _download_extension_logs(
    browser_context: BrowserContext,
    settings: Settings,
    extension_id: str,
    artifact_name: str,
) -> Path | None:
    log_page = browser_context.new_page()
    log_page.set_default_timeout(settings.expect_timeout_ms)
    log_page.set_default_navigation_timeout(settings.page_load_timeout_ms)
    try:
        popup_page = ExtensionPopupPage(log_page, settings)
        popup_page.open(extension_id)
        return popup_page.download_logs(settings.extension_logs_dir, artifact_name)
    except Exception as error:
        attach_text("extension-log-capture", f"Extension log capture failed: {error}")
        return None
    finally:
        log_page.close()
