from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class CallState(str, Enum):
    INVITED = "invited"
    ACTIVE = "active"
    ENDED = "ended"
    FAILED = "failed"


@dataclass(slots=True)
class CallInvite:
    call_id: str
    user_id: str
    group_id: str | None = None
    nickname: str | None = None
    raw_event: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class AudioFrame:
    call_id: str
    pcm: bytes
    sample_rate: int = 16000
    timestamp_ms: int | None = None
    sequence: int | None = None


@dataclass(slots=True)
class TranscriptTurn:
    speaker: str
    text: str
    at: float = field(default_factory=time.time)


@dataclass(slots=True)
class CallSummary:
    call_id: str
    user_id: str
    group_id: str | None
    started_at: float
    ended_at: float
    duration_seconds: float
    summary: str
    facts: list[str]
    user_emotion: str
    follow_up: list[str]
    transcript: list[TranscriptTurn]

    def as_memory_text(self) -> str:
        facts = "；".join(self.facts) if self.facts else "无明确事实"
        follow_up = "；".join(self.follow_up) if self.follow_up else "无明确待办"
        transcript = "\n".join(f"{turn.speaker}: {turn.text}" for turn in self.transcript[-12:])
        return (
            "QQ 语音电话摘要\n"
            f"用户: {self.user_id}\n"
            f"群聊: {self.group_id or '私聊'}\n"
            f"时长: {self.duration_seconds:.1f} 秒\n"
            f"摘要: {self.summary}\n"
            f"事实: {facts}\n"
            f"用户情绪: {self.user_emotion}\n"
            f"待办: {follow_up}\n"
            f"最近转写:\n{transcript}"
        )


class CallSession:
    def __init__(self, invite: CallInvite, *, now: float | None = None) -> None:
        timestamp = time.time() if now is None else now
        self.invite = invite
        self.call_id = invite.call_id
        self.state = CallState.INVITED
        self.started_at = timestamp
        self.ended_at: float | None = None
        self.transcript: list[TranscriptTurn] = []
        self.audio_frames_received = 0
        self.audio_frames_sent = 0
        self.error = ""

    def mark_active(self) -> None:
        if self.state != CallState.FAILED:
            self.state = CallState.ACTIVE

    def note_inbound_audio(self) -> None:
        self.audio_frames_received += 1

    def note_outbound_audio(self) -> None:
        self.audio_frames_sent += 1

    def add_user_text(self, text: str, *, at: float | None = None) -> None:
        clean = " ".join(text.split())
        if clean:
            self.transcript.append(TranscriptTurn("user", clean, time.time() if at is None else at))

    def add_assistant_text(self, text: str, *, at: float | None = None) -> None:
        clean = " ".join(text.split())
        if clean:
            self.transcript.append(TranscriptTurn("assistant", clean, time.time() if at is None else at))

    def fail(self, reason: str, *, now: float | None = None) -> None:
        self.error = reason
        self.state = CallState.FAILED
        self.ended_at = time.time() if now is None else now

    def end(self, *, now: float | None = None) -> None:
        if self.ended_at is None:
            self.ended_at = time.time() if now is None else now
        if self.state != CallState.FAILED:
            self.state = CallState.ENDED

    def duration_seconds(self) -> float:
        end = self.ended_at if self.ended_at is not None else time.time()
        return max(0.0, end - self.started_at)
