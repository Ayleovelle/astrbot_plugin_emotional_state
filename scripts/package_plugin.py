from __future__ import annotations

import argparse
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN_NAME = "astrbot_plugin_qq_voice_call"
INCLUDE_ROOT_FILES = {
    "__init__.py",
    "main.py",
    "call_session.py",
    "doubao_realtime_client.py",
    "napcat_call_adapter.py",
    "summary.py",
    "sylanne_bridge.py",
    "metadata.yaml",
    "README.md",
    "requirements.txt",
    "_conf_schema.json",
}
INCLUDE_DIRS = {"docs"}
EXCLUDED_PARTS = {".git", "__pycache__", ".pytest_cache", "dist", "output", "tests", "scripts"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo"}


def should_include(path: Path) -> bool:
    relative = path.relative_to(ROOT)
    if set(relative.parts) & EXCLUDED_PARTS:
        return False
    if path.suffix in EXCLUDED_SUFFIXES:
        return False
    if len(relative.parts) == 1:
        return relative.name in INCLUDE_ROOT_FILES
    return relative.parts[0] in INCLUDE_DIRS


def collect_files() -> list[Path]:
    return sorted(path for path in ROOT.rglob("*") if path.is_file() and should_include(path))


def build_zip(output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(f"{PLUGIN_NAME}/", "")
        for path in collect_files():
            archive.write(path, f"{PLUGIN_NAME}/{path.relative_to(ROOT).as_posix()}")
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=f"dist/{PLUGIN_NAME}.zip")
    args = parser.parse_args()
    print(build_zip(ROOT / args.output))


if __name__ == "__main__":
    main()
