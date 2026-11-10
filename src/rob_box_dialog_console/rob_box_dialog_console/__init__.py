"""Консоль стенда хода v2 (ADR-0167 Ш3): тонкая обёртка над scripts/dialogue/chat.py.

Скрипты стенда (scripts/dialog/*, scripts/dialogue/chat.py) лежат как package-data
в data/scripts/ — rbx-chat кладёт их в sys.path и запускает chat.main(). Один источник
скриптов — scripts/ в корне репо; сюда они копируются при сборке колеса.
"""

__version__ = "0.7.2"
