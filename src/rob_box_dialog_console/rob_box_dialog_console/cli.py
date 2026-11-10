"""Entry point rbx-chat: консоль стенда хода v2 без ROS (scripts/dialogue/chat.py).

Из чекаута chat.py и модули dialog/* лежат в scripts/; из поставленного колеса — в
package-data data/scripts/. Здесь один способ запуска: положить каталог скриптов
первым в sys.path и вызвать chat.main().
"""

from __future__ import annotations

import sys
from importlib import resources
from pathlib import Path

#: Пакет, внутри которого лежат скрипты стенда как package-data.
PKG = "rob_box_dialog_console"


def _scripts_dir() -> Path:
    """Каталог scripts/ (dialog + dialogue): из колеса — package-data, из чекаута — корень репо."""
    try:
        data = resources.files(PKG) / "data" / "scripts"
        if (data / "dialog" / "dry_stand.py").is_file():
            return Path(str(data))
    except Exception:  # noqa: BLE001 — пакет не поставлен / data нет
        pass
    here = Path(__file__).resolve()
    for candidate in (here.parents[3] / "scripts", here.parents[4] / "scripts"):
        if (candidate / "dialog" / "dry_stand.py").is_file():
            return candidate
    raise SystemExit("rbx-chat: не нашёл scripts/ стенда (data/scripts/ в пакете или scripts/ в чекауте)")


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
