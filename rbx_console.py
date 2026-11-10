"""Entry point ``rbx-chat``: консоль стенда хода v2 без ROS (scripts/dialogue/chat.py).

Скрипты стенда (scripts/dialog/*, scripts/dialogue/chat.py) — не код ядра: у них есть относительные
пути (parents[N]) для прогона из чекаута, поэтому в пакет ядра они НЕ входят (граница ADR-0167 §2.1).
Для pip-установки они кладутся в data-files (share/rob_box_dialog_core/scripts/), а rbx-chat находит
их либо там, либо в чекауте (scripts/).
"""

from __future__ import annotations

import sys
from pathlib import Path


def _scripts_dir() -> Path:
    """Каталог scripts/ (dialog + dialogue): сначала data-files установки, затем чекаут."""
    here = Path(__file__).resolve()
    # data-files: <sys.prefix>/share/rob_box_dialog_core/scripts
    for prefix in (Path(sys.prefix), Path(sys.exec_prefix) if sys.exec_prefix != sys.prefix else Path()):
        if str(prefix) and (prefix / "share" / "rob_box_dialog_core" / "scripts" / "dialog" / "dry_stand.py").is_file():
            return prefix / "share" / "rob_box_dialog_core" / "scripts"
    # чекаут: rbx_console.py лежит в корне репо, рядом scripts/ (или src/... при editable)
    for candidate in (here.parent / "scripts", here.parents[2] / "scripts"):
        if (candidate / "dialog" / "dry_stand.py").is_file():
            return candidate
    raise SystemExit("rbx-chat: не нашёл scripts/ стенда (share/rob_box_dialog_core/scripts или scripts/ чекаута)")


def main(argv=None) -> int:
    scripts = _scripts_dir()
    for sub in ("dialog", "dialogue"):
        p = scripts / sub
        if str(p) not in sys.path:
            sys.path.insert(0, str(p))
    import chat  # noqa: PLC0415 — только после сборки sys.path
    return chat.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
