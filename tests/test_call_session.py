import unittest

from call_session import CallInvite, CallSession, CallState
from summary import summarize_call


class CallSessionTests(unittest.TestCase):
    def test_session_transcript_and_summary(self):
        session = CallSession(CallInvite(call_id="c1", user_id="u1"), now=10.0)
        session.mark_active()
        session.add_user_text("我需要你明天提醒我复习，记住我喜欢安静。", at=11.0)
        session.add_assistant_text("好的，我会记住。", at=12.0)
        session.end(now=70.0)

        summary = summarize_call(session)

        self.assertEqual(session.state, CallState.ENDED)
        self.assertEqual(summary.duration_seconds, 60.0)
        self.assertIn("复习", summary.summary)
        self.assertTrue(summary.facts)
        self.assertTrue(summary.follow_up)
        self.assertIn("QQ 语音电话摘要", summary.as_memory_text())


if __name__ == "__main__":
    unittest.main()
