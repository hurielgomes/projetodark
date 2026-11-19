import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from myhub_llm import _asset_chat_key


class AssetChatScopeTests(unittest.TestCase):
    def test_each_svg_asset_gets_its_own_chat(self):
        scope = "exemplo_2026-11-19_video_teste"
        a = _asset_chat_key(scope, "Escreva SVG.\nDESENHE: Quintal residencial com gramado.")
        b = _asset_chat_key(scope, "Escreva SVG.\nDESENHE: Pepita de ouro.")
        self.assertNotEqual(a, b)
        self.assertIn("quintal_residencial", a)
        self.assertIn("pepita_de_ouro", b)

    def test_same_asset_reuses_the_same_chat(self):
        prompt = "DESENHE: Proprietário surpreso diante da descoberta.\nFORMATO: SVG"
        self.assertEqual(_asset_chat_key("projeto", prompt), _asset_chat_key("projeto", prompt))

    def test_chat_key_respects_bridge_limit(self):
        key = _asset_chat_key("x" * 200, "DESENHE: " + "objeto muito detalhado " * 20)
        self.assertLessEqual(len(key), 100)

    def test_prompt_without_draw_line_returns_none(self):
        self.assertIsNone(_asset_chat_key("projeto", "Escreva somente SVG."))


if __name__ == "__main__":
    unittest.main()
