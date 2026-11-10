"""rbx-chat: консоль стенда хода v2 без ROS (scripts/dialogue/chat.py), только из чекаута.

Скрипты стенда (scripts/dialog/*, scripts/dialogue/chat.py) в пакет ядра не входят: у них
относительные пути (parents[N]) и чекаут-относительная раскладка (граница ADR-0167 §2.1).
Колонка и хост робота держат свой стенд отдельно. rbx-chat ищет scripts/ от текущего
каталога (dev запускает из репо), иначе напоминает про python scripts/dialogue/chat.py.
"""

from __future__ import annotations

import sys
from pathlib import Path


def _scripts_dir() -> Path:
    """Каталог scripts/ (dialog + dialogue) из чекаута: ищем вверх от cwd и от этого файла."""
    roots = [Path.cwd(), Path(__file__).resolve().parent]
    for root in roots:
        cur = root
        for _ in range(6):  # до 6 уровней вверх (cwd могла быть scripts/dialogue)
            if (cur / "scripts" / "dialog" / "dry_stand.py").is_file():
                return cur / "scripts"
            if cur.parent == cur:
                break
            cur = cur.parent
    raise SystemExit(
        "rbx-chat: не нашёл scripts/ стенда — консоль работает только из чекаута "
        "(pip-пакет скрипты стенда не несёт, граница ADR-0167 §2.1); "
        "используй python scripts/dialogue/chat.py из репозитория"
    )


def main(argv=None) -> int:
    scripts = _scripts_dir()
    for sub in ("dialog", "dialogue"):
        p = scripts / sub
        if str(p) not in sys.path:
            sys.path.insert(0, str(p))
    import chat  # noqa: PLC0415 — после сборки sys.path
    return chat.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
