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
