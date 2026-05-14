from __future__ import annotations

import asyncio
import contextlib
from typing import Any, Callable

try:
    from astrbot.api import AstrBotConfig, logger
    from astrbot.api.event import AstrMessageEvent, filter
    from astrbot.api.star import Context, Star, register
except Exception:  # pragma: no cover
    AstrBotConfig = dict
    logger = None

    class AstrMessageEvent:  # type: ignore
        pass

    class Star:  # type: ignore
        def __init__(self, context: Any = None) -> None:
            self.context = context

    class Context:  # type: ignore
        pass

    class _Filter:
        @staticmethod
        def command(*args: Any, **kwargs: Any) -> Callable[[Any], Any]:
            return lambda func: func

    filter = _Filter()  # type: ignore

    def register(*args: Any, **kwargs: Any) -> Callable[[Any], Any]:
        return lambda cls: cls

from call_session import AudioFrame, CallSession
from doubao_realtime_client import (
    DOUBAO_REALTIME_DEFAULT_RESOURCE_ID,
    DOUBAO_REALTIME_DEFAULT_URL,
    DoubaoRealtimeClient,
    DoubaoRealtimeConfig,
    RealtimeEvent,
    RealtimeVoiceClient,
)
from napcat_call_adapter import (
    InMemoryNapCatCallBridge,
    NapCatCallBridge,
    WebSocketNapCatCallBridge,
    parse_audio_frame,
    parse_call_invite,
    parse_hangup,
)
from summary import summarize_call
from sylanne_bridge import SylanneBridge


PLUGIN_NAME = "astrbot_plugin_qq_voice_call"
PLUGIN_VERSION = "0.1.0"


def _log_warning(message: str) -> None:
    if logger is not None:
        logger.warning(message)


