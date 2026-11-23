"""Описание ``chimera_perform``, которое видит модель, согласовано с enum схемы (#5152, ADR-0148).

Каталог объявляет инструмент: ``action`` — ``chimera_offer.ACTIONS``, не профиль поставки.
Сужение до фактического профиля делает рантайм (``offered_schema``), не генератор. Текст и поля
строит тот же модуль из списка, который стоит в enum. Своей копии строки в тесте нет.
"""

from rob_box_core.tool_catalog import get_tool
from rob_box_dialog import knowledge as kn
from rob_box_dialog.chimera_offer import ACTIONS, fields_for, perform_description
from rob_box_dialog.command import Form, tool_schema
from rob_box_dialog_host.dialog_v2_ports import tool_schema as model_schema


def _entry():
    return get_tool(kn.CHIMERA_TOOL)


def _shown(form):
    from rob_box_dialog.command import turn_form

    with turn_form(form):
        return model_schema(_entry())["function"]


def test_shown_schema_agrees_with_the_catalog_enum_and_hides_foreign_fields():
    """Вне хода показ равен enum каталога. Каталог объявляет все четыре действия.

    Существо и вызов в каталоге без enum: их сужает загрузчик поставки, не генератор.
    Текст — ``perform_description`` того же списка. Литерал каталога совпадает с показом.
    """
    shown = _shown(Form())
    actions = shown["parameters"]["properties"]["action"]["enum"]
    assert actions == list(ACTIONS)
    assert shown["description"] == perform_description(actions)
    assert shown["description"] == _entry().description
    assert "не обещает" not in shown["description"]
    names = set(shown["parameters"]["properties"])
    assert names == {"action", *fields_for(actions)}
    assert {"title", "syllables", "timbre", "creature", "call", "phrase_id"} <= names
    assert "enum" not in shown["parameters"]["properties"]["creature"]
    assert "enum" not in shown["parameters"]["properties"]["call"]


def test_synth_form_offers_sing_and_does_not_deny_it():
    form = Form(sing="live:song", text="Робот, спой химерой песню про енота")
    shown = _shown(form)
    actions = shown["parameters"]["properties"]["action"]["enum"]
    assert actions == ["sing"]
    assert shown["description"] == perform_description(actions)
    assert "sing" in shown["description"]
    offered = shown["description"].split("сейчас это ", 1)[1].split(".", 1)[0]
    assert "пение" in offered and "не обещает" not in offered
    names = set(shown["parameters"]["properties"])
    assert names == {"action", *fields_for(actions)}
    assert {"title", "timbre", "syllables"} <= names
    assert "creature" not in names and "phrase_id" not in names


def test_validator_keeps_the_catalog_fields_outside_the_sing_form():
    """Вне хода валидатор не режет поля и не подменяет enum: судит каталог как есть.

    Каталог объявляет все четыре действия, поэтому ``sing`` здесь из enum. Отказ
    «не обещает» строит тот же модуль, когда список короче объявления.
    """
    shown = tool_schema(kn.CHIMERA_TOOL, Form())
    assert "title" in shown["properties"]
    assert shown["properties"]["action"]["enum"] == list(ACTIONS)
    denied = perform_description(["call"])
    assert "не обещает" in denied and "пение" in denied
    assert denied != perform_description(list(ACTIONS))
