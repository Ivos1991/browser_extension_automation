import shutil
from pathlib import Path
from tempfile import mkdtemp

from playwright.sync_api import BrowserContext, Playwright

from config.settings import Settings
from core.exceptions import ExtensionConfigurationError
from core.testing_utils.evidence import should_record_video


class BrowserFactory:
    def __init__(self, playwright: Playwright, settings: Settings, logger, collect_all_evidence_requested: bool = False) -> None:
        self.playwright = playwright
        self.settings = settings
        self.logger = logger
        self.collect_all_evidence_requested = collect_all_evidence_requested
        self._user_data_dir: Path | None = None

    def launch(self) -> BrowserContext:
        extension_path = self._validated_extension_path()
        user_data_dir = Path(mkdtemp(prefix="pw-ext-", dir=str(self.settings.playwright_output_dir)))
        self._user_data_dir = user_data_dir
        self.logger.info("Launching persistent Chromium context with extension: %s", extension_path)

        context = self.playwright.chromium.launch_persistent_context(
            user_data_dir=str(user_data_dir),
            channel=self.settings.browser_channel,
            headless=self.settings.headless,
            slow_mo=self.settings.slow_mo_ms,
            ignore_default_args=["--disable-extensions"],
            args=[
                f"--disable-extensions-except={extension_path}",
                f"--load-extension={extension_path}",
            ],
            viewport={"width": 1600, "height": 1000},
            accept_downloads=False,
            ignore_https_errors=True,
            record_video_dir=(
                str(self.settings.videos_dir)
                if should_record_video(
                    self.settings.browser_evidence_mode,
                    self.collect_all_evidence_requested,
                )
                else None
            ),
        )
        context.set_default_timeout(self.settings.expect_timeout_ms)
        context.set_default_navigation_timeout(self.settings.page_load_timeout_ms)
        return context

    def cleanup(self) -> None:
        if self._user_data_dir and self._user_data_dir.exists():
            shutil.rmtree(self._user_data_dir, ignore_errors=True)

    def _validated_extension_path(self) -> Path:
        extension_path = self.settings.extension_path
        if extension_path is None:
            raise ExtensionConfigurationError(
                "EXTENSION_PATH is not configured. Set it to the unpacked extension directory."
            )
        if not extension_path.exists():
            raise ExtensionConfigurationError(
                f"Configured EXTENSION_PATH does not exist: {extension_path}"
            )
        if not extension_path.is_dir():
            raise ExtensionConfigurationError(
                f"Configured EXTENSION_PATH must be a directory: {extension_path}"
            )
        manifest = extension_path / "manifest.json"
        if not manifest.exists():
            raise ExtensionConfigurationError(
                f"Unpacked extension directory is missing manifest.json: {manifest}"
            )
        return extension_path
