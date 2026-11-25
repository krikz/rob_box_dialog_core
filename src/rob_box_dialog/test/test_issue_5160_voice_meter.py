"""The addressed meter command reaches the motion owner with fixed arguments."""

import pytest
from robot_wake_fixture import ROBOT_WAKE
from test_turn import Ports, _engine, _run_addressed

from rob_box_dialog.address import BACKLOG_PICKUP, Addressed, decide
from rob_box_dialog.backlog import Backlog, Heard
from rob_box_dialog.command import Command
from rob_box_dialog.session import Session
from rob_box_dialog.turn import Answer, TurnEngine


def _voice_turn(ports: Ports, text: str) -> None:
    utterance = decide(Heard(text, t=100.0), Backlog(), ROBOT_WAKE)
    assert isinstance(utterance, Addressed)
    _run_addressed(_engine(ports), utterance)


@pytest.mark.parametrize(
    ("text", "status", "expected"),
    [
        ("Робот, вперёд на метр", "rejected", "Не могу поехать."),
        ("Робот, вперед на метр.", "done", "Приехал."),
    ],
)
def test_meter_command_calls_move_direction_once_and_reports_outcome(text: str, status: str, expected: str) -> None:
    ports = Ports(
        answers=[Answer(Command(speech="Уточни просьбу."), "test")],
        outcomes={"move_direction": (status, {})},
    )

    _voice_turn(ports, text)

    assert ports.executed == [[("move_direction", {"direction": "вперёд", "distance": 1.0})]]
    assert ports.asked == []
    assert [spoken for spoken, _, _ in ports.said] == [expected]


@pytest.mark.parametrize(
    "text",
    [
        "Робот, вперёд",
        "Робот, вперёд на метр?",
        "Робот, «вперёд на метр»",
        "Робот, не вперёд на метр",
        "Робот, посмотри вперёд на метр",
        "Скажи, Робот, вперёд на метр",
        "Робот, стоп, вперёд на метр",
        "Робот, назад на метр",
        "Робот, вперёд на два метра",
    ],
)
def test_meter_lookalikes_leave_motion_closed(text: str) -> None:
    ports = Ports(answers=[Answer(Command(speech="Хорошо."), "test")])

    _voice_turn(ports, text)

    assert ports.executed == []
    assert all("move_direction" not in names for _, names, _ in ports.asked)


def test_meter_text_picked_up_from_backlog_does_not_move_the_base() -> None:
    ports = Ports(answers=[Answer(Command(speech="Хорошо."), "test")])

    _run_addressed(_engine(ports), Addressed("вперёд на метр", BACKLOG_PICKUP, pickup=True))

    assert ports.executed == []


def test_meter_command_does_not_run_on_a_product_without_motion_owner() -> None:
    ports = Ports(answers=[Answer(Command(speech="Хорошо."), "test")])
    engine = TurnEngine(Session("personality", owners=()), ports)
    utterance = decide(Heard("Робот, вперёд на метр", t=100.0), Backlog(), ROBOT_WAKE)
    assert isinstance(utterance, Addressed)

    _run_addressed(engine, utterance)

    assert ports.executed == []
