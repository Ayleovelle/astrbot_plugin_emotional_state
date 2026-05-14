import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class MetadataAndConfigTests(unittest.TestCase):
    def test_metadata_identity(self):
        text = (ROOT / "metadata.yaml").read_text(encoding="utf-8")
        self.assertIn("name: astrbot_plugin_qq_voice_call", text)
        self.assertIn("QQ 语音电话助手", text)
        self.assertIn("https://github.com/Ayleovelle/astrbot_plugin_qq_voice_call", text)

    def test_config_contains_call_and_doubao_keys(self):
        schema = json.loads((ROOT / "_conf_schema.json").read_text(encoding="utf-8"))
        for key in (
            "auto_answer",
            "napcat_call_bridge_url",
            "doubao_realtime_url",
            "doubao_app_id",
            "doubao_access_token",
            "write_sylanne_memory",
            "observe_sylanne_emotion",
        ):
            self.assertIn(key, schema)
        self.assertFalse(schema["auto_answer"]["default"])


if __name__ == "__main__":
    unittest.main()
