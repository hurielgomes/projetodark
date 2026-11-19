import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "estudio"))

import recursos_ia as R  # noqa: E402


class FakeBib:
    def __init__(self):
        self.idx = {"recursos": {}}


class LotesSvgTests(unittest.TestCase):
    def test_lote_pede_arquivos_svg_independentes_e_com_ids(self):
        prompt = R._prompt_svg_lote([
            {"id": "casa", "tipo": "objeto", "nome": "Casa", "descricao": "Casa suburbana", "tags": []},
            {"id": "ceu", "tipo": "cenario", "nome": "Céu", "descricao": "Céu ao entardecer", "clima": "entardecer", "tags": []},
        ])
        self.assertIn("casa.svg", prompt)
        self.assertIn("ceu.svg", prompt)
        self.assertIn("ARQUIVOS SVG ANEXOS", prompt)
        self.assertIn("SEPARADO", prompt)

    def test_associacao_prioriza_download_e_associa_por_nome(self):
        specs = [{"id": "casa", "tipo": "objeto"}, {"id": "ceu", "tipo": "cenario"}]
        artifacts = [
            {"filename": "artefato_01.svg", "extension": ".svg", "valid": True, "source": "code_block", "content": "inline"},
            {"filename": "ceu.svg", "extension": ".svg", "valid": True, "source": "download", "content": "SVG_CEU"},
            {"filename": "casa.svg", "extension": ".svg", "valid": True, "source": "download", "content": "SVG_CASA"},
        ]
        mapped = R._associar_svgs_lote(specs, artifacts)
        self.assertEqual(mapped["ceu"], "SVG_CEU")
        self.assertEqual(mapped["casa"], "SVG_CASA")

    def test_quatorze_recursos_geram_lotes_de_dois_sem_abrir_um_chat_por_svg(self):
        specs = [
            {"id": f"objeto_{i}", "tipo": "objeto", "nome": f"Objeto {i}", "descricao": f"Descrição detalhada {i}", "tags": []}
            for i in range(14)
        ]
        chamadas = []
        def request_artifacts(prompt, *, chat, outputs, capture_all_downloads, model=None):
            ids = []
            for line in prompt.splitlines():
                if line.startswith("ARQUIVO ") and line.endswith(".svg"):
                    ids.append(line.split(":", 1)[1].strip()[:-4])
            chamadas.append((chat, ids, tuple(outputs), capture_all_downloads))
            artifacts = [
                {"filename": f"{rid}.svg", "extension": ".svg", "valid": True, "source": "download", "content": f"<svg>{rid}</svg>"}
                for rid in ids
            ]
            return {"artifacts": artifacts, "text": ""}
        def fake_llm(prompt, json_mode=False):
            raise AssertionError("Objetos/cenários agrupáveis não deveriam gerar chamada individual quando o lote deu certo")
        fake_llm.request_artifacts = request_artifacts
        fake_llm.batch_scope = "video_teste"
        bib = FakeBib()
        with patch.object(R, "_svg_validar_para_spec", side_effect=lambda svg, spec: {"id": spec["id"]}), \
             patch.object(R, "_registrar_recurso_gerado", side_effect=lambda spec, rec, bib, origem="ia", log=print: spec["id"]):
            result = R.criar_recursos_lote(specs, bib, fake_llm, log=lambda _: None, tamanho_lote=2)
        self.assertEqual(len(result), 14)
        self.assertEqual(len(chamadas), 7)
        self.assertTrue(all(len(item[1]) == 2 for item in chamadas))
        self.assertTrue(all(item[2] == ("svg",) and item[3] for item in chamadas))
        self.assertTrue(all("video_teste" in item[0] for item in chamadas))


if __name__ == "__main__":
    unittest.main()
