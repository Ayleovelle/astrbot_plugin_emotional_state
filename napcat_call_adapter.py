from __future__ import annotations

import asyncio
import base64
import json
from dataclasses import dataclass
from typing import Any, AsyncIterator, Protocol

from call_session import AudioFrame, CallInvite


class CallBridgeError(RuntimeError):
    pass


@dataclass(slots=True)
class BridgeCommandResult:
    ok: bool
    detail: str = ""
    raw: dict[str, Any] | None = None


class NapCatCallBridge(Protocol):
    async def accept_call(self, call_id: str) -> BridgeCommandResult: ...
    async def reject_call(self, call_id: str, reason: str = "") -> BridgeCommandResult: ...
    async def hangup_call(self, call_id: str, reason: str = "") -> BridgeCommandResult: ...
    async def send_audio(self, frame: AudioFrame) -> BridgeCommandResult: ...
    async def events(self) -> AsyncIterator[dict[str, Any]]: ...


def parse_call_invite(event: dict[str, Any]) -> CallInvite | None:
    post_type = event.get("post_type")
    notice_type = event.get("notice_type") or event.get("sub_type")
    event_type = event.get("type") or event.get("event")
    if event_type not in {"qq_call_invite", "call_invite"} and notice_type not in {"qq_call_invite", "call_invite"}:
        return None
    call_id = str(event.get("call_id") or event.get("session_id") or event.get("message_id") or "").strip()
    user_id = str(event.get("user_id") or event.get("sender_id") or "").strip()
    if not call_id or not user_id:
        return None
    return CallInvite(
        call_id=call_id,
        user_id=user_id,
        group_id=str(event.get("group_id")) if event.get("group_id") else None,
        nickname=event.get("nickname") or event.get("sender", {}).get("nickname"),
        raw_event=dict(event),
    )


def parse_audio_frame(event: dict[str, Any]) -> AudioFrame | None:
    event_type = event.get("type") or event.get("event")
    if event_type not in {"qq_call_audio", "call_audio"}:
        return None
    call_id = str(event.get("call_id") or "").strip()
    payload = event.get("pcm_base64") or event.get("audio_base64")
    if not call_id or not payload:
        return None
    try:
        pcm = base64.b64decode(payload)
    except Exception as exc:
        raise CallBridgeError("invalid call audio base64 payload") from exc
    return AudioFrame(
        call_id=call_id,
        pcm=pcm,
        sample_rate=int(event.get("sample_rate") or 16000),
        timestamp_ms=event.get("timestamp_ms"),
        sequence=event.get("sequence"),
    )


def parse_hangup(event: dict[str, Any]) -> tuple[str, str] | None:
    event_type = event.get("type") or event.get("event")
    notice_type = event.get("notice_type") or event.get("sub_type")
    if event_type not in {"qq_call_hangup", "call_hangup"} and notice_type not in {"qq_call_hangup", "call_hangup"}:
        return None
    call_id = str(event.get("call_id") or event.get("session_id") or "").strip()
    if not call_id:
        return None
    return call_id, str(event.get("reason") or "remote_hangup")


class InMemoryNapCatCallBridge:
    def __init__(self) -> None:
        self.commands: list[tuple[str, str, str]] = []
        self.outbound_audio: list[AudioFrame] = []
        self._events: asyncio.Queue[dict[str, Any] | None] = asyncio.Queue()

    async def emit(self, event: dict[str, Any]) -> None:
        await self._events.put(event)

    async def close(self) -> None:
        await self._events.put(None)

    async def accept_call(self, call_id: str) -> BridgeCommandResult:
        self.commands.append(("accept", call_id, ""))
        return BridgeCommandResult(True, "accepted")

    async def reject_call(self, call_id: str, reason: str = "") -> BridgeCommandResult:
        self.commands.append(("reject", call_id, reason))
        return BridgeCommandResult(True, "rejected")

    async def hangup_call(self, call_id: str, reason: str = "") -> BridgeCommandResult:
        self.commands.append(("hangup", call_id, reason))
        return BridgeCommandResult(True, "hung_up")

    async def send_audio(self, frame: AudioFrame) -> BridgeCommandResult:
        self.outbound_audio.append(frame)
        return BridgeCommandResult(True, "audio_sent")

    async def events(self) -> AsyncIterator[dict[str, Any]]:
        while True:
            event = await self._events.get()
            if event is None:
                break
            yield event


class WebSocketNapCatCallBridge:
    def __init__(self, url: str) -> None:
        self.url = url
        self._ws: Any | None = None

    async def _connect(self) -> Any:
        if self._ws is None:
            try:
                import websockets
            except ImportError as exc:
                raise CallBridgeError("websockets package is required for NapCat call bridge") from exc
            self._ws = await websockets.connect(self.url)
        return self._ws

    async def _command(self, action: str, **payload: Any) -> BridgeCommandResult:
        ws = await self._connect()
        await ws.send(json.dumps({"action": action, **payload}, ensure_ascii=False))
        raw = json.loads(await ws.recv())
        return BridgeCommandResult(bool(raw.get("ok")), str(raw.get("detail") or ""), raw)

    async def accept_call(self, call_id: str) -> BridgeCommandResult:
        return await self._command("accept_call", call_id=call_id)

    async def reject_call(self, call_id: str, reason: str = "") -> BridgeCommandResult:
        return await self._command("reject_call", call_id=call_id, reason=reason)

    async def hangup_call(self, call_id: str, reason: str = "") -> BridgeCommandResult:
        return await self._command("hangup_call", call_id=call_id, reason=reason)

    async def send_audio(self, frame: AudioFrame) -> BridgeCommandResult:
        return await self._command(
            "send_audio",
            call_id=frame.call_id,
            pcm_base64=base64.b64encode(frame.pcm).decode("ascii"),
            audio_base64=base64.b64encode(frame.pcm).decode("ascii"),
            sample_rate=frame.sample_rate,
            timestamp_ms=frame.timestamp_ms,
            sequence=frame.sequence,
        )

    async def events(self) -> AsyncIterator[dict[str, Any]]:
        ws = await self._connect()
        async for message in ws:
            yield json.loads(message)

    async def close(self) -> None:
        if self._ws is not None:
            await self._ws.close()
            self._ws = None
