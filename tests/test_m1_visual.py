"""Testes do acabamento visual do M1 (polimento.py, descaixar, layout do diretor, legenda TikTok)."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "estudio"))

from PIL import Image  # noqa: E402

import diretor_m1  # noqa: E402
from estudio.cenas2d import polimento as pol  # noqa: E402
from estudio.cenas2d.rig import Rig, descaixar  # noqa: E402
from estudio.cenas2d.recursos.validar import validar_recurso  # noqa: E402


class ContadorTests(unittest.TestCase):
    def test_formatos_pt_br(self):
        self.assertEqual(pol.texto_contagem("8,5 MILHÕES", 0.4), "3,4 MILHÕES")
        self.assertEqual(pol.texto_contagem("7.300 KM", 0.5), "3.650 KM")
        self.assertEqual(pol.texto_contagem("360 MIL", 0.0), "0 MIL")
        self.assertEqual(pol.texto_contagem("360 MIL", 1.0), "360 MIL")
        self.assertEqual(pol.texto_contagem("SEM NUMERO", 0.3), "SEM NUMERO")


class ExposicaoTests(unittest.TestCase):
    def test_cena_escura_e_levantada_e_clara_fica_igual(self):
        escura = Image.new("RGB", (100, 180), (6, 8, 18))
        clara = Image.new("RGB", (100, 180), (160, 170, 190))
        g = pol.gamma_para(escura)
        self.assertLess(g, 0.9)
        self.assertGreater(sum(pol.exposicao(escura, g).convert("L").getdata()), sum(escura.convert("L").getdata()))
        self.assertEqual(pol.gamma_para(clara), 1.0)


def _obj_com_fundo(cor_fundo):
    return {"formato": "m1-recurso/1", "id": "t", "tipo": "objeto", "nome": "t", "caixa": [0, 0, 400, 300], "base": [200, 300],
            "partes": [{"id": "base", "pivo": [0, 0], "formas": [
                {"t": "rect", "x": 0, "y": 0, "w": 400, "h": 300, "fill": cor_fundo},
                {"t": "rect", "x": 150, "y": 100, "w": 100, "h": 150, "fill": "#ffffff"}]}]}


class DescaixarTests(unittest.TestCase):
    def test_remove_retangulo_de_fundo_e_encolhe_caixa_so_em_objeto_ia(self):
        rec, _ = validar_recurso(_obj_com_fundo("#050a14"))
        novo = descaixar(rec, "ia")
        self.assertEqual(len(novo["partes"][0]["formas"]), 1)
        self.assertLess(novo["caixa"][2] - novo["caixa"][0], 200)
        self.assertEqual(len(rec["partes"][0]["formas"]), 2)           # original intacto
        self.assertEqual(len(descaixar(rec, "curado")["partes"][0]["formas"]), 2)    # curado nao e mexido
        Rig(rec, origem="ia")                                           # compila sem erro

    def test_fundo_claro_tambem_sai(self):
        rec, _ = validar_recurso(_obj_com_fundo("#1fb7ff"))
        self.assertEqual(len(descaixar(rec, "ia")["partes"][0]["formas"]), 1)


class LayoutTests(unittest.TestCase):
    def _plano(self):
        cat = [{"id": "mapa", "tipo": "objeto", "animacoes": ["parado"]}]
        plano = {"cenario": None, "personagens": [], "objetos": ["mapa"], "hero": "mapa", "clima": "alerta", "acento": "#ff5a4a",
                 "rotulos": [{"texto": "7.300 KM", "sub": "de costa"}], "chip": "DIA 1 · COSTA"}
        return cat, plano

    def test_heroi_marcado_titulo_na_cena_1_e_contador_depois(self):
        cat, plano = self._plano()
        c0 = diretor_m1.plano_para_cena(plano, cat, "Fala de teste aqui.", 6.0, 0, "", titulo="Titulo do video")
        c1 = diretor_m1.plano_para_cena(plano, cat, "Fala de teste aqui.", 4.0, 1, "")
        self.assertTrue(c0["elementos"][0]["hero"])
        self.assertEqual((c0["clima"], c0["acento"]), ("alerta", "#ff5a4a"))
        self.assertIn("titulo", c0["hud"])
        self.assertGreater(c0["hud"]["contadores"][0]["t"], c0["hud"]["titulo"]["fim"])     # o contador espera o titulo sair
        self.assertLess(c1["hud"]["contadores"][0]["t"], 1.0)
        self.assertNotIn("titulo", c1["hud"])
        self.assertNotEqual(c0["camera"]["zoom"][0]["v"], c1["camera"]["zoom"][0]["v"])      # camera alterna entre cenas
        self.assertIn("pan", c0["camera"])

    def test_cena_1_curta_fica_so_com_o_titulo(self):
        cat, plano = self._plano()
        c0 = diretor_m1.plano_para_cena(plano, cat, "Fala.", 3.0, 0, "", titulo="Titulo do video")
        self.assertIn("titulo", c0["hud"])
        self.assertNotIn("contadores", c0["hud"])

    def test_numero_com_acento_no_rotulo(self):
        self.assertEqual(diretor_m1._rotulos("cruzar 8,5 milhões de quilômetros")[0]["texto"], "8,5 MILHÕES")


class LegendaTests(unittest.TestCase):
    def test_estilo_tiktok_desenha(self):
        from estudio.comum import legendas
        f = Image.new("RGBA", (540, 960), (10, 10, 30, 255))
        legendas.desenhar(f, 0.5, [{"ini": 0.0, "fim": 2.0, "texto": "O QUE ACONTECERIA"}], 540, 960, "9x16", [], estilo="tiktok", cor_ativa=(53, 214, 255))
        self.assertGreater(len(set(f.getdata())), 50)


if __name__ == "__main__":
    unittest.main()
