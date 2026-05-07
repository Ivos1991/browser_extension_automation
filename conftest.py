import pytest

from config.settings import Settings
from core.core_utils.logger import configure_logging, get_logger
from core.reporting import write_allure_environment
from core.testing_utils.playwright_artifacts import attach_test_evidence


pytest_plugins = ("fixtures.browser_fixtures",)


@pytest.fixture(scope="session")
def settings() -> Settings:
    return Settings.from_env()


@pytest.fixture(scope="session", autouse=True)
def framework_logging(settings: Settings) -> None:
    configure_logging(settings.log_dir, settings.log_level)


@pytest.fixture(scope="session", autouse=True)
def write_environment_metadata(settings: Settings) -> None:
    write_allure_environment(
        settings.allure_results_dir,
        {
            "target_env": settings.target_env,
            "headless": str(settings.headless).lower(),
            "browser_channel": settings.browser_channel,
            "allowed_url": settings.allowed_url,
            "blocked_url": settings.blocked_url,
            "extension_path": str(settings.extension_path or ""),
            "extension_api_domain": settings.extension_api_domain,
            "browser_evidence_mode": settings.browser_evidence_mode,
            "extension_logs_enabled": str(settings.extension_logs_enabled).lower(),
        },
    )


@pytest.fixture(scope="session")
def logger():
    return get_logger("tests")


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    try:
        Settings.from_env()
    except ValueError as error:
        raise pytest.UsageError(str(error)) from error
    setattr(
        config,
        "_collect_all_evidence_requested",
        any(item.get_closest_marker("collect_all_evidence") for item in items),
    )


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo[object]):
    outcome = yield
    report = outcome.get_result()
    setattr(item, f"rep_{report.when}", report)

    if report.when != "teardown":
        return

    evidence_paths = getattr(item, "_allure_evidence_paths", [])
    page_url = getattr(item, "_allure_evidence_page_url", None)
    test_failed = bool(getattr(item, "rep_call", None) and getattr(item.rep_call, "failed", False))
    if evidence_paths or page_url:
        attach_test_evidence(evidence_paths, page_url, test_failed)
