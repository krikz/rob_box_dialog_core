from rob_box_dialog_host.dialog_v2_ports import V2Ports


class _Performer:
    def __init__(self):
        self.answers = []

    def answer(self, yes):
        self.answers.append(yes)
        return True


def test_answer_perform_forwards_the_answer_to_its_owner():
    performer = _Performer()
    ports = V2Ports(None, None, None, None, performer=lambda: performer)

    assert ports.answer_perform(True) is True
    assert performer.answers == [True]


class _SingleProvider:
    """Один провайдер без цепочки: ``answered_by`` нет, имя — на самом провайдере (колонка, #29)."""

    name = "deepseek"


def test_lone_provider_is_named_by_its_own_name_not_left_blank():
    """Один провайдер — не цепочка, ``answered_by`` он не ставит. Имя берётся с провайдера, как у успешного ответа,
    иначе фраза отказа врёт «долго думаю» (``understand.timeout`` выбирается только при пустом имени)."""
    ports = V2Ports(None, _SingleProvider(), None, None)

    assert ports.provider() == "deepseek"


def test_wrapper_name_is_not_a_provider_name():
    """``health-aware-fallback`` — имя обёртки, одно на всех: человеку оно ничего не говорит."""

    class _Wrapper:
        name = "health-aware-fallback"

    assert V2Ports(None, _Wrapper(), None, None).provider() == ""
