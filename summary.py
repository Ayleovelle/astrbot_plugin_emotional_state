from __future__ import annotations

import re

from call_session import CallSession, CallSummary


_SENTENCE_SPLIT_RE = re.compile(r"(?<=[。！？!?])\s*|\n+")
_FACT_MARKERS = ("我叫", "我是", "住在", "喜欢", "讨厌", "正在", "计划", "需要", "记住", "别忘")
_FOLLOW_UP_MARKERS = ("提醒", "待会", "明天", "后天", "下次", "帮我", "记得", "安排")
_NEGATIVE_MARKERS = ("难受", "焦虑", "害怕", "生气", "烦", "累", "崩溃", "委屈", "孤独")
_POSITIVE_MARKERS = ("开心", "放心", "高兴", "喜欢", "期待", "轻松", "谢谢", "太好了")


def _sentences(text: str) -> list[str]:
    chunks: list[str] = []
    for part in _SENTENCE_SPLIT_RE.split(text.replace("\r", "\n")):
        clean = " ".join(part.split())
        if clean:
            chunks.append(clean)
    return chunks


def _pick_lines(lines: list[str], markers: tuple[str, ...], limit: int = 5) -> list[str]:
    picked: list[str] = []
    for line in lines:
        if any(marker in line for marker in markers):
            picked.append(line)
        if len(picked) >= limit:
            break
    return picked


def _estimate_emotion(user_text: str) -> str:
    if any(word in user_text for word in _NEGATIVE_MARKERS):
        return "偏负面或需要安抚"
    if any(word in user_text for word in _POSITIVE_MARKERS):
        return "偏正面或放松"
    return "中性或不明确"


def summarize_call(session: CallSession, *, max_chars: int = 1200) -> CallSummary:
    user_turns = [turn.text for turn in session.transcript if turn.speaker == "user"]
    assistant_turns = [turn.text for turn in session.transcript if turn.speaker == "assistant"]
    user_lines = _sentences("\n".join(user_turns))
    assistant_lines = _sentences("\n".join(assistant_turns))

    if user_lines:
        summary = "；".join(user_lines[:6])
    elif assistant_lines:
        summary = "用户拨打 QQ 语音电话，主要由 bot 进行回应，用户侧未产生清晰转写。"
    else:
        summary = "用户拨打 QQ 语音电话，但本次通话没有获得可用转写内容。"
    summary = summary[: max(80, max_chars)]

    user_text = "\n".join(user_turns)
    return CallSummary(
        call_id=session.call_id,
        user_id=session.invite.user_id,
        group_id=session.invite.group_id,
        started_at=session.started_at,
        ended_at=session.ended_at or session.started_at,
        duration_seconds=session.duration_seconds(),
        summary=summary,
        facts=_pick_lines(user_lines, _FACT_MARKERS),
        user_emotion=_estimate_emotion(user_text),
        follow_up=_pick_lines(user_lines, _FOLLOW_UP_MARKERS),
        transcript=list(session.transcript),
    )
