import base64
import unittest

from napcat_call_adapter import parse_audio_frame, parse_call_invite


class NapCatCallAdapterTests(unittest.TestCase):
    def test_parse_call_invite(self):
        invite = parse_call_invite({
            "post_type": "notice",
            "notice_type": "qq_call_invite",
            "call_id": "call-1",
            "user_id": 12345,
            "group_id": 67890,
            "sender": {"nickname": "Alice"},
        })

        self.assertIsNotNone(invite)
        self.assertEqual(invite.call_id, "call-1")
        self.assertEqual(invite.user_id, "12345")
        self.assertEqual(invite.group_id, "67890")
        self.assertEqual(invite.nickname, "Alice")

    def test_parse_audio_frame(self):
        frame = parse_audio_frame({
            "type": "qq_call_audio",
            "call_id": "call-1",
            "pcm_base64": base64.b64encode(b"pcm").decode("ascii"),
            "sample_rate": 24000,
        })

        self.assertIsNotNone(frame)
        self.assertEqual(frame.pcm, b"pcm")
        self.assertEqual(frame.sample_rate, 24000)


if __name__ == "__main__":
    unittest.main()
