import asyncio
import unittest

from doubao_realtime_client import DoubaoRealtimeConfig, FakeRealtimeVoiceClient, RealtimeEvent


class DoubaoRealtimeClientTests(unittest.TestCase):
    def test_config_builds_auth_headers(self):
        config = DoubaoRealtimeConfig(
            url="wss://example.test/realtime",
            app_id="app",
            access_token="token",
            model="doubao-realtime-voice",
        )

        self.assertEqual(config.headers()["X-Api-App-Id"], "app")
        self.assertEqual(config.headers()["Authorization"], "Bearer token")
        self.assertEqual(config.headers()["X-Api-Access-Key"], "token")
        self.assertEqual(config.headers()["X-Api-Resource-Id"], "volc.speech.dialog")

    def test_fake_client_streams_events(self):
        async def run():
            client = FakeRealtimeVoiceClient([
                RealtimeEvent("input.transcript", text="你好"),
                RealtimeEvent("response.audio.delta", audio=b"out"),
            ])
            await client.start()
            await client.send_audio(b"in")
            await client.finish_audio()
            events = []
            async for event in client.events():
                events.append(event)
            await client.close()
            return client, events

        client, events = asyncio.run(run())

        self.assertTrue(client.started)
        self.assertTrue(client.finished)
        self.assertTrue(client.closed)
        self.assertEqual(client.audio_chunks, [b"in"])
        self.assertEqual(events[0].text, "你好")
        self.assertEqual(events[1].audio, b"out")


if __name__ == "__main__":
    unittest.main()
