import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "estudio"))

from PIL import Image
from estudio.cenas2d.rig import Posicionado  # noqa: E402


class BloomReductionTests(unittest.TestCase):
    def test_glow_svg_usa_alpha_reduzido(self):
        pos = Posicionado.__new__(Posicionado)
        pos.s = 1.0
        form = {"t": "glow", "a": 1.0, "op": 1.0, "cor": (255, 180, 80, 255), "exp": 1.8}
        with patch("estudio.cenas2d.rig.pt.brilho_sprite") as sprite, patch.object(Posicionado, "_cola"):
            sprite.return_value = Image.new("RGBA", (4, 4), (255, 255, 255, 10))
            pos._desenha_forma(Image.new("RGBA", (40, 40)), 0, 0, 1, "parte", form, [(20, 20, 10, 10)], 1.0, {})
        self.assertAlmostEqual(sprite.call_args.args[2], 0.58, places=4)

    def test_luz_por_parte_usa_intensidade_reduzida(self):
        pos = Posicionado.__new__(Posicionado)
        pos.rig = types.SimpleNamespace(rec={"luzes_por_parte": [
            {"parte": "corpo", "int": 1.0, "dx": 0, "dy": 0, "raio": 20, "cor": (255, 255, 255), "exp": 1.8}
        ]})
        pos.op = {"corpo": 1.0}
        pos.s = 1.0
        pos.A = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
        with patch.object(Posicionado, "centro_parte", return_value=(20, 20)):
            result = pos.luzes()
        self.assertAlmostEqual(result[0][4], 0.72, places=4)


if __name__ == "__main__":
    unittest.main()
