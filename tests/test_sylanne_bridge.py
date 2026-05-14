import asyncio
import unittest

from call_session import CallInvite, CallSession
from summary import summarize_call
from sylanne_bridge import SylanneBridge


class FakeSylanneService:
    def __init__(self):
        self.memory_payloads = []
        self.emotion_observations = []

    async def build_emotion_memory_payload(self, **kwargs):
        self.memory_payloads.append(kwargs)
        return {"ok": True}

    async def observe_emotion_text(self, **kwargs):
        self.emotion_observations.append(kwargs)
        return {"ok": True}


class TestableBridge(SylanneBridge):
    def __init__(self, service):
        super().__init__(context=None)
        self.service = service

    def _get_emotion_service(self):
        return self.service


class SylanneBridgeTests(unittest.TestCase):
    def test_write_summary_to_memory_and_emotion(self):
        session = CallSession(CallInvite(call_id="c1", user_id="u1"), now=1.0)
        session.add_user_text("我有点焦虑，帮我记住明天复习。")
        session.end(now=3.0)
        summary = summarize_call(session)
        service = FakeSylanneService()

        result = asyncio.run(TestableBridge(service).write_call_summary(summary))

        self.assertTrue(result.ok)
        self.assertEqual(result.memory, "ok")
        self.assertEqual(result.emotion, "ok")
        self.assertIn("QQ 语音电话摘要", service.memory_payloads[0]["memory_text"])
        self.assertEqual(service.memory_payloads[0]["source"], "qq_voice_call")
        self.assertEqual(service.emotion_observations[0]["phase"], "call_summary")
        self.assertEqual(service.emotion_observations[0]["source"], "qq_voice_call_summary")

    def test_service_unavailable_is_explicit(self):
        session = CallSession(CallInvite(call_id="c1", user_id="u1"), now=1.0)
        session.end(now=2.0)
        summary = summarize_call(session)

        result = asyncio.run(SylanneBridge(None).write_call_summary(summary))

        self.assertEqual(result.memory, "service_unavailable")
        self.assertEqual(result.emotion, "service_unavailable")


if __name__ == "__main__":
    unittest.main()
