import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from constants.evidence import (
    EVIDENCE_MODE_FAILURE_ONLY,
    LEGACY_EVIDENCE_MODE_MAP,
    VALID_EVIDENCE_MODES,
)
from constants.framework import DEFAULT_EXTENSION_DIR


def _to_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _to_optional_path(value: str | None) -> Path | None:
    if not value:
        return None
    return Path(value).expanduser().resolve()


@dataclass
class Settings:
    target_env: str
    headless: bool
    slow_mo_ms: int
    browser_channel: str
    browser_evidence_mode: str
    page_load_timeout_ms: int
    expect_timeout_ms: int
    artifact_dir: Path
    log_level: str
    update_visual_baselines: bool
    visual_max_diff_pixels: int
    allowed_url: str
    blocked_url: str
    extension_path: Path | None
    extension_api_key: str
    extension_api_domain: str
    policy_sync_timeout_ms: int
    policy_sync_poll_interval_ms: int

    @property
    def allure_results_dir(self) -> Path:
        return self.artifact_dir / "allure-results"

    @property
    def log_dir(self) -> Path:
        return self.artifact_dir / "logs"

    @property
    def playwright_output_dir(self) -> Path:
        return self.artifact_dir / "playwright"

    @property
    def traces_dir(self) -> Path:
        return self.playwright_output_dir / "traces"

    @property
    def videos_dir(self) -> Path:
        return self.playwright_output_dir / "videos"

    @property
    def screenshots_dir(self) -> Path:
        return self.artifact_dir / "screenshots"

    @property
    def visual_artifacts_dir(self) -> Path:
        return self.artifact_dir / "visual"

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()
        artifact_dir = Path(os.getenv("ARTIFACT_DIR", "artifacts")).resolve()
        return cls(
            target_env=os.getenv("TARGET_ENV", "local").strip().lower(),
            headless=_to_bool(os.getenv("HEADLESS"), True),
            slow_mo_ms=int(os.getenv("SLOW_MO_MS", "0")),
            browser_channel=os.getenv("BROWSER_CHANNEL", "chromium").strip(),
            browser_evidence_mode=_evidence_mode_from_env(),
            page_load_timeout_ms=int(os.getenv("PAGE_LOAD_TIMEOUT_MS", "30000")),
            expect_timeout_ms=int(os.getenv("EXPECT_TIMEOUT_MS", "10000")),
            artifact_dir=artifact_dir,
            log_level=os.getenv("LOG_LEVEL", "INFO").strip().upper(),
            update_visual_baselines=_to_bool(os.getenv("UPDATE_VISUAL_BASELINES"), False),
            visual_max_diff_pixels=int(os.getenv("VISUAL_MAX_DIFF_PIXELS", "0")),
            allowed_url=os.getenv("ALLOWED_URL", "https://chatgpt.com").strip(),
            blocked_url=os.getenv("BLOCKED_URL", "https://gemini.google.com").strip(),
            extension_path=_to_optional_path(os.getenv("EXTENSION_PATH", str(DEFAULT_EXTENSION_DIR))),
            extension_api_key=os.getenv(
                "EXTENSION_API_KEY",
                "13793400-107d-406b-b9ed-5cd7bb22be98",
            ).strip(),
            extension_api_domain=os.getenv("EXTENSION_API_DOMAIN", "eu.prompt.security").strip(),
            policy_sync_timeout_ms=int(os.getenv("POLICY_SYNC_TIMEOUT_MS", "90000")),
            policy_sync_poll_interval_ms=int(os.getenv("POLICY_SYNC_POLL_INTERVAL_MS", "2000")),
        )


def _evidence_mode_from_env() -> str:
    raw_mode = os.getenv("BROWSER_EVIDENCE_MODE", EVIDENCE_MODE_FAILURE_ONLY).strip().lower()
    normalized_mode = LEGACY_EVIDENCE_MODE_MAP.get(raw_mode, raw_mode)
    if normalized_mode not in VALID_EVIDENCE_MODES:
        raise ValueError(
            "BROWSER_EVIDENCE_MODE must be one of: "
            f"{', '.join(sorted(VALID_EVIDENCE_MODES | set(LEGACY_EVIDENCE_MODE_MAP)))}"
        )
    return normalized_mode
