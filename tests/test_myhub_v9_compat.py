import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "estudio"))

import recursos_ia as R  # noqa: E402
from estudio.cenas2d.rig import Rig  # noqa: E402


class FakeBib:
    def __init__(self):
        self.idx = {"recursos": {}}


class BatchCompatibilityTests(unittest.TestCase):
    def test_rig_accepts_optional_origin_metadata(self):
        rec = {"id": "teste", "partes": [], "camadas": [], "animacoes": {}}
        rig = Rig(rec, origem="ia")
        self.assertEqual(rig.origem, "ia")

    def test_converted_resource_does_not_mix_origin_into_geometry_payload(self):
        svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><g id="forma"><rect x="10" y="10" width="80" height="80" fill="#ffffff"/></g></svg>'
        rec, _ = R._recurso_de_svg(svg, {"id": "teste", "tipo": "objeto", "origem": "ia"})
        self.assertNotIn("origem", rec)

    def test_empty_batch_does_not_trigger_two_extra_single_requests(self):
        specs = [
            {"id": "objeto_a", "tipo": "objeto", "nome": "Objeto A", "descricao": "A", "tags": []},
            {"id": "objeto_b", "tipo": "objeto", "nome": "Objeto B", "descricao": "B", "tags": []},
        ]
        calls = []

        def request_artifacts(prompt, *, chat, outputs, capture_all_downloads, model=None):
            calls.append((chat, tuple(outputs)))
            return {"artifacts": [], "text": "Anexos não disponíveis."}

        def llm(*args, **kwargs):
            raise AssertionError("Não deve haver retry individual quando o lote inteiro veio sem artefatos")

        llm.request_artifacts = request_artifacts
        llm.batch_scope = "teste"
        bib = FakeBib()
        with patch.object(R, "_procedural", side_effect=lambda spec: {"id": spec["id"], "tipo": spec["tipo"]}), \
             patch.object(R, "_registrar_recurso_gerado", side_effect=lambda spec, rec, bib, origem="ia", log=print: spec["id"]), \
             patch.object(R, "_gerar_por_ia", side_effect=AssertionError("retry individual inesperado")):
            result = R.criar_recursos_lote(specs, bib, llm, log=lambda _msg: None, tamanho_lote=2)
        self.assertEqual(result, {"objeto_a": "objeto_a", "objeto_b": "objeto_b"})
        self.assertEqual(len(calls), 1)

    def test_partial_batch_retries_only_missing_item(self):
        specs = [
            {"id": "objeto_a", "tipo": "objeto", "nome": "Objeto A", "descricao": "A", "tags": []},
            {"id": "objeto_b", "tipo": "objeto", "nome": "Objeto B", "descricao": "B", "tags": []},
        ]
        individual = []
        def request_artifacts(prompt, *, chat, outputs, capture_all_downloads, model=None):
            return {"artifacts": [{"filename": "objeto_a.svg", "extension": ".svg", "valid": True, "source": "download", "content": "svg_a"}], "text": ""}
        def llm(prompt, json_mode=False):
            individual.append(prompt)
            return "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 10 10\"></svg>"
        llm.request_artifacts = request_artifacts
        llm.batch_scope = "teste"
        bib = FakeBib()
        with patch.object(R, "_svg_validar_para_spec", side_effect=lambda svg, spec: {"id": spec["id"]}), \
             patch.object(R, "_gerar_por_ia", side_effect=lambda spec, llm, log, tentativas=1: (individual.append(spec["id"]) or {"id": spec["id"]})), \
             patch.object(R, "_registrar_recurso_gerado", side_effect=lambda spec, rec, bib, origem="ia", log=print: spec["id"]):
            result = R.criar_recursos_lote(specs, bib, llm, log=lambda _msg: None, tamanho_lote=2)
        self.assertEqual(set(result), {"objeto_a", "objeto_b"})
        self.assertEqual(individual, ["objeto_b"])


if __name__ == "__main__":
    unittest.main()
