"""Unit-тесты для rob_box_llm.stt_providers.minimax_provider (перенесён в ядро, ADR-0167 Ш3).

Без сети и без ROS: HTTP подменяется заглушкой. Покрываем контракт, который использует
хост колонки (rob_box_station): transcribe(), ensure_wav_container(), типизированные
MiniMaxSTT*Error, _extract_text, maybe_from_env. Цепочка select_recognition / stt_fallback
осталась у робота и сюда НЕ переносилась.
"""

from __future__ import annotations

import io
import wave

import pytest

from rob_box_llm.stt_providers.minimax_provider import (
    DEFAULT_BASE_URL,
    DEFAULT_MODEL,
    MAX_AUDIO_BYTES,
    PROVIDER_NAME,
    MiniMaxSTTAuthError,
    MiniMaxSTTError,
    MiniMaxSTTInvalidResponseError,
    MiniMaxSTTProvider,
    MiniMaxSTTQuotaError,
    MiniMaxSTTRateLimitError,
    MiniMaxSTTResponse,
    MiniMaxSTTUnavailableError,
    _extract_text,
    ensure_wav_container,
    looks_like_quota_problem,
)


class _Resp:
    """Минимальная заглушка httpx.Response: status_code, text, json()."""

    def __init__(self, status=200, payload=None, raw=None):
        self.status_code = status
        self._payload = payload
        self.text = ("" if raw is None else (raw.decode("utf-8", "replace") if isinstance(raw, bytes) else raw)) \
            if payload is None else ""

    def json(self):
        if self._payload is None:
            raise ValueError("no json")
        return self._payload


class _Client:
    """Заглушка httpx.Client: post() запоминает вызов и отдаёт заданный ответ."""

    def __init__(self, status=200, payload=None, raw=None, exception=None):
        self._status, self._payload, self._raw, self._exception = status, payload, raw, exception
        self.calls = []
        self.closed = False

    def post(self, url, *, headers, files, data):
        self.calls.append({"url": url, "headers": dict(headers), "files": dict(files), "data": dict(data)})
        if self._exception is not None:
            raise self._exception
        return _Resp(self._status, self._payload, self._raw)

    def close(self):
        self.closed = True


def _provider(client, api_key="test-key"):
    p = MiniMaxSTTProvider(api_key=api_key)
    p._client = client
    return p


SILENCE = b"\x00\x00" * 16000


# ── ensure_wav_container ───────────────────────────────────────────────


def test_ensure_wav_wraps_headerless_pcm():
    wav = ensure_wav_container(SILENCE)
    assert wav[:4] == b"RIFF" and wav[8:12] == b"WAVE"
    with wave.open(io.BytesIO(wav), "rb") as w:
        assert w.getnchannels() == 1
        assert w.getsampwidth() == 2
        assert w.getframerate() == 16000
        assert w.readframes(w.getnframes()) == SILENCE


def test_ensure_wav_passthrough_existing_wav():
    wav = ensure_wav_container(SILENCE)
    assert ensure_wav_container(wav) == wav


def test_ensure_wav_empty_and_odd_bytes():
    assert ensure_wav_container(b"") == b""
    assert ensure_wav_container(b"\x00") == b"\x00"  # нечётная длина — как есть


# ── _extract_text ──────────────────────────────────────────────────────


def test_extract_top_level_and_nested():
    assert _extract_text({"text": "привет"}) == "привет"
    assert _extract_text({"text": "  привет  "}) == "привет"
    assert _extract_text({"data": {"text": "привет"}}) == "привет"
    assert _extract_text({"text": ""}) == ""
    assert _extract_text({"data": {}}) == ""
    assert _extract_text({"foo": "bar"}) is None
    assert _extract_text("not dict") is None


# ── транскрипция + ошибки ──────────────────────────────────────────────


def test_transcribe_success():
    client = _Client(200, {"text": "расскажи сказку"})
    resp = _provider(client).transcribe(SILENCE)
    assert isinstance(resp, MiniMaxSTTResponse)
    assert resp.text == "расскажи сказку"
    assert client.calls[0]["url"].endswith("/v1/speech_to_text")
    assert client.calls[0]["headers"]["Authorization"] == "Bearer test-key"
    assert client.calls[0]["files"]["file"][0] == "audio.wav"


def test_transcribe_typed_errors():
    with pytest.raises(MiniMaxSTTAuthError):
        _provider(_Client(401, {"error": "x"})).transcribe(SILENCE)
    with pytest.raises(MiniMaxSTTRateLimitError):
        _provider(_Client(429, {"error": "x"})).transcribe(SILENCE)
    with pytest.raises(MiniMaxSTTUnavailableError):
        _provider(_Client(503, {"error": "x"})).transcribe(SILENCE)
    with pytest.raises(MiniMaxSTTInvalidResponseError):
        _provider(_Client(200, {"foo": "bar"})).transcribe(SILENCE)


def test_quota_in_body_not_http_status():
    # квота/план приезжает в теле (HTTP 200 + base_resp 2056), а не статусом
    payload = {"base_resp": {"status_code": 2056, "status_msg": "Token Plan usage limit reached"}}
    with pytest.raises(MiniMaxSTTQuotaError):
        _provider(_Client(200, payload)).transcribe(SILENCE)


def test_error_hierarchy():
    assert issubclass(MiniMaxSTTAuthError, MiniMaxSTTError)
    assert issubclass(MiniMaxSTTRateLimitError, MiniMaxSTTError)
    assert issubclass(MiniMaxSTTUnavailableError, MiniMaxSTTError)
    assert issubclass(MiniMaxSTTInvalidResponseError, MiniMaxSTTError)
    assert issubclass(MiniMaxSTTQuotaError, MiniMaxSTTError)


def test_looks_like_quota_problem():
    assert looks_like_quota_problem("token plan not support model (2061)")
    assert looks_like_quota_problem("insufficient balance")
    assert not looks_like_quota_problem("invalid audio format")
    assert not looks_like_quota_problem("")


# ── maybe_from_env / конструктор ───────────────────────────────────────


def test_maybe_from_env_without_key(monkeypatch):
    monkeypatch.delenv("MINIMAX_API_KEY", raising=False)
    assert MiniMaxSTTProvider.maybe_from_env() is None


def test_maybe_from_env_with_key(monkeypatch):
    monkeypatch.setenv("MINIMAX_API_KEY", "abc")
    p = MiniMaxSTTProvider.maybe_from_env()
    assert p is not None and p.name == PROVIDER_NAME


def test_no_key_raises():
    with pytest.raises(MiniMaxSTTUnavailableError):
        MiniMaxSTTProvider(api_key="")


def test_constants():
    assert PROVIDER_NAME == "minimax"
    assert DEFAULT_BASE_URL == "https://api.minimax.io"
    assert DEFAULT_MODEL == "asr-1.0"
    assert 1 * 1024 * 1024 < MAX_AUDIO_BYTES <= 100 * 1024 * 1024


def test_input_validation_before_network():
    client = _Client(200, {"text": "ok"})
    p = _provider(client)
    with pytest.raises(MiniMaxSTTError, match="empty"):
        p.transcribe(b"")
    with pytest.raises(MiniMaxSTTError, match="exceeds"):
        p.transcribe(b"\x00" * (MAX_AUDIO_BYTES + 1))
    assert client.calls == []
