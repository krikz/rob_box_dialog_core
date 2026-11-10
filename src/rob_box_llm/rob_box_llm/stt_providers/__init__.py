"""Адаптеры STT без ROS (ADR-0167 §2.1) в ядре: провайдеры распознавания речи.

Перенесены из ``rob_box_voice.stt_providers`` робота. Цепочка ``select_recognition``
и ``stt_fallback`` остаются у робота — здесь только сами провайдеры (контракт
``transcribe()`` + типизированные ``MiniMaxSTT*Error``), которые использует хост
колонки (``rob_box_station``). Старый путь ``rob_box_voice.*`` не воскрешаем (Ш1г-2).
"""

from rob_box_llm.stt_providers.minimax_provider import (  # noqa: F401
    MiniMaxSTTProvider,
    MiniMaxSTTError,
    ensure_wav_container,
)

__all__ = ["MiniMaxSTTProvider", "MiniMaxSTTError", "ensure_wav_container"]
