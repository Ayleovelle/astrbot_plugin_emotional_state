from __future__ import annotations

import inspect
from dataclasses import dataclass, field
from typing import Any

from call_session import CallSummary


@dataclass(slots=True)
class SylanneWriteResult:
    memory: str = "skipped"
    emotion: str = "skipped"
    memory_payload: dict[str, Any] | None = None
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors and (self.memory == "ok" or self.emotion == "ok")


async def _maybe_await(value: Any) -> Any:
    if inspect.isawaitable(value):
        return await value
    return value


class SylanneBridge:
    def __init__(self, context: Any | None = None, *, memory_service: Any | None = None) -> None:
        self.context = context
        self.memory_service = memory_service

    def _get_emotion_service(self) -> Any | None:
        if self.context is None:
            return None
        for module_name in (
            "astrbot_plugin_sylanne.public_api",
            "astrbot_plugin_emotional_state.public_api",
        ):
            try:
                module = __import__(module_name, fromlist=["get_emotion_service"])
                service = module.get_emotion_service(self.context)
                if service is not None:
                    return service
            except Exception:
                continue
        getter = getattr(self.context, "get_registered_star", None)
        if callable(getter):
            for plugin_name in ("astrbot_plugin_sylanne", "astrbot_plugin_emotional_state"):
                try:
                    metadata = getter(plugin_name)
                    service = getattr(metadata, "star_cls", None) if metadata else None
                except Exception:
                    service = None
                if service is not None:
                    return service
        return None

    async def write_call_summary(
        self,
        summary: CallSummary,
        *,
        write_memory: bool = True,
        observe_emotion: bool = True,
    ) -> SylanneWriteResult:
        result = SylanneWriteResult()
        service = self._get_emotion_service()
        memory_text = summary.as_memory_text()
        session_key = self._session_key(summary)
        if service is None:
            if write_memory:
                result.memory = "service_unavailable"
            if observe_emotion:
                result.emotion = "service_unavailable"
            return result
        if write_memory:
            await self._write_memory_annotation(service, summary, memory_text, session_key, result)
        if observe_emotion:
            await self._observe_emotion(service, summary, memory_text, session_key, result)
        return result

    def _session_key(self, summary: CallSummary) -> str:
        if summary.group_id:
            return f"qq-group:{summary.group_id}:user:{summary.user_id}"
        return f"qq-user:{summary.user_id}"

    async def _write_memory_annotation(
        self,
        service: Any,
        summary: CallSummary,
        memory_text: str,
        session_key: str,
        result: SylanneWriteResult,
    ) -> None:
        try:
            if not hasattr(service, "build_emotion_memory_payload"):
                result.memory = "method_unavailable"
                return
            payload = await _maybe_await(service.build_emotion_memory_payload(
                session_key=session_key,
                memory_text=memory_text,
                source="qq_voice_call",
                include_prompt_fragment=False,
                include_raw_snapshot=False,
                written_at=summary.ended_at,
            ))
            if isinstance(payload, dict):
                payload.setdefault("kind", "qq_voice_call_summary")
                payload.setdefault("call_id", summary.call_id)
                payload.setdefault("user_id", summary.user_id)
                payload.setdefault("group_id", summary.group_id)
                payload.setdefault("duration_seconds", summary.duration_seconds)
                result.memory_payload = payload
            wrote = await self._try_write_memory(payload if isinstance(payload, dict) else memory_text, summary)
            result.memory = "ok" if wrote or payload is not None else "payload_built"
        except Exception as exc:
            result.memory = "error"
            result.errors.append(f"memory: {exc}")

    async def _try_write_memory(self, memory: Any, summary: CallSummary) -> bool:
        service = self.memory_service or self._find_registered_memory_service()
        if service is None:
            return False
        for method_name in ("add_memory", "write_memory", "record_memory", "remember"):
            method = getattr(service, method_name, None)
            if not callable(method):
                continue
            fake_event = self._memory_event(summary)
            try:
                await _maybe_await(method(fake_event, memory))
            except TypeError:
                await _maybe_await(method(memory))
            return True
        return False

    def _find_registered_memory_service(self) -> Any | None:
        if self.context is None:
            return None
        getter = getattr(self.context, "get_registered_star", None)
        if not callable(getter):
            return None
        for name in ("astrbot_plugin_livingmemory", "astrbot_plugin_living_memory", "livingmemory"):
            try:
                metadata = getter(name)
            except Exception:
                continue
            plugin = getattr(metadata, "star_cls", None) if metadata else None
            if plugin is not None:
                return plugin
        return None

    def _memory_event(self, summary: CallSummary) -> Any:
        class MemoryEvent:
            pass

        event = MemoryEvent()
        event.unified_msg_origin = self._session_key(summary)
        event.user_id = summary.user_id
        event.group_id = summary.group_id
        return event

    async def _observe_emotion(
        self,
        service: Any,
        summary: CallSummary,
        memory_text: str,
        session_key: str,
        result: SylanneWriteResult,
    ) -> None:
        try:
            if not hasattr(service, "observe_emotion_text"):
                result.emotion = "method_unavailable"
                return
            await _maybe_await(service.observe_emotion_text(
                session_key=session_key,
                text=memory_text,
                phase="call_summary",
                role="user",
                source="qq_voice_call_summary",
                context_text=summary.summary,
                use_llm=True,
                commit=True,
                observed_at=summary.ended_at,
            ))
            result.emotion = "ok"
        except Exception as exc:
            result.emotion = "error"
            result.errors.append(f"emotion: {exc}")
