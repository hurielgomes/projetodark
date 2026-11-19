import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "estudio"))

import myhub_llm  # noqa: E402
from myhub_llm import MyHubBridgeError, criar_llm_myhub  # noqa: E402
import diretor_m1  # noqa: E402
from estudio.cenas2d.recursos.biblioteca import Biblioteca  # noqa: E402


class MyHubBridgeAdapterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.bridge = self.root / "myhub-bridge"
        self.bridge.mkdir()
        (self.bridge / "config.json").write_text("{}", encoding="utf-8")
        (self.bridge / "main.py").write_text("# Bridge simulado para teste HTTP", encoding="utf-8")
        self.jobs = []

        def fake_submit(client, job):
            self.jobs.append(dict(job))
            out = self.bridge / "results" / str(job["id"])
            (out / "artifacts").mkdir(parents=True, exist_ok=True)
            (out / "response.txt").write_text("RESPOSTA SIMULADA DO MYHUB", encoding="utf-8")
            artifacts = []
            if job.get("expected_outputs") and "svg" in job["expected_outputs"]:
                svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><rect x="1" y="1" width="98" height="98" fill="#123456"/></svg>'
                file = out / "artifacts" / "teste.svg"
                file.write_text(svg, encoding="utf-8")
                artifacts.append({"filename": "teste.svg", "path": "artifacts/teste.svg", "source": "download", "valid": True})
            (out / "response.json").write_text(json.dumps({"success": True, "artifacts": artifacts}), encoding="utf-8")
            return out

        self._patcher = patch.object(myhub_llm._BridgeClient, "submit", fake_submit)
        self._patcher.start()

    def tearDown(self):
        self._patcher.stop()
        self.tmp.cleanup()

    def test_chama_bridge_e_retorna_texto(self):
        logs = []
        llm = criar_llm_myhub({"myhub_bridge_dir": str(self.bridge)}, self.root, logs.append)
        response = llm("Crie uma direção de arte", True)
        self.assertEqual(response, "RESPOSTA SIMULADA DO MYHUB")
        self.assertEqual(len(self.jobs), 1)
        self.assertEqual(self.jobs[0]["chat_key"], "fabrica_m1__direcao_arte")
        self.assertEqual(self.jobs[0]["expected_outputs"], ["json"])
        self.assertTrue(any("modelo GPT-6 Luna" in line for line in logs))

    def test_separa_chat_de_direcao_e_recursos(self):
        llm = criar_llm_myhub({"myhub_bridge_dir": str(self.bridge)}, self.root, lambda _: None)
        llm("Prompt JSON", True)
        llm("Prompt SVG", False)
        self.assertEqual({x["chat_key"] for x in self.jobs}, {
            "fabrica_m1__direcao_arte", "fabrica_m1__recursos_svg"
        })

    def test_etapas_editoriais_usam_chats_persistentes_separados(self):
        etapas = ["planejamento", "roteiro", "checagem", "otimizacao", "refino"]
        llms = [
            criar_llm_myhub(
                {"myhub_bridge_dir": str(self.bridge)}, self.root, lambda _: None,
                purpose=etapa, expected_outputs=["json"], chat_scope="canal_2026_tema_teste",
            )
            for etapa in etapas
        ]
        for llm in llms:
            self.assertEqual(llm("{}", True), "RESPOSTA SIMULADA DO MYHUB")
        self.assertEqual({x["chat_key"] for x in self.jobs}, {
            "fabrica__roteiro_planejamento__canal_2026_tema_teste", "fabrica__roteiro_criacao__canal_2026_tema_teste",
            "fabrica__roteiro_checagem__canal_2026_tema_teste", "fabrica__roteiro_otimizacao__canal_2026_tema_teste",
            "fabrica__roteiro_refino__canal_2026_tema_teste",
        })
        self.assertTrue(all(x["expected_outputs"] == ["json"] for x in self.jobs))

    def test_escolhe_modelos_configurados_separadamente(self):
        cfg = {"myhub_bridge_dir": str(self.bridge), "myhub_model_texto": "MyHubNitro", "myhub_model_artes": "Claude Haiku 5.5"}
        llm_txt = criar_llm_myhub(cfg, self.root, lambda _: None, purpose="roteiro")
        llm_art = criar_llm_myhub(cfg, self.root, lambda _: None, chat_scope="teste")
        llm_txt("{}", True)
        llm_art("SVG", False)
        self.assertEqual([x["model"] for x in self.jobs], ["MyHubNitro", "Claude Haiku 5.5"])

    def test_request_artifacts_retorna_svg_baixado(self):
        llm = criar_llm_myhub({"myhub_bridge_dir": str(self.bridge), "myhub_model_artes": "Gemini 3.8 Flash"}, self.root, lambda _: None)
        result = llm.request_artifacts("Gere o SVG", chat="lote_teste", outputs=("svg",))
        self.assertEqual(result["artifacts"][0]["extension"], ".svg")
        self.assertTrue(result["artifacts"][0]["source"] == "download")
        self.assertEqual(self.jobs[0]["model"], "Gemini 3.8 Flash")
        self.assertTrue(self.jobs[0]["metadata"]["capture_all_downloads"])

    def test_erro_quando_bridge_nao_existe(self):
        with self.assertRaises(MyHubBridgeError):
            criar_llm_myhub({"myhub_bridge_dir": str(self.root / "nao-existe")}, self.root)

    def test_diretor_m1_usa_o_provedor_myhub(self):
        calls = []
        payload = json.dumps({"cenas": [{"n": 1, "cenario": {"ref": "savana"},
                                          "hero": {"ref": "tigre", "anim": "caminhar"},
                                          "apoio": [], "personagens": [], "chip": "DIA · SAVANA"}]})

        def fake_create(cfg, root, log, **kwargs):
            calls.append((cfg, Path(root), kwargs))
            return lambda prompt, json_mode=True: payload if json_mode else ""

        module = types.SimpleNamespace(criar_llm_myhub=fake_create)
        with tempfile.TemporaryDirectory() as folder:
            bib_path = Path(folder) / "bib"
            import shutil
            shutil.copytree(ROOT / "biblioteca_m1", bib_path)
            bib = Biblioteca(bib_path, bloquear_pendentes=True)
            cv = types.SimpleNamespace(_parse_json=staticmethod(json.loads))
            messages = []
            with patch.dict(sys.modules, {"myhub_llm": module}):
                scenes = diretor_m1.dirigir(
                    {"titulo": "Teste", "cenas": [{"narracao": "O tigre caminha pela savana."}]},
                    [5.0], bib, modo="myhub", cfg={"myhub_bridge_dir": str(self.bridge)},
                    cv=cv, log=messages.append,
                )
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][2].get("chat_scope"), "teste")
        self.assertEqual(scenes[0]["cenario"]["ref"], "savana")
        self.assertTrue(any("direcao de arte: MyHub Bridge" in x for x in messages))


if __name__ == "__main__":
    unittest.main()
