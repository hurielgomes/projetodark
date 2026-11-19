import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "motores"))
sys.path.insert(0, str(ROOT / "motores" / "adapters"))

from character_2_5d import Character25DEngine  # noqa: E402


class Character25DMyHubRoutingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "config.json").write_text(json.dumps({"m1_diretor_padrao": "myhub"}), encoding="utf-8")
        self.engine = Character25DEngine()
        self.job = {"canal": "teste", "tema": "Tema", "formatos": "9x16", "motor": "character_2_5d"}

    def tearDown(self):
        self.tmp.cleanup()

    def test_usa_myhub_salvo_na_configuracao(self):
        cmd = self.engine.build_command(self.job, self.root, "python")
        pos = cmd.index("--diretor")
        self.assertEqual(cmd[pos + 1], "myhub")

    def test_opcao_explicita_do_job_prevalece(self):
        cmd = self.engine.build_command({**self.job, "diretor": "gemini"}, self.root, "python")
        pos = cmd.index("--diretor")
        self.assertEqual(cmd[pos + 1], "gemini")

    def test_aceita_myhub_como_provedor_explicito(self):
        cmd = self.engine.build_command({**self.job, "diretor": "myhub"}, self.root, "python")
        pos = cmd.index("--diretor")
        self.assertEqual(cmd[pos + 1], "myhub")

    def test_config_invalida_recorre_para_myhub_como_padrao_seguro(self):
        (self.root / "config.json").write_text("{ json quebrado", encoding="utf-8")
        cmd = self.engine.build_command(self.job, self.root, "python")
        pos = cmd.index("--diretor")
        self.assertEqual(cmd[pos + 1], "myhub")


if __name__ == "__main__":
    unittest.main()
