from __future__ import annotations

import asyncio
import base64
import json
import uuid
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Protocol


DOUBAO_REALTIME_DEFAULT_URL = "wss://openspeech.bytedance.com/api/v3/realtime/dialogue"
DOUBAO_REALTIME_DEFAULT_RESOURCE_ID = "volc.speech.dialog"


@dataclass(slots=True)
class DoubaoRealtimeConfig:
    url: str = DOUBAO_REALTIME_DEFAULT_URL
    app_id: str = ""
    access_token: str = ""
    app_key: str = ""
    resource_id: str = DOUBAO_REALTIME_DEFAULT_RESOURCE_ID
    model: str = "doubao-realtime-voice"
    sample_rate: int = 16000
    extra_headers: dict[str, str] = field(default_factory=dict)

    def headers(self) -> dict[str, str]:
        headers = dict(self.extra_headers)
        if self.app_id:
            headers["X-Api-App-ID"] = self.app_id
            headers["X-Api-App-Id"] = self.app_id
        if self.access_token:
            headers["X-Api-Access-Key"] = self.access_token
            headers["Authorization"] = f"Bearer {self.access_token}"
        if self.app_key:
            headers["X-Api-App-Key"] = self.app_key
        if self.resource_id:
            headers["X-Api-Resource-Id"] = self.resource_id
        headers.setdefault("X-Api-Connect-Id", str(uuid.uuid4()))
        return headers


@dataclass(slots=True)
class RealtimeEvent:
    type: str
    text: str = ""
    audio: bytes = b""
    raw: dict[str, Any] = field(default_factory=dict)


class RealtimeVoiceClient(Protocol):
    async def start(self) -> None: ...
    async def send_audio(self, pcm: bytes) -> None: ...
    async def finish_audio(self) -> None: ...
    async def events(self) -> AsyncIterator[RealtimeEvent]: ...
    async def close(self) -> None: ...


class DoubaoRealtimeClient:
    def __init__(self, config: DoubaoRealtimeConfig) -> None:
        self.config = config
        self._ws: Any | None = None

    async def start(self) -> None:
        if not self.config.url:
            raise ValueError("doubao_realtime_url is required")
        try:
            import websockets
        except ImportError as exc:
            raise RuntimeError("websockets package is required for Doubao realtime voice") from exc
        self._ws = await websockets.connect(self.config.url, extra_headers=self.config.headers())
        await self._send_json({
            "type": "session.start",
            "model": self.config.model,
            "modalities": ["text", "audio"],
            "input_audio_format": "pcm_s16le",
            "output_audio_format": "pcm_s16le",
            "sample_rate": self.config.sample_rate,
        })

    async def _send_json(self, payload: dict[str, Any]) -> None:
        if self._ws is None:
            raise RuntimeError("Doubao realtime client is not started")
        await self._ws.send(json.dumps(payload, ensure_ascii=False))

    async def send_audio(self, pcm: bytes) -> None:
        await self._send_json({
            "type": "input_audio_buffer.append",
            "audio": base64.b64encode(pcm).decode("ascii"),
        })

    async def finish_audio(self) -> None:
        await self._send_json({"type": "input_audio_buffer.commit"})
        await self._send_json({"type": "response.create"})

    async def events(self) -> AsyncIterator[RealtimeEvent]:
        if self._ws is None:
            raise RuntimeError("Doubao realtime client is not started")
        async for message in self._ws:
            raw = json.loads(message)
            yield self._parse_event(raw)

    def _parse_event(self, raw: dict[str, Any]) -> RealtimeEvent:
        event_type = str(raw.get("type") or raw.get("event") or "")
        text = str(
            raw.get("text")
            or raw.get("transcript")
            or raw.get("delta")
            or raw.get("content")
            or ""
        )
        audio_payload = raw.get("audio") or raw.get("audio_base64") or raw.get("delta_audio")
        audio = base64.b64decode(audio_payload) if isinstance(audio_payload, str) and audio_payload else b""
        return RealtimeEvent(event_type, text=text, audio=audio, raw=raw)

    async def close(self) -> None:
        if self._ws is not None:
            try:
                await self._send_json({"type": "session.close"})
            except Exception:
                pass
            await self._ws.close()
            self._ws = None


class FakeRealtimeVoiceClient:
    def __init__(self, events: list[RealtimeEvent] | None = None) -> None:
        self.started = False
        self.closed = False
        self.audio_chunks: list[bytes] = []
        self.finished = False
        self._events = list(events or [])

    async def start(self) -> None:
        self.started = True

    async def send_audio(self, pcm: bytes) -> None:
        self.audio_chunks.append(pcm)

    async def finish_audio(self) -> None:
        self.finished = True

    async def events(self) -> AsyncIterator[RealtimeEvent]:
        for event in self._events:
            await asyncio.sleep(0)
            yield event

    async def close(self) -> None:
        self.closed = True
