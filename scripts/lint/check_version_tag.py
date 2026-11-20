#!/usr/bin/env python3
"""Гард: тег ``vX.Y.Z`` совпадает со строкой ``version`` в корневом ``pyproject.toml``.

Паспорт пакета (``pip show``, ``importlib.metadata.version``) берётся из ``pyproject.toml``, а не из имени тега.
Тег ``v0.7.12`` вышел со строкой ``0.7.11`` — образ ставил код тега, а версия пакета врала. То же было у
``v0.7.1`` (строка ``0.7.0``) и ``v0.7.9`` (строка ``0.7.8``).

На push тега CI передаёт имя тега (``--tag``). Без тега гард молчит: ветка и PR версию с тегом не сверяют,
тег ставит человек уже после мёржа. ``--self-check`` гоняет вшитые случаи и не читает репозиторий.

    python scripts/lint/check_version_tag.py --tag v0.7.13
    python scripts/lint/check_version_tag.py --self-check
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PYPROJECT = REPO / "pyproject.toml"

_TAG = re.compile(r"^v(\d+\.\d+\.\d+)$")
_VERSION_LINE = re.compile(r'^version\s*=\s*"(\d+\.\d+\.\d+)"\s*$', re.MULTILINE)


def declared_version(text: str) -> str:
    """Единственная строка ``version = "X.Y.Z"`` в ``[project]``. Пусто — строки нет или их несколько."""
    found = _VERSION_LINE.findall(text)
    if len(found) != 1:
        return ""
    return found[0]


def tag_version(tag: str) -> str:
    """``vX.Y.Z`` → ``X.Y.Z``. Иное имя тега — пусто (гард его не судит)."""
    match = _TAG.match(tag.strip())
    return match.group(1) if match else ""


def check(tag: str, pyproject_text: str) -> tuple[int, str]:
    """0 — совпало или тег не ``vX.Y.Z``; 1 — паспорт врёт или строки версии нет."""
    expected = tag_version(tag)
    if not expected:
        return 0, f"SKIP: тег {tag!r} не vX.Y.Z, паспорт не сверяю"
    actual = declared_version(pyproject_text)
    if not actual:
        return 1, 'FAIL: в pyproject.toml нет ровно одной строки version = "X.Y.Z"'
    if actual != expected:
        return 1, f'FAIL: тег v{expected} объявляет version = "{actual}" (pyproject.toml)'
    return 0, f'OK: тег v{expected} совпадает с version = "{actual}"'


def self_check() -> int:
    """Вшитые случаи. Репозиторий не читается: гард не должен зеленеть от текущего файла."""
    cases = [
        ("v0.7.13", 'version = "0.7.13"\n', 0),
        ("v0.7.12", 'version = "0.7.11"\n', 1),  # факт тега v0.7.12
        ("v0.7.9", 'version = "0.7.8"\n', 1),
        ("v0.7.1", 'version = "0.7.0"\n', 1),
        ("v0.7.11", 'version = "0.7.11"\nversion = "0.7.12"\n', 1),
        ("v0.7.11", 'name = "rob-box-dialog-core"\n', 1),
        ("not-a-release", 'version = "0.0.1"\n', 0),
    ]
    failed = 0
    for tag, text, want in cases:
        code, message = check(tag, text)
        mark = "OK" if code == want else "FAIL"
        if code != want:
            failed += 1
        print(f"{mark}: {tag} -> {code} (ждали {want}) {message}")
    return 1 if failed else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Тег vX.Y.Z совпадает с version в pyproject.toml")
    parser.add_argument("--tag", default="", help="имя тега, например v0.7.13; пусто — проверка не нужна")
    parser.add_argument("--pyproject", type=Path, default=PYPROJECT)
    parser.add_argument("--self-check", action="store_true", help="вшитые случаи, репозиторий не читается")
    args = parser.parse_args(argv)
    if args.self_check:
        return self_check()
    if not args.tag:
        print("SKIP: тег не передан (не push тега)")
        return 0
    text = args.pyproject.read_text(encoding="utf-8")
    code, message = check(args.tag, text)
    print(message)
    return code


if __name__ == "__main__":
    sys.exit(main())
