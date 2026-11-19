import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "estudio"))

import diretor_m1


class KitCompatibilidadeTests(unittest.TestCase):
    def test_ausencia_de_garantir_kit_nao_interrompe_m1(self):
        mensagens = []
        recursos_ia_antigo = types.SimpleNamespace(
            __file__=r"C:\ProjetoDark2\recursos_ia.py",
            criar_recurso=lambda *args, **kwargs: "ok",
        )
        with patch.object(diretor_m1, "R", recursos_ia_antigo):
            resultado = diretor_m1._garantir_kit_compativel(object(), mensagens.append)
        self.assertEqual(resultado, [])
        self.assertTrue(any("sem garantir_kit" in msg for msg in mensagens))
        self.assertTrue(any("recursos_ia.py" in msg for msg in mensagens))

    def test_falha_no_kit_e_registrada_sem_ser_propaga(self):
        mensagens = []
        recursos_ia_com_falha = types.SimpleNamespace(
            __file__="recursos_ia_teste.py",
            garantir_kit=lambda bib, log: (_ for _ in ()).throw(RuntimeError("falha simulada")),
        )
        with patch.object(diretor_m1, "R", recursos_ia_com_falha):
            resultado = diretor_m1._garantir_kit_compativel(object(), mensagens.append)
        self.assertEqual(resultado, [])
        self.assertTrue(any("falha simulada" in msg for msg in mensagens))

    def test_usa_garantir_kit_quando_disponivel(self):
        chamadas = []
        bib = object()
        recursos_ia_nova = types.SimpleNamespace(
            garantir_kit=lambda recebido, log: chamadas.append((recebido, log)) or ["termometro"]
        )
        with patch.object(diretor_m1, "R", recursos_ia_nova):
            resultado = diretor_m1._garantir_kit_compativel(bib, lambda _: None)
        self.assertEqual(resultado, ["termometro"])
        self.assertIs(chamadas[0][0], bib)


if __name__ == "__main__":
    unittest.main()
