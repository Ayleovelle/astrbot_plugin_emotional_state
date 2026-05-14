import asyncio
import unittest

from call_session import AudioFrame
from doubao_realtime_client import FakeRealtimeVoiceClient, RealtimeEvent
from main import PLUGIN_NAME, QQVoiceCallPlugin
from napcat_call_adapter import InMemoryNapCatCallBridge, parse_call_invite


class PluginLifecycleTests(unittest.TestCase):
    def test_plugin_name(self):
        self.assertEqual(PLUGIN_NAME, "astrbot_plugin_qq_voice_call")

    def test_invite_does_not_auto_answer_by_default(self):
        async def run():
            plugin = QQVoiceCallPlugin(config={})
            event = {"type": "qq_call_invite", "call_id": "c1", "user_id": "u1"}
            return await plugin.handle_bridge_event(event), plugin

        result, plugin = asyncio.run(run())

        self.assertTrue(result["ok"])
        self.assertFalse(result["auto_answer"])
        self.assertIn("c1", plugin.sessions)

    def test_auto_answer_accepts_call(self):
        async def run():
            bridge = InMemoryNapCatCallBridge()
            plugin = QQVoiceCallPlugin(config={"auto_answer": True})
            plugin.set_call_bridge(bridge)
            plugin.set_realtime_client_factory(lambda: FakeRealtimeVoiceClient())
            invite = parse_call_invite({"type": "qq_call_invite", "call_id": "c1", "user_id": "u1"})
            result = await plugin.handle_call_invite(invite)
            return result, bridge

        result, bridge = asyncio.run(run())

        self.assertEqual(result["state"], "active")
        self.assertEqual(bridge.commands[0], ("accept", "c1", ""))

    def test_model_turn_records_transcript_and_sends_audio(self):
        async def run():
            bridge = InMemoryNapCatCallBridge()
            plugin = QQVoiceCallPlugin(config={"auto_answer": True})
            plugin.set_call_bridge(bridge)
            plugin.set_realtime_client_factory(lambda: FakeRealtimeVoiceClient([
                RealtimeEvent("input.transcript", text="我有点焦虑，帮我记住明天复习。"),
                RealtimeEvent("response.text.delta", text="别急，我会帮你记住。"),
                RealtimeEvent("response.audio.delta", audio=b"voice"),
            ]))
            invite = parse_call_invite({"type": "qq_call_invite", "call_id": "c1", "user_id": "u1"})
            await plugin.handle_call_invite(invite)
            await plugin.run_model_turn("c1", [AudioFrame(call_id="c1", pcm=b"pcm")])
            summary = await plugin.finish_call("c1")
            return plugin, bridge, summary

        plugin, bridge, summary = asyncio.run(run())

        self.assertEqual(bridge.outbound_audio[0].pcm, b"voice")
        self.assertIn("复习", summary.summary)
        self.assertNotIn("c1", plugin.sessions)

    def test_bridge_audio_event_streams_to_started_realtime_client(self):
        async def run():
            bridge = InMemoryNapCatCallBridge()
            client = FakeRealtimeVoiceClient([
                RealtimeEvent("input.transcript", text="电话里说帮我记住买药。"),
                RealtimeEvent("response.audio.delta", audio=b"reply"),
            ])
            plugin = QQVoiceCallPlugin(config={"auto_answer": True})
            plugin.set_call_bridge(bridge)
            plugin.set_realtime_client_factory(lambda: client)
            await plugin.handle_bridge_event({"type": "qq_call_invite", "call_id": "c1", "user_id": "u1"})
            result = await plugin.handle_bridge_event({"type": "qq_call_audio", "call_id": "c1", "pcm_base64": "cGNt"})
            summary = await plugin.finish_call("c1")
            return result, client, bridge, summary

        result, client, bridge, summary = asyncio.run(run())

        self.assertTrue(result["ok"])
        self.assertEqual(client.audio_chunks, [b"pcm"])
        self.assertEqual(bridge.outbound_audio[0].pcm, b"reply")
        self.assertIn("买药", summary.summary)


if __name__ == "__main__":
    unittest.main()
