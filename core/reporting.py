import json
from pathlib import Path

import allure


def attach_text(name: str, text: str) -> None:
    allure.attach(text, name=name, attachment_type=allure.attachment_type.TEXT)


def attach_json(name: str, payload: object) -> None:
    allure.attach(
        json.dumps(payload, indent=2, sort_keys=True, default=str),
        name=name,
        attachment_type=allure.attachment_type.JSON,
    )


def attach_file(
    name: str,
    path: Path,
    attachment_type: allure.attachment_type = allure.attachment_type.TEXT,
) -> None:
    allure.attach.file(str(path), name=name, attachment_type=attachment_type)


def write_allure_environment(results_dir: Path, values: dict[str, str]) -> None:
    results_dir.mkdir(parents=True, exist_ok=True)
    environment_file = results_dir / "environment.properties"
    environment_file.write_text(
        "\n".join(f"{key}={value}" for key, value in sorted(values.items())),
        encoding="utf-8",
    )
