from dataclasses import dataclass
from pathlib import Path

import allure
from assertpy import assert_that
from PIL import Image, ImageChops
from playwright.sync_api import Locator

from core.reporting import attach_file, attach_text


@dataclass
class VisualComparisonResult:
    different_pixels: int
    width: int
    height: int


def assert_locator_matches_snapshot(
    locator: Locator,
    baseline_path: Path,
    actual_path: Path,
    diff_path: Path,
    max_diff_pixels: int = 0,
    update_baseline: bool = False,
) -> None:
    actual_path.parent.mkdir(parents=True, exist_ok=True)
    diff_path.parent.mkdir(parents=True, exist_ok=True)
    baseline_path.parent.mkdir(parents=True, exist_ok=True)

    locator.screenshot(path=str(actual_path))

    if update_baseline or not baseline_path.exists():
        baseline_path.write_bytes(actual_path.read_bytes())
        attach_text("visual-baseline-updated", str(baseline_path))
        attach_file("visual-actual", actual_path, allure.attachment_type.PNG)
        return

    result = _compare_images(baseline_path, actual_path, diff_path)
    attach_file("visual-baseline", baseline_path, allure.attachment_type.PNG)
    attach_file("visual-actual", actual_path, allure.attachment_type.PNG)
    attach_file("visual-diff", diff_path, allure.attachment_type.PNG)
    attach_text(
        "visual-comparison",
        f"different_pixels={result.different_pixels}, size={result.width}x{result.height}, threshold={max_diff_pixels}",
    )
    assert_that(result.different_pixels).described_as(
        f"visual regression pixel diff for {baseline_path.name}"
    ).is_less_than_or_equal_to(max_diff_pixels)


def _compare_images(
    baseline_path: Path,
    actual_path: Path,
    diff_path: Path,
) -> VisualComparisonResult:
    baseline = Image.open(baseline_path).convert("RGBA")
    actual = Image.open(actual_path).convert("RGBA")

    assert_that(actual.size).described_as(
        f"visual snapshot size for {baseline_path.name}"
    ).is_equal_to(baseline.size)

    diff = ImageChops.difference(baseline, actual)
    mask = diff.convert("L").point(lambda value: 255 if value else 0)
    different_pixels = mask.histogram()[255]
    diff.save(diff_path)
    return VisualComparisonResult(
        different_pixels=different_pixels,
        width=baseline.size[0],
        height=baseline.size[1],
    )
