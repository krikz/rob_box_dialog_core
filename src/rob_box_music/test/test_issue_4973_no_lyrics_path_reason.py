"""#4973 — отказ «инструментал/кавер с поданными словами» читает причину по ключу, не падает.

``instrumental_order`` монорепо берёт ``REASON_WORDS["no_lyrics_path"]`` жёстко (не ``.get``) и печатает строку
в отказе до заказа: путь не несёт поданных слов, тему не подменяют. Образ ставит ``rob_box_music`` из тега ядра;
без ключа следующий сборка ловит ``KeyError``. Строка — контракт с монорепо, не формулировка теста.
"""

from rob_box_music.source import REASON_WORDS

NO_LYRICS_PATH = "этот путь не поёт поданные слова"


def test_no_lyrics_path_reason_is_the_monorepo_contract():
    """Ключ есть, и текст ровно тот, что печатает отказ монорепо."""
    assert REASON_WORDS["no_lyrics_path"] == NO_LYRICS_PATH