@register(PLUGIN_NAME, "pidan", "QQ 语音电话助手", PLUGIN_VERSION)
class QQVoiceCallPlugin(Star):
    def __init__(self, context: Context | None = None, config: AstrBotConfig | dict[str, Any] | None = None) -> None:
        super().__init__(context)
        self.context = context
        self.config = dict(config or {})
        self.sessions: dict[str, CallSession] = {}
        self._clients: dict[str, RealtimeVoiceClient] = {}
        self._bridge_task: asyncio.Task[None] | None = None
        self._client_factory: Callable[[], RealtimeVoiceClient] | None = None
        self.bridge: NapCatCallBridge = self._build_bridge()
        self.sylanne = SylanneBridge(context)

    def _cfg(self, key: str, default: Any = None) -> Any:
        return self.config.get(key, default)

    def _build_bridge(self) -> NapCatCallBridge:
        bridge_url = str(self._cfg("napcat_call_bridge_url", "")).strip()
        if bridge_url:
            return WebSocketNapCatCallBridge(bridge_url)
        return InMemoryNapCatCallBridge()

    async def initialize(self) -> None:
        if self._cfg("enabled", True) and self._cfg("start_bridge_listener", True):
            self._bridge_task = asyncio.create_task(self._listen_bridge_events())

    async def terminate(self) -> None:
        if self._bridge_task is not None:
            self._bridge_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._bridge_task
            self._bridge_task = None
        for call_id in list(self.sessions):
            await self.finish_call(call_id, reason="plugin_terminate")
        close = getattr(self.bridge, "close", None)
        if callable(close):
            await close()

    def set_call_bridge(self, bridge: NapCatCallBridge) -> None:
        self.bridge = bridge

    def set_realtime_client_factory(self, factory: Callable[[], RealtimeVoiceClient]) -> None:
        self._client_factory = factory

    def _new_realtime_client(self) -> RealtimeVoiceClient:
        if self._client_factory is not None:
            return self._client_factory()
        return DoubaoRealtimeClient(DoubaoRealtimeConfig(
            url=str(self._cfg("doubao_realtime_url", DOUBAO_REALTIME_DEFAULT_URL)),
            app_id=str(self._cfg("doubao_app_id", "")),
            access_token=str(self._cfg("doubao_access_token", "")),
            app_key=str(self._cfg("doubao_app_key", "")),
            resource_id=str(self._cfg("doubao_resource_id", DOUBAO_REALTIME_DEFAULT_RESOURCE_ID)),
            model=str(self._cfg("doubao_model", "doubao-realtime-voice")),
            sample_rate=int(self._cfg("sample_rate", 16000)),
        ))

    async def _listen_bridge_events(self) -> None:
        try:
            async for event in self.bridge.events():
                await self.handle_bridge_event(event)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            _log_warning(f"{PLUGIN_NAME}: NapCat 电话桥接监听已停止: {exc}")

    async def handle_bridge_event(self, event: dict[str, Any]) -> dict[str, Any]:
        invite = parse_call_invite(event)
        if invite is not None:
            return await self.handle_call_invite(invite)

        frame = parse_audio_frame(event)
        if frame is not None:
            return await self.handle_audio_frame(frame)

        hangup = parse_hangup(event)
        if hangup is not None:
            call_id, reason = hangup
            summary = await self.finish_call(call_id, reason=reason)
            return {"ok": True, "summary": summary.summary if summary else ""}
        return {"ok": False, "reason": "ignored"}

    async def handle_call_invite(self, invite: Any) -> dict[str, Any]:
        if not self._cfg("enabled", True):
            return {"ok": False, "reason": "plugin_disabled"}
        session = CallSession(invite)
        self.sessions[invite.call_id] = session
        if not self._cfg("auto_answer", False):
            return {"ok": True, "state": session.state.value, "auto_answer": False}

        accepted = await self.bridge.accept_call(invite.call_id)
        if not accepted.ok:
            session.fail(accepted.detail or "accept_failed")
            return {"ok": False, "reason": session.error}

        session.mark_active()
        client = self._new_realtime_client()
        try:
            await client.start()
        except Exception as exc:
            session.fail(str(exc))
            await self.bridge.hangup_call(invite.call_id, "doubao_start_failed")
            return {"ok": False, "reason": "doubao_start_failed", "detail": str(exc)}
        self._clients[invite.call_id] = client
        return {"ok": True, "state": session.state.value, "auto_answer": True}

    async def handle_audio_frame(self, frame: AudioFrame) -> dict[str, Any]:
        session = self.sessions.get(frame.call_id)
        client = self._clients.get(frame.call_id)
        if session is None or client is None:
            return {"ok": False, "reason": "unknown_or_inactive_call"}
        session.note_inbound_audio()
        await client.send_audio(frame.pcm)
        await self._drain_realtime_events(session, client)
        return {"ok": True, "audio_frames_received": session.audio_frames_received}

    async def run_model_turn(self, call_id: str, frames: list[AudioFrame]) -> None:
        session = self.sessions[call_id]
        client = self._clients.get(call_id)
        owned_client = False
        if client is None:
            client = self._new_realtime_client()
            await client.start()
            owned_client = True
        try:
            for frame in frames:
                session.note_inbound_audio()
                await client.send_audio(frame.pcm)
            await client.finish_audio()
            await self._drain_realtime_events(session, client)
        finally:
            if owned_client:
                await client.close()

    async def _drain_realtime_events(self, session: CallSession, client: RealtimeVoiceClient) -> None:
        async for event in client.events():
            await self._handle_realtime_event(session, event)

    async def _handle_realtime_event(self, session: CallSession, event: RealtimeEvent) -> None:
        if event.text:
            event_type = event.type.lower()
            if "input" in event_type or "user" in event_type or "transcript" in event_type:
                session.add_user_text(event.text)
            else:
                session.add_assistant_text(event.text)
        if event.audio:
            await self.bridge.send_audio(AudioFrame(
                call_id=session.call_id,
                pcm=event.audio,
                sample_rate=int(self._cfg("sample_rate", 16000)),
            ))
            session.note_outbound_audio()

    async def finish_call(self, call_id: str, *, reason: str = "hangup") -> Any:
        session = self.sessions.get(call_id)
        if session is None:
            return None
        client = self._clients.pop(call_id, None)
        if client is not None:
            with contextlib.suppress(Exception):
                await client.finish_audio()
                await self._drain_realtime_events(session, client)
            with contextlib.suppress(Exception):
                await client.close()
        session.end()
        summary = summarize_call(session, max_chars=int(self._cfg("summary_max_chars", 1200)))
        await self.sylanne.write_call_summary(
            summary,
            write_memory=bool(self._cfg("write_sylanne_memory", True)),
            observe_emotion=bool(self._cfg("observe_sylanne_emotion", True)),
        )
        self.sessions.pop(call_id, None)
        return summary

    @filter.command("qq_call_status")
    async def qq_call_status(self, event: AstrMessageEvent) -> None:
        text = f"QQ 语音电话插件运行中，当前通话数：{len(self.sessions)}"
        if hasattr(event, "plain_result"):
            yield event.plain_result(text)
        elif hasattr(event, "send"):
            await event.send(text)

    @filter.command("qq_call_help")
    async def qq_call_help(self, event: AstrMessageEvent) -> None:
        text = (
            "QQ 语音电话助手：需要 NapCat 电话桥接层提供来电、接听、PCM 音频帧和挂断事件；"
            "模型侧配置火山引擎豆包端到端实时语音大模型；挂断后会写入 Sylanne 摘要记忆和情绪观察。"
        )
        if hasattr(event, "plain_result"):
            yield event.plain_result(text)
        elif hasattr(event, "send"):
            await event.send(text)
