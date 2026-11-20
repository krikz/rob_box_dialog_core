"""Тег vX.Y.Z совпадает с version в pyproject.toml (scripts/lint/check_version_tag.py)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_version_tag as guard  # noqa: E402

REPO = Path(__file__).resolve().parents[2]


def test_match_is_ok() -> None:
    code, message = guard.check("v0.7.13", 'name = "x"\nversion = "0.7.13"\n')
    assert code == 0
    assert "OK" in message


def test_v0_7_12_lie_fails() -> None:
    """Факт: тег v0.7.12 объявлял version = \"0.7.11\"."""
    code, message = guard.check("v0.7.12", 'version = "0.7.11"\n')
    assert code == 1
    assert "0.7.11" in message
    assert "0.7.12" in message


@pytest.mark.parametrize(
    "tag,text",
    [
        ("v0.7.9", 'version = "0.7.8"\n'),
        ("v0.7.1", 'version = "0.7.0"\n'),
        ("v0.7.11", 'version = "0.7.11"\nversion = "9.9.9"\n'),
        ("v0.7.11", 'name = "rob-box-dialog-core"\n'),
    ],
)
def test_mismatch_or_missing_fails(tag: str, text: str) -> None:
    assert guard.check(tag, text)[0] == 1


def test_non_release_tag_is_skipped() -> None:
    assert guard.check("not-a-release", 'version = "0.0.1"\n')[0] == 0


def test_self_check_cli_exits_zero() -> None:
    script = REPO / "scripts" / "lint" / "check_version_tag.py"
    done = subprocess.run([sys.executable, str(script), "--self-check"], capture_output=True, text=True, check=False)
    assert done.returncode == 0, done.stdout + done.stderr
    # Строка случая начинается с OK; FAIL внутри — ожидаемый текст проверки, не провал случая.
    lines = [line for line in done.stdout.splitlines() if line.strip()]
    assert lines
    assert all(line.startswith("OK:") for line in lines), done.stdout


def test_live_pyproject_has_one_version_matching_its_own_tag() -> None:
    text = (REPO / "pyproject.toml").read_text(encoding="utf-8")
    version = guard.declared_version(text)
    assert version
    assert guard.check(f"v{version}", text)[0] == 0
